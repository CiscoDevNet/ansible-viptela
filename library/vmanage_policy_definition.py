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
                         aggregate=dict(type='list'),
                         name=dict(type='str'),
                         description = dict(type = 'str'),
                         type = dict(type ='str', required = True, choices= ['cflowd', 'dnssecurity', 'control',
                                'hubandspoke', 'acl', 'vpnmembershipgroup', 'mesh', 'rewriterule', 'data',
                                'rewriterule', 'aclv6']),
                         sequences = dict(type ='list'),
                         default_action = dict(type ='dict', alias='defaultAction'),
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
        definition_list =  viptela.params['aggregate']
    else:
        definition_list = [
            {
                "name": viptela.params['name'],
                "description": viptela.params['description'],
                "type": viptela.params['type'],
                "sequences": viptela.params['sequences'],
                "defaultAction": viptela.params['default_action']
            }
        ]

    policy_definition_dict = viptela.get_policy_definition_dict(viptela.params['type'], remove_key=False)

    compare_values = ["name", "description", "type", "sequences", "defaultAction"]

    # Import site lists
    for list in definition_list:
        payload = {
            "name": list['name'],
            "description": list['description'],
            "type": list['type'],
            "sequences": list['sequences'],
            "defaultAction": list['defaultAction']
        }
        if viptela.params['state'] == 'present':
            if list['name'] in policy_definition_dict:
                changed_items = viptela.compare_payloads(list, policy_definition_dict[list['name']], compare_values=compare_values)
                if changed_items:
                    viptela.result['changed'] = True
                    viptela.result['what_changed'] = changed_items
                    payload['sequences'] = viptela.convert_sequences_to_id(list['sequences'])
                    if not module.check_mode:
                        viptela.request('/dataservice/template/policy/definition/{0}/{1}'.format(list['type'], policy_definition_dict[list['name']]['definitionId']),
                                        method='PUT', payload=payload)
            else:
                payload['sequences'] = viptela.convert_sequences_to_id(list['sequences'])
                if not module.check_mode:
                    viptela.request('/dataservice/template/policy/definition/{0}/'.format(list['type']),
                                    method='POST', payload=payload)
                viptela.result['changed'] = True
        else:
            if list['name'] in policy_definition_dict:
                if not module.check_mode:
                    viptela.request('/dataservice/template/policy/definition/{0}/{1}'.format(list['type'], list['definitionId']),
                                    method='DELETE')
                viptela.result['changed'] = True

    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()