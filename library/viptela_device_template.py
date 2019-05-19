#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

import requests
from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.viptela import viptelaModule, viptela_argument_spec


def run_module():
    # define available arguments/parameters a user can pass to the module
    argument_spec = viptela_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
                         name = dict(type='str', alias='templateName'),
                         description = dict(type='str', alias='templateDescription'),
                         definition = dict(type='str', alias='templateDefinition'),
                         type = dict(type='str', alias='templateType'),
                         device_type = dict(type='list', alias='deviceType'),
                         template_min_version = dict(type='str', alias='templateMinVersion'),
                         factory_default=dict(type='bool', alias='factoryDefault'),
                         aggregate=dict(type='dict'),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    viptela = viptelaModule(module)

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    feature_templates = viptela.get_feature_template_dict(factory_default=True)
    device_templates = viptela.get_device_templates()

    if viptela.params['aggregate']:
        if viptela.params['state'] == 'present':
            for name, data in viptela.params['aggregate'].items():
                if name not in device_templates:
                    payload = {}
                    payload['templateName'] = name

                    payload['templateDescription'] = data['templateDescription']
                    payload['deviceType'] = data['deviceType']
                    payload['factoryDefault'] = data['factoryDefault']
                    payload['configType'] = data['configType']
                    #
                    # File templates are much easier in that they are just a bunch of CLI
                    #
                    if data['configType'] == 'file':
                        payload['templateConfiguration'] = data['templateConfiguration']
                        if not module.check_mode:
                            viptela.request('/dataservice/template/device/cli', method='POST', data=json.dumps(payload))
                    #
                    # Feature based templates are just a list of templates Id that make up a devie template.  We are
                    # given the name of the feature templates, but we need to translate that to the template ID
                    #
                    else:
                        generalTemplates = []
                        for template in data['generalTemplates']:
                            if template['templateName'] in feature_templates:
                                if 'subTemplates' in template:
                                    subTemplates = []
                                    for sub_template in template['subTemplates']:
                                        if sub_template['templateName'] in feature_templates:
                                            subTemplates.append(
                                                    {'templateId': feature_templates[sub_template['templateName']]['templateId'],
                                                     'templateType': sub_template['templateType']})
                                        else:
                                            viptela.fail_json(msg="There is no existing feature template named {0}".format(
                                                sub_template['templateName']))
                                    template_item = {
                                        'templateId': feature_templates[template['templateName']]['templateId'],
                                        'templateType': template['templateType'],
                                        'subTemplates': subTemplates}
                                else:
                                    template_item = {
                                        'templateId': feature_templates[template['templateName']]['templateId'],
                                        'templateType': template['templateType']}
                                generalTemplates.append(template_item)
                            else:
                                viptela.fail_json(msg="There is no existing feature template named {0}".format(template['templateName']))

                        payload['generalTemplates'] = generalTemplates
                        payload['policyId'] = ''
                        if 'connectionPreference' in data:
                            payload['connectionPreference'] = data['connectionPreference']
                        if 'connectionPreferenceRequired' in data:
                            payload['connectionPreferenceRequired'] = data['connectionPreferenceRequired']
                        payload['featureTemplateUidRange'] = []
                        # payload['templateType'] = data['templateType']
                        # payload['templateMinVersion'] = data['templateMinVersion']
                        if not module.check_mode:
                            viptela.request('/dataservice/template/device/feature', method='POST', data=json.dumps(payload))
                        viptela.result['changed'] = True

    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()

# {
#     "templateName":"test",
#     "templateDescription":"test",
#     "deviceType":"vedge-cloud",
#     "configType":"template",
#     "factoryDefault":false,
#     "policyId":"",
#     "featureTemplateUidRange":[],
#     "connectionPreferenceRequired":true,
#     "connectionPreference":true,
#     "generalTemplates":
#         [
#             {
#                 "templateId":"547c617d-abe2-42fc-af0c-15ef762d0120",
#                 "templateType":"aaa"
#             },
#             {
#                 "templateId":"8eb69d4f-3572-400d-8d70-88bcbb937e1c",
#                 "templateType":"bfd-vedge"
#             },
#             {
#                 "templateId":"666bd113-1570-4f10-95ab-94ffd2fbbb77",
#                 "templateType":"omp-vedge"
#             },
#             {
#                 "templateId":"cfc2f2e8-8608-4aea-b7ec-1309296eaa02",
#                 "templateType":"security-vedge"
#             },
#             {
#                 "templateId":"744044ff-42b1-4d8d-a3fd-a08586a784ff",
#                 "templateType":"system-vedge",
#                 "subTemplates":
#                     [
#                         {
#                             "templateId":"ee8dc781-21e8-4964-a459-80a8b1b1f0a5",
#                             "templateType":"logging"
#                         }
#                     ]
#             },
#             {
#                 "templateId":"dda3f205-e01c-4d3a-8752-65556ca019a5",
#                 "templateType":"vpn-vedge",
#                 "subTemplates":
#                     [
#                         {
#                             "templateId":"72a0377e-30f8-42c1-957c-5b37706fe75a",
#                             "templateType":"vpn-vedge-interface"
#                         }
#                     ]
#             },
#             {
#                 "templateId":"ea348dfd-74be-454e-9be1-6651dbf6273d",
#                 "templateType":"vpn-vedge"
#             }
#         ]
# }