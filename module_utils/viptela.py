from __future__ import absolute_import, division, print_function
__metaclass__ = type
import json
import requests
import re
import time
from ansible.module_utils.basic import AnsibleModule, json, env_fallback


try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

def viptela_argument_spec():
    return dict(host=dict(type='str', required=True, fallback=(env_fallback, ['viptela_HOST'])),
            user=dict(type='str', required=True, fallback=(env_fallback, ['viptela_USER'])),
            password=dict(type='str', required=True, fallback=(env_fallback, ['viptela_PASSWORD'])),
            validate_certs=dict(type='bool', required=False, default=False),
            timeout=dict(type='int', default=30)
    )

STANDARD_HTTP_TIMEOUT = 10
STANDARD_JSON_HEADER = {'Connection': 'keep-alive', 'Content-Type': 'application/json'}
POLICY_LIST_DICT = {
    'siteLists': 'site',
    'vpnLists': 'vpn',
}

class viptelaModule(object):

    def __init__(self, module, function=None):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = dict()
        self.function = function
        self.cookies = None
        self.json = None

        self.method = None
        self.path = None
        self.response = None
        self.status = None
        self.url = None
        self.params['force_basic_auth'] = True
        self.user = self.params['user']
        self.password = self.params['password']
        self.host = self.params['host']
        self.timeout = self.params['timeout']
        self.modifiable_methods = ['POST', 'PUT', 'DELETE']

        self.session = requests.Session()
        self.session.verify = self.params['validate_certs']

        self.POLICY_DEFINITION_TYPES = ['cflowd', 'dnssecurity', 'control', 'hubandspoke', 'acl', 'vpnmembershipgroup',
                                        'mesh', 'rewriterule', 'data', 'rewriterule', 'aclv6']
        self.POLICY_LIST_TYPES = ['community', 'localdomain', 'ipv6prefix', 'dataipv6prefix', 'tloc', 'aspath', 'zone',
                                  'color', 'sla', 'app', 'mirror', 'dataprefix', 'extcommunity', 'site', 'ipprefixall',
                                  'prefix', 'umbrelladata', 'class', 'ipssignature', 'dataprefixall',
                                  'urlblacklist', 'policer', 'urlwhitelist', 'vpn']

        self.login()

    # Deleting (Calling destructor)
    def __del__(self):
        self.logout()

    def _fallback(self, value, fallback):
        if value is None:
            return fallback
        return value

    def list_to_dict(self, list, key_name, remove_key=True):
        dict = {}
        for item in list:
            if key_name in item:
                if remove_key:
                    key = item.pop(key_name)
                else:
                    key = item[key_name]

                dict[key] = item
            # else:
            #     self.fail_json(msg="key {0} not found in dictionary".format(key_name))

        return dict

    @staticmethod
    def compare_payloads(new_payload, old_payload, compare_values=[]):
        payload_key_diff = []
        for key, value in new_payload.items():
            if key in compare_values:
                if key not in old_payload:
                    payload_key_diff.append(key)
                elif new_payload[key] != old_payload[key]:
                    payload_key_diff.append(key)
        return payload_key_diff


    def login(self):
        try:
            response = self.session.post(
                url='https://{0}/j_security_check'.format(self.host),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={'j_username': self.user, 'j_password': self.password},
                timeout=self.timeout
            )
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            self.module.fail_json(msg=e)

        if response.text.startswith('<html>'):
            self.fail_json(msg='Could not login to device, check user credentials.', **self.result)
        else:
            return response

    def logout(self):
        self.request('/logout')

    def request(self, url_path, method='GET', headers=STANDARD_JSON_HEADER, data=None, files=None, payload=None):
        """Generic HTTP method for viptela requests."""

        self.method = method
        self.headers = headers
        self.url = 'https://{0}{1}'.format(self.host, url_path)

        if payload:
            self.result['payload'] = payload
            data = json.dumps(payload)
            self.result['data'] = data

        response = self.session.request(method, self.url, headers=headers, files=files, data=data)

        self.status_code = response.status_code
        self.status = requests.status_codes._codes[response.status_code][0]

        if self.status_code >= 300 or self.status_code < 0:
            try:
                decoded_response = response.json()
                details = decoded_response['error']['details']
                error = decoded_response['error']['message']
                self.fail_json(msg='{0}: {1}'.format(error, details))
            except JSONDecodeError as e:
                self.fail_json(msg=self.status)

        try:
            response.json = response.json()
        except JSONDecodeError as e:
            response.json = {}

        return response

    def get_template_attachments(self, template_id):
        response = self.request('/dataservice/template/device/config/attached/{0}'.format(template_id))

        attached_devices = []
        if response.json:
            device_list = response.json['data']
            for device in device_list:
                attached_devices.append(device['host-name'])

        return attached_devices

    def generalTemplates_to_id(self, generalTemplates):
        converted_generalTemplates = []
        feature_templates = self.get_feature_template_dict(factory_default=True)
        for template in generalTemplates:
            if 'templateName' not in template:
                self.result['generalTemplates'] = generalTemplates
                self.fail_json(msg="Bad template")
            if template['templateName'] in feature_templates:
                template_item = {
                    'templateId': feature_templates[template['templateName']]['templateId'],
                    'templateType': template['templateType']}
                if 'subTemplates' in template:
                    subTemplates = []
                    for sub_template in template['subTemplates']:
                        if sub_template['templateName'] in feature_templates:
                            subTemplates.append(
                                {'templateId': feature_templates[sub_template['templateName']]['templateId'],
                                 'templateType': sub_template['templateType']})
                        else:
                            self.fail_json(msg="There is no existing feature template named {0}".format(
                                sub_template['templateName']))
                    template_item['subTemplates'] = subTemplates

                converted_generalTemplates.append(template_item)
            else:
                self.fail_json(msg="There is no existing feature template named {0}".format(template['templateName']))

        return converted_generalTemplates

    def convert_sequences_to_id(self, sequence_list):
        for sequence in sequence_list:
            for entry in sequence['match']['entries']:
                policy_list_dict = self.get_policy_list_dict(entry['listType'])
                if entry['listName'] in policy_list_dict:
                    entry['ref'] = policy_list_dict[entry['listName']]['listId']
                    entry.pop('listName')
                    entry.pop('listType')
                else:
                    self.fail_json(msg="Could not find list {0} of type {1}".format(entry['listName'], entry['listType']))
        return sequence_list

    def get_device_template_list(self, factory_default=False):
        response = self.request('/dataservice/template/device')

        return_list = []
        if response.json:

            device_body = response.json
            feature_template_dict = self.get_feature_template_dict(factory_default=True, key_name='templateId')

            for device in device_body['data']:
                object_response = self.request('/dataservice/template/device/object/{0}'.format(device['templateId']))
                if object_response.json:
                    object = object_response.json
                    if not factory_default and object['factoryDefault']:
                        continue

                    if 'generalTemplates' in object:
                        generalTemplates = []
                        for old_template in object.pop('generalTemplates'):
                            new_template = {
                                'templateName': feature_template_dict[old_template['templateId']]['templateName'],
                                'templateType': old_template['templateType']}
                            if 'subTemplates' in old_template:
                                subTemplates = []
                                for sub_template in old_template['subTemplates']:
                                    subTemplates.append({'templateName':feature_template_dict[sub_template['templateId']]['templateName'], 'templateType':sub_template['templateType']})
                                new_template['subTemplates'] = subTemplates

                            generalTemplates.append(new_template)
                        object['generalTemplates'] = generalTemplates

                    object['templateId'] = device['templateId']
                    object['attached_devices'] = self.get_template_attachments(device['templateId'])
                    object['input'] = self.get_template_input(device['templateId'])

                    return_list.append(object)

        return return_list

    def get_device_template_dict(self, factory_default=False, key_name='templateName', remove_key=True):
        device_template_list = self.get_device_template_list(factory_default=factory_default)

        return self.list_to_dict(device_template_list, key_name, remove_key)

    def get_feature_template_list(self, factory_default=False):
        response = self.request('/dataservice/template/feature')

        return_list = []
        if response.json:
            template_list = response.json['data']
            for template in template_list:
                if not factory_default and template['factoryDefault']:
                    continue
                template['templateDefinition'] = json.loads(template['templateDefinition'])
                template.pop('editedTemplateDefinition', None)
                return_list.append(template)

        return return_list

    def get_feature_template_dict(self, factory_default=False, key_name='templateName', remove_key=True):
        feature_template_list = self.get_feature_template_list(factory_default=factory_default)

        return self.list_to_dict(feature_template_list, key_name, remove_key)

    def get_policy_list(self, type, list_id):
        response = self.request('/dataservice/template/policy/list/{0}/{1}'.format(type.lower(), list_id))
        return response.json

    def get_policy_list_list(self, type):
        if type == 'all':
            response = self.request('/dataservice/template/policy/list')
        else:
            response = self.request('/dataservice/template/policy/list/{0}'.format(type.lower()))

        return response.json['data']

    def get_policy_list_dict(self, type, key_name='name', remove_key=False):

        policy_list = self.get_policy_list_list(type)

        return self.list_to_dict(policy_list, key_name, remove_key=remove_key)

    def get_policy_definition(self, type, definition_id):
        response = self.request('/dataservice/template/policy/definition/{0}/{1}'.format(type, definition_id))
        return response.json

    def get_policy_definition_list(self, type):
        response = self.request('/dataservice/template/policy/definition/{0}'.format(type))

        return response.json['data']

    def get_policy_definition_dict(self, type, key_name='name', remove_key=False):

        policy_definition_list = self.get_policy_definition_list(type)

        return self.list_to_dict(policy_definition_list, key_name, remove_key=remove_key)

    def get_central_policy_list(self):
        response = self.request('/dataservice/template/policy/vsmart')
        if response.json:
            central_policy_list = response.json['data']
            for policy in central_policy_list:
                policy['policyDefinition'] = json.loads(policy['policyDefinition'])
                for item in policy['policyDefinition']['assembly']:
                    policy_definition = self.get_policy_definition(item['type'], item['definitionId'])
                    item['definitionName'] = policy_definition['name']
                    for entry in item['entries']:
                        for key, list in entry.items():
                            if key in POLICY_LIST_DICT:
                                for index, list_id in enumerate(list):
                                    policy_list = self.get_policy_list(POLICY_LIST_DICT[key], list_id)
                                    list[index] = policy_list['name']
            #     if 'policyDefinition' in policy:
            #         for old_template in policy.pop('policyDefinition'):
            #

            return central_policy_list
        else:
            return []

    def get_central_policy_dict(self, key_name='policyName', remove_key=False):

        central_policy_list = self.get_central_policy_list()

        return self.list_to_dict(central_policy_list, key_name, remove_key=remove_key)



    def get_device_list(self, type, key_name='host-name', remove_key=True):
        response = self.request('/dataservice/system/device/{0}'.format(type))

        if response.json:
            return response.json['data']
        else:
            return []

    def get_device_dict(self, type, key_name='host-name', remove_key=False):

        device_list = self.get_device_list(type)

        return self.list_to_dict(device_list, key_name=key_name, remove_key=remove_key)

    def get_device_vedges(self, key_name='host-name', remove_key=True):
        response = self.request('/dataservice/system/device/vedges')

        if response.json:
            return self.list_to_dict(response.json['data'], key_name=key_name, remove_key=remove_key)
        else:
            return {}


    def get_device_controllers(self, key_name='host-name', remove_key=True):
        response = self.request('/dataservice/system/device/controllers')

        if response.json:
            return self.list_to_dict(response.json['data'], key_name=key_name, remove_key=remove_key)
        else:
            return {}

    def get_template_input(self, template_id):
        payload = {
            "deviceIds": [],
            "isEdited": False,
            "isMasterEdited": False,
            "templateId": template_id
        }
        return_dict = {
            "columns": [],
        }
        response = self.request('/dataservice/template/device/config/input', method='POST', payload=payload)

        if response.json:
            if 'header' in response.json and 'columns' in response.json['header']:
                column_list = response.json['header']['columns']

                regex = re.compile(r'\((?P<variable>[^(]+)\)')

                for column in column_list:
                    if column['editable']:
                        match = regex.search(column['title'])
                        if match:
                            variable = match.groups('variable')[0]
                        else:
                            variable = None

                        entry = {'title': column['title'],
                                 'property': column['property'],
                                 'variable': variable}
                        return_dict['columns'].append(entry)

        return return_dict

    def get_template_variables(self, template_id):
        payload = {
            "deviceIds": [],
            "isEdited": False,
            "isMasterEdited": False,
            "templateId": template_id
        }
        return_dict = {}
        response = self.request('/dataservice/template/device/config/input', method='POST', payload=payload)

        if response.json:
            if 'header' in response.json and 'columns' in response.json['header']:
                column_list = response.json['header']['columns']

                regex = re.compile(r'\((?P<variable>[^(]+)\)')

                for column in column_list:
                    if column['editable']:
                        match = regex.search(column['title'])
                        if match:
                            variable = match.groups('variable')[0]
                            return_dict[variable] = column['property']

        return return_dict

    def waitfor_action_completion(self, action_id):
        status = 'in_progress'
        response = {}
        while status == "in_progress":
            response = self.request('/dataservice/device/action/status/{0}'.format(action_id))
            if response.json:
                status = response.json['summary']['status']
                if response.json['data']:
                    action_status = response.json['data'][0]['statusId']
                    action_activity = response.json['data'][0]['activity']
                    action_config = response.json['data'][0]['actionConfig']
            else:
                self.fail_json(msg="Unable to get action status")
            time.sleep(5)

        self.result['action_id'] = action_id
        self.result['action_status'] = action_status
        self.result['action_activity'] = action_activity
        self.result['action_config'] = action_config
        if self.result['action_status'] == 'failure':
            self.fail_json(msg="Action failed")
        return response

    def exit_json(self, **kwargs):
        """Custom written method to exit from module."""
        self.result['status'] = self.status
        self.result['status_code'] = self.status_code
        self.result['url'] = self.url
        self.result['method'] = self.method

        self.result.update(**kwargs)
        self.module.exit_json(**self.result)

    def fail_json(self, msg, **kwargs):
        """Custom written method to return info on failure."""
        self.result['status'] = self.status
        self.result['status_code'] = self.status_code
        self.result['url'] = self.url
        self.result['method'] = self.method

        self.result.update(**kwargs)
        self.module.fail_json(msg=msg, **self.result)