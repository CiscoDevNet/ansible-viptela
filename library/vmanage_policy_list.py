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
                         type = dict(type ='str', required = True, choices= ['color', 'vpn', 'site', 'app',
                            'dataprefix', 'prefix', 'aspath', 'class', 'community', 'extcommunity', 'mirror', 'tloc',
                            'sla', 'policer']),
                         entries = dict(type ='list'),
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
        policy_list =  viptela.params['aggregate']
    else:
        policy_list = [
            {
                "name": viptela.params['name'],
                "description": viptela.params['description'],
                "type": viptela.params['type'],
                "entries": viptela.params['entries'],
            }
        ]

    policy_list_dict = viptela.get_policy_list_dict(viptela.params['type'], remove_key=False)

    ignore_values = ["lastUpdated", "listId"]

    # Import site lists
    for list in policy_list:
        if viptela.params['state'] == 'present':
            if list['name'] in policy_list_dict:
                changed_items = viptela.compare_payloads(list, policy_list_dict[list['name']], ignore_values=ignore_values)
                if changed_items:
                    viptela.result['changed'] = True
                    viptela.result['what_changed'] = changed_items
                    if not module.check_mode:
                        viptela.request('/dataservice/template/policy/list/{0}/{1}'.format(list['type'], policy_list_dict[list['name']]['listId']),
                                        method='PUT', data=json.dumps(list))
            else:
                if not module.check_mode:
                    viptela.request('/dataservice/template/policy/list/{0}/'.format(list['type']),
                                    method='POST', data=json.dumps(list))
                viptela.result['changed'] = True
        else:
            if list['name'] in policy_list_dict:
                if not module.check_mode:
                    viptela.request('/dataservice/template/policy/list/{0}/{1}'.format(list['type'], list['listId']),
                                    method='DELETE')
                viptela.result['changed'] = True

    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()