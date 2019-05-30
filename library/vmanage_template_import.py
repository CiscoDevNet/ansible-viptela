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
    argument_spec.update(file = dict(type='str', required=True),
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

    # Read in the datafile
    if not os.path.exists(viptela.params['file']):
        module.fail_json(msg='Cannot find file {0}'.format(viptela.params['file']))
    with open(viptela.params['file']) as f:
        template_data = json.load(f)

    # Separate the feature template data from the device template data
    feature_template_data = template_data['feature_templates']
    device_template_data = template_data['device_templates']

    # Process the feature templates
    feature_templates = viptela.get_feature_template_dict(factory_default=True)
    for data in feature_template_data:
        if data['templateName'] not in feature_templates:
            payload = {
                'templateName': data['templateName'],
                'templateDescription': data['templateDescription'],
                'deviceType': data['deviceType'],
                'templateDefinition': data['templateDefinition'],
                'templateType': data['templateType'],
                'templateMinVersion': data['templateMinVersion'],
                'factoryDefault': data['factoryDefault'],
                'configType': data['configType'],
                'feature': data['feature'],
            }
            viptela.result['payload'] = payload
            # Don't make the actual POST if we are in check mode
            if not module.check_mode:
                response = viptela.request('/dataservice/template/feature/', method='POST', data=json.dumps(payload))
            viptela.result['changed'] = True

    # Process the device templates
    device_templates = viptela.get_device_template_dict()
    for device_template in device_template_data:
        if device_template['templateName'] not in device_templates:
            payload = {
                'templateName': device_template['templateName'],
                'templateDescription': device_template['templateDescription'],
                'deviceType': device_template['deviceType'],
                'factoryDefault': device_template['factoryDefault'],
                'configType': device_template['configType']
            }

            #
            # File templates are much easier in that they are just a bunch of CLI
            #
            if device_template['configType'] == 'file':
                payload['templateConfiguration'] = device_template['templateConfiguration']
                if not module.check_mode:
                    viptela.request('/dataservice/template/device/cli', method='POST', payload=payload)
            #
            # Feature based templates are just a list of templates Id that make up a devie template.  We are
            # given the name of the feature templates, but we need to translate that to the template ID
            #
            else:
                if 'generalTemplates' in device_template:
                    payload['generalTemplates'] = viptela.generalTemplates_to_id(device_template['generalTemplates'])
                else:
                    viptela.fail_json(msg="No generalTemplates found in device template", data=device_template)
                payload['policyId'] = ''
                if 'connectionPreference' in device_template:
                    payload['connectionPreference'] = device_template['connectionPreference']
                if 'connectionPreferenceRequired' in device_template:
                    payload['connectionPreferenceRequired'] = device_template['connectionPreferenceRequired']
                payload['featureTemplateUidRange'] = []
                # Don't make the actual POST if we are in check mode
                if not module.check_mode:
                    viptela.request('/dataservice/template/device/feature', method='POST', payload=payload)
                viptela.result['changed'] = True

    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()