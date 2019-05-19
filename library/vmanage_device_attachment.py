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
    # define available arguments/parameters a user can pass to the module
    argument_spec = viptela_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
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



    # Get device data and see if it is a real device
    devices = viptela.get_device_vedges()
    if viptela.params['device'] not in devices:
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

        if viptela.params['device'] in template_data['attached_devices']:
            viptela.result['changed'] = False
        else:
            viptela.result['changed'] = True
            device_entry = {
                "csv-status": "complete",
                "csv-deviceId": device_data['uuid'],
                "csv-deviceIP": device_data['deviceIP'],
                "csv-host-name": viptela.params['device'],
                "csv-templateId": template_data['templateId'],
                '//system/host-name': viptela.params['device'],
                '//system/system-ip': device_data['system-ip'],
                '//system/site-id': device_data['site-id'],
            }
            for key, value in viptela.params['variables'].items():
                device_entry[key] = value

            payload = {
                "deviceTemplateList":
                [
                    {
                        "templateId": template_data['templateId'],
                        "device": [device_entry],
                        "isEdited": 'false',
                        "isMasterEdited": 'false'
                    }
                ]
            }
            if not module.check_mode:
                response = viptela.request('/dataservice/template/device/config/attachfeature', method='POST', data=json.dumps(payload))
                if response.json:
                    viptela.result['action_id'] = response.json['id']

                    # If told, wait for the status of the request and report it
                    if viptela.params['wait']:
                        status = 'in_progress'
                        while status == "in_progress":
                            response = viptela.request('/dataservice/device/action/status/{0}'.format(post_response['id']))
                            if resonse.json:
                                status = response.json['summary']['status']
                                time.sleep(5)
                            viptela.result['action_status'] = response_json['data'][0]['statusId']
                            viptela.result['action_activity'] = response_json['data'][0]['currentActivity']
    else:
        if 'templateId' in device_data:
            viptela.result['changed'] = True
            payload = {
                    "deviceType": device_data['deviceType'],
                    "devices":[
                        {
                            "deviceId": device_data['deviceType'],
                            "deviceIP": device_data['uuid']
                        }
                    ]
                }
            if not module.check_mode:
                response = viptela.request('/dataservice/template/config/device/mode/cli', method='POST', data=json.dumps(payload))
                post_response = response.json()
                viptela.result['action_id'] = post_response['id']

                # If told, wait for the status of the request and report it
                if viptela.params['wait']:
                    status = 'in_progress'
                    while status == "in_progress":
                        response = viptela.request('/dataservice/device/action/status/{0}'.format(post_response['id']))
                        response_json = response.json()
                        status = response_json['summary']['status']
                        time.sleep(5)
                    viptela.result['action_status'] = response_json['data'][0]['statusId']
                    viptela.result['action_activity'] = response_json['data'][0]['currentActivity']

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