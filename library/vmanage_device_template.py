#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

import os
from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.viptela import viptelaModule, viptela_argument_spec


def run_module():
    # define available arguments/parameters a user can pass to the module
    argument_spec = viptela_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
                         name = dict(type='str', alias='templateName'),
                         description = dict(type='str', alias='templateDescription'),
                         templates = dict(type='str', alias='generalTemplates'),
                         device_type = dict(type='list', alias='deviceType'),
                         config_type=dict(type='list', alias='configType'),
                         factory_default=dict(type='bool', alias='factoryDefault'),
                         aggregate=dict(type='list'),
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

    # Always as an aggregate... make a list if just given a single entry
    if viptela.params['aggregate']:
        device_template_list =  viptela.params['aggregate']
    else:
        if viptela.params['state'] == 'present':
            device_template_list = [
                {
                    'templateName': viptela.params['name'],
                    'templateDescription': viptela.params['description'],
                    'deviceType': viptela.params['device_type'],
                    'configType': viptela.params['config_type'],
                    'factoryDefault': viptela.params['factory_default'],
                    'generalTemplates': viptela.params['templates'],
                }
            ]
        else:
            device_template_list = [
                {
                    'templateName': viptela.params['name'],
                    'state': 'absent'
                }
            ]

    device_template_dict = viptela.get_device_template_dict(factory_default=True, remove_key=False)
    feature_template_dict = viptela.get_feature_template_dict(factory_default=True, remove_key=False)

    compare_values = ['templateDescription', 'deviceType', 'configType', 'generalTemplates']
    ignore_values = ["lastUpdatedOn", "lastUpdatedBy", "templateId", "createdOn", "createdBy"]

    for device_template in device_template_list:
        if viptela.params['state'] == 'present':
            #
            # Convert template names to template IDs
            #
            if device_template['configType'] == 'template':
                generalTemplates = []
                for template in device_template['generalTemplates']:
                    if template['templateName'] in feature_template_dict:
                        if 'subTemplates' in template:
                            subTemplates = []
                            for sub_template in template['subTemplates']:
                                if sub_template['templateName'] in feature_template_dict:
                                    subTemplates.append(
                                        {'templateId': feature_template_dict[sub_template['templateName']]['templateId'],
                                         'templateType': sub_template['templateType']})
                                else:
                                    viptela.fail_json(msg="There is no existing feature template named {0}".format(
                                        sub_template['templateName']))
                            template_item = {
                                'templateId': feature_template_dict[template['templateName']]['templateId'],
                                'templateType': template['templateType'],
                                'subTemplates': subTemplates}
                        else:
                            template_item = {
                                'templateId': feature_template_dict[template['templateName']]['templateId'],
                                'templateType': template['templateType']}
                        generalTemplates.append(template_item)
                    else:
                        viptela.fail_json(msg="There is no existing feature template named {0}".format(template['templateName']))

                device_template['generalTemplates'] = generalTemplates
            if device_template['templateName'] in device_template_dict:
                changed_items = viptela.compare_payloads(device_template, device_template_dict[device_template['templateName']], compare_values=compare_values)
                if changed_items:
                    viptela.result['changed'] = True
                    viptela.result['what_changed'] = changed_items
                    viptela.result['old_payload'] = device_template_dict[device_template['templateName']]
                    viptela.result['new_payload'] = device_template
                    if not module.check_mode:
                        viptela.request('/dataservice/template/device/feature/{0}'.format(device_template_dict[device_template['templateName']]['templateId']),
                                        method='PUT', data=json.dumps(device_template))
            else:
                if not module.check_mode:
                    viptela.request('/dataservice/template/device/feature/', method='POST', data=json.dumps(device_template))
                viptela.result['changed'] = True
        else:
            if device_template['templateName'] in device_template_dict:
                if not module.check_mode:
                    viptela.request('/dataservice/template/device/{0}'.format(device_template_dict[device_template['templateName']]['templateId']),
                                    method='DELETE')
                viptela.result['changed'] = True


    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()