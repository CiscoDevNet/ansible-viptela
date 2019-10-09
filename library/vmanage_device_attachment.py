#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

import time
from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.viptela import viptelaModule, viptela_argument_spec


def run_module():
    action_id = None
    action_status = None
    action_activity = None
    action_config = None

    # define available arguments/parameters a user can pass to the module
    argument_spec = viptela_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present','query'], default='present'),
                         device = dict(type='str', required=True),
                         template = dict(type='str'),
                         variables=dict(type='dict', default={}),
                         wait=dict(type='bool', default=False),
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

    # First, get the list of vedges and see if this device is in the list
    devices = viptela.get_device_dict('vedges')
    if viptela.params['device'] not in devices:
        # Next, get the list of controllers and see if this device is in the list
        devices = viptela.get_device_dict('controllers')
        if viptela.params['device'] not in devices:
            # This device is neither a vedge or a controller, so error and inform accordingly
            viptela.fail_json(msg='Device {0} not found.'.format(viptela.params['device']))

    device_data = devices[viptela.params['device']]

    if viptela.params['state'] == 'present':
        if ('system-ip' not in device_data):
            viptela.fail_json(msg='system-ip must be defined for {0}.'.format(viptela.params['device']))
        if ('site-id' not in device_data):
            viptela.fail_json(msg='site-id must be defined for {0}.'.format(viptela.params['device']))

        # Get template data and see if it is a real template
        device_template_dict = viptela.get_device_template_dict(factory_default=True)
        if viptela.params['template']:
            if viptela.params['template'] not in device_template_dict:
                viptela.fail_json(msg='Template {0} not found.'.format(viptela.params['template']))
            template_data = device_template_dict[viptela.params['template']]
        else:
            viptela.fail_json(msg='Must specify a template with state present')

        # Make sure they passed in the required variables
        template_variables = viptela.get_template_variables(device_template_dict[viptela.params['template']]['templateId'])
        if template_variables:
            if viptela.params['variables']:
                for variable in template_variables:
                    if variable not in viptela.params['variables']:
                        viptela.fail_json(msg='Template {0} requires variables: {1}'.format(viptela.params['template'], ', '.join(template_variables)))


        # Construct the variable payload
        device_template_variables = {
                "csv-status": "complete",
                "csv-deviceId": device_data['uuid'],
                "csv-deviceIP": device_data['deviceIP'],
                "csv-host-name": viptela.params['device'],
                # "csv-templateId": template_data['templateId'],
                '//system/host-name': viptela.params['device'],
                '//system/system-ip': device_data['system-ip'],
                '//system/site-id': device_data['site-id'],
            }

        # For each of the variables passed in, match them up with the names of the variables requires in the
        # templates and add them with the corresponding property.  The the variables is not in template_variables,
        # just leave it out since it is not required.
        for key, value in viptela.params['variables'].items():
            if key in template_variables:
                property = template_variables[key]
                device_template_variables[property] = viptela.params['variables'][key]

        if viptela.params['device'] in template_data['attached_devices']:
            # Add the template ID to the device's variable payload because we'll need it for comparison and update.
            # device_template_variables['csv-templateId'] = template_data['templateId']
            # The device is already attached to the template.  We need to see if any of the input changed, so we make
            # an API call to get the input on last attach
            payload = {
                "templateId": template_data['templateId'],
                "deviceIds": [device_data['uuid']],
                "isEdited": "true",
                "isMasterEdited": "false"
            }
            response = viptela.request('/dataservice/template/device/config/input/', method='POST', payload=payload)
            if response.json and 'data' in response.json:
                if response.json['data'][0] != device_template_variables:
                    viptela.result['changed'] = True
                    viptela.result['current_variables'] = response.json['data']
                    viptela.result['new_variables'] = device_template_variables
                else:
                    viptela.result['changed'] = False
        else:
            viptela.result['changed'] = True

        if not module.check_mode and viptela.result['changed']:
            payload = {
                "deviceTemplateList":
                [
                    {
                        "templateId": template_data['templateId'],
                        "device": [device_template_variables],
                        "isEdited": False,
                        "isMasterEdited": False
                    }
                ]
            }
            response = viptela.request('/dataservice/template/device/config/attachfeature', method='POST', payload=payload)
            if response.json:
                action_id = response.json['id']
            else:
                viptela.fail_json(msg='Did not get action ID after attaching device to template.')
    elif viptela.params['state'] == 'absent':
        if 'templateId' in device_data:
            viptela.result['changed'] = True
            payload = {
                    "deviceType": device_data['deviceType'],
                    "devices":[
                        {
                            "deviceId": device_data['uuid'],
                            "deviceIP": device_data['deviceIP']
                        }
                    ]
                }
            if not module.check_mode:
                response = viptela.request('/dataservice/template/config/device/mode/cli', method='POST', payload=payload)
                if response.json:
                    action_id = response.json['id']
                else:
                    viptela.fail_json(msg='Did not get action ID after attaching device to template.')
    elif viptela.params['state'] == 'query':
        # Get template data and see if it is a real template
        device_template_dict = viptela.get_device_template_dict(factory_default=True)
        if viptela.params['template']:
            if viptela.params['template'] not in device_template_dict:
                viptela.fail_json(msg='Template {0} not found.'.format(viptela.params['template']))
            template_data = device_template_dict[viptela.params['template']]
        else:
            viptela.fail_json(msg='Must specify a template with state present')

        payload = {
            "templateId": template_data['templateId'],
            "deviceIds": [device_data['uuid']],
            "isEdited": "false",
            "isMasterEdited": "false"
        }

        response = viptela.request('/dataservice/template/device/config/input/', method='POST', payload=payload)
        if response.json:
            viptela.result['response'] = response.json
    else:
        pass
    # If told, wait for the status of the request and report it
    if viptela.params['wait'] and action_id:
        viptela.waitfor_action_completion(action_id)

    viptela.logout()
    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()

# {
#     "deviceType":"vedge",
#     "devices":[
#         {
#             "deviceId":"9c74c69e-acba-41dd-811a-5ab0e3086786",
#             "deviceIP":"10.255.110.1"
#         }
#     ]
# }

#{
#  "deviceTemplateList":
#  [
#    {
#      "templateId":"da237d75-4aa1-438e-918c-3b2b80850925",
#      "device": [
#        {
#          "csv-status":"complete",
#          "csv-deviceId":"9c74c69e-acba-41dd-811a-5ab0e3086786",
#          "csv-deviceIP":"10.255.110.1",
#          "csv-host-name":"site1-vedge1",
#          "/11/ge0/2/interface/ip/address":"172.22.2.1/24",
#          "/10/ge0/1/interface/ip/address":"172.22.1.1/24",
#          "/0/vpn-instance/ip/route/0.0.0.0/0/next-hop/vpn0_default_gateway/address":"172.16.22.1",
#          "/0/ge0/0/interface/ip/address":"172.16.22.2/24",
#          "/0/ge0/0/interface/tunnel-interface/color/value":"public-internet",
#          "//system/host-name":"site1-vedge1",
#          "//system/system-ip":"10.255.110.1",
#          "//system/site-id":"110",
#          "csv-templateId":"da237d75-4aa1-438e-918c-3b2b80850925"
#        }
#      ],
#      "isEdited":false,
#      "isMasterEdited":false
#    }
#  ]
#}
