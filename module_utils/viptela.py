from __future__ import absolute_import, division, print_function
__metaclass__ = type
import json
import requests
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native, to_bytes, to_text

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

class viptelaModule(object):

    def __init__(self, module, function=None):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = dict()
        self.function = function
        self.cookies = None
        self.json = None

        # normal output
        self.existing = None

        # info output
        self.config = dict()
        self.original = None
        self.proposed = dict()
        self.merged = None

        # debug output
        self.filter_string = ''
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

        self.login()

    def _fallback(self, value, fallback):
        if value is None:
            return fallback
        return value

    @staticmethod
    def list_to_dict(list, key_name, remove_key=True):
        dict = {}
        for item in list:
            if remove_key:
                key = item.pop(key_name)
            else:
                key = item[key_name]

            dict[key] = item

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

    def request(self, url_path, method='GET', headers=STANDARD_JSON_HEADER, data=None, files=None):
        """Generic HTTP method for viptela requests."""

        self.method = method
        self.headers = headers
        self.url = 'https://{0}{1}'.format(self.host, url_path)

        response = self.session.request(method, self.url, headers=headers, files=files, data=data)

        self.status_code = response.status_code
        self.status = requests.status_codes._codes[response.status_code][0]

        # Timeout the session so that we can unlock whatever we did
        if method in ['PUT', 'POST']:
            self.session.request('GET', 'https://{0}/dataservice/settings/clientSessionTimeout'.format(self.host))

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
                            if 'subTemplates' in old_template:
                                subTemplates = []
                                for sub_template in old_template['subTemplates']:
                                    subTemplates.append({'templateName':feature_template_dict[sub_template['templateId']]['templateName'], 'templateType':sub_template['templateType']})
                                new_template = {'templateName': feature_template_dict[old_template['templateId']]['templateName'],
                                                 'templateType': old_template['templateType'],
                                                 'subTemplates': subTemplates}
                            else:
                                new_template = {'templateName': feature_template_dict[old_template['templateId']]['templateName'],
                                                 'templateType': old_template['templateType']}
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
                template['editedTemplateDefinition'] = json.loads(template['editedTemplateDefinition'])
                return_list.append(template)

        return return_list

    def get_feature_template_dict(self, factory_default=False, key_name='templateName', remove_key=True):
        feature_template_list = self.get_feature_template_list(factory_default=factory_default)

        return self.list_to_dict(feature_template_list, key_name, remove_key)

    def get_policy_list_list(self, type):
        response = self.request('/dataservice/template/policy/list/{0}'.format(type))

        return response.json

    def get_vsmart_policy_list(self, type):
        response = self.request('/dataservice/template/policy/vsmart')

        response_json = response.json()

        return response_json['data']

    def get_policy_list_dict(self, type, key_name='name', remove_key=False):

        policy_list = self.get_policy_list_list(type)

        return self.list_to_dict(policy_list, key_name, remove_key=remove_key)

    def get_device_vedges(self, key_name='host-name'):
        response = self.request('/dataservice/system/device/vedges')

        device_dict = {}
        if response.json:
            device_list = response.json['data']
            for device in device_list:
                if key_name in device:
                    key = device.pop(key_name)
                    device_dict[key] = device

        return device_dict

    def get_device_controllers(self, key_name='host-name'):
        response = self.request('/dataservice/system/device/controllers')

        device_list = response.json()

        device_dict = {}
        for device in device_list['data']:
            if key_name in device:
                key = device.pop(key_name)
                device_dict[key] = device

        return device_dict

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
        response = self.request('/dataservice/template/device/config/input', method='POST', data=json.dumps(payload))

        try:
            template_input = response.json()
            column_list = template_input['header']['columns']
        except:
            return return_dict

        for column in column_list:
            if column['editable']:
                entry = {'title': column['title'],
                         'property': column['property']}
                return_dict['columns'].append(entry)

        return return_dict



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