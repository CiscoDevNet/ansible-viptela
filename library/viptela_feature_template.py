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


    feature_templates = viptela.get_feature_template_dict(factory_default=True)

    if viptela.params['aggregate']:
        if viptela.params['state'] == 'present':
            for name, data in viptela.params['aggregate'].items():
                if name not in feature_templates:
                    payload = {}
                    payload['templateName'] = name
                    payload['templateDescription'] = data['templateDescription']
                    payload['deviceType'] = data['deviceType']
                    payload['templateDefinition'] = data['templateDefinition']
                    payload['templateType'] = data['templateType']
                    payload['templateMinVersion'] = data['templateMinVersion']
                    payload['factoryDefault'] = data['factoryDefault']
                    if not module.check_mode:
                        response = viptela.request('/dataservice/template/feature/', method='POST', data=json.dumps(payload))
                    viptela.result['changed'] = True

    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()
    
{
    "templateName":"vpn0_test",
    "templateDescription":"vpn0",
    "templateType":"vpn-vedge",
    "deviceType":["vedge-cloud"],
    "factoryDefault":false,
    "templateMinVersion":"15.0.0",
    "templateDefinition":
        {
            "ecmp-hash-key":
                {
                    "layer4":
                        {
                            "vipObjectType":"object",
                            "vipType":"ignore",
                            "vipValue":"false",
                            "vipVariableName":"vpn_layer4"}
                },
            "host":
                {
                    "vipObjectType":"tree",
                    "vipPrimaryKey":["hostname"],
                    "vipType":"ignore",
                    "vipValue":[]},
            "ip":
                {
                    "gre-route":{},
                    "ipsec-route":{},
                    "route":{
                        "vipObjectType":"tree",
                        "vipPrimaryKey":["prefix"],
                        "vipType":"constant",
                        "vipValue":
                            [
                                {
                                    "next-hop":
                                        {
                                            "vipObjectType":"tree",
                                            "vipPrimaryKey":["address"],
                                            "vipType":"constant",
                                            "vipValue":
                                                [
                                                    {
                                                        "address":
                                                            {
                                                                "vipObjectType":"object",
                                                                "vipType":"variableName",
                                                                "vipValue":"",
                                                                "vipVariableName":"vpn0_default_gateway"
                                                            },
                                                        "distance":
                                                            {
                                                                "vipObjectType":"object",
                                                                "vipType":"ignore",
                                                                "vipValue":1,
                                                                "vipVariableName":"vpn_next_hop_ip_distance_0"
                                                            },
                                                        "priority-order":
                                                            [
                                                                "address","distance"
                                                            ]
                                                    }
                                                ]
                                        },
                                    "prefix":
                                        {
                                            "vipObjectType":"object",
                                            "vipType":"constant",
                                            "vipValue":"0.0.0.0/0",
                                            "vipVariableName":"vpn_ipv4_ip_prefix"
                                        },
                                    "priority-order":
                                        [
                                            "prefix","next-hop"
                                        ]
                                }
                            ]
                    }
                },
            "ipv6":{},
            "name":
                {
                    "vipObjectType":"object",
                    "vipType":"ignore",
                    "vipVariableName":"vpn_name"
                },
            "omp":
                {
                    "advertise":
                        {
                            "vipObjectType":"tree",
                            "vipPrimaryKey":["protocol"],
                            "vipType":"ignore",
                            "vipValue":[]
                        },
                    "ipv6-advertise":
                        {
                            "vipObjectType":"tree",
                            "vipPrimaryKey":["protocol"],
                            "vipType":"ignore","vipValue":[]}},"service":{"vipObjectType":"tree","vipPrimaryKey":["svc-type"],"vipType":"ignore","vipValue":[]},"tcp-optimization":{"vipObjectType":"node-only","vipType":"ignore","vipValue":"false","vipVariableName":"vpn_tcp_optimization"},"vpn-id":{"vipObjectType":"object","vipType":"constant","vipValue":0}}}