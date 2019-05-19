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

    # vSmart policies
    # response = viptela.request('/dataservice/template/policy/vsmart')
    # response_json = response.json()
    # vsmart_policies = response_json['data']

    # Site lists
    site_lists = viptela.get_policy_list_list('site')

    # Prefix lists
    prefix_lists = viptela.get_policy_list_list('prefix')

    # VPN lists
    vpn_lists = viptela.get_policy_list_list('vpn')

    policy_lists = {
        # 'vsmart_policies': vsmart_policies,
        'vmanage_site_lists': site_lists,
        'vmanage_prefix_lists': prefix_lists,
        'vmanage_vpn_lists': vpn_lists,
    }

    viptela.result['policy_lists'] = policy_lists

    # if viptela.params['file']:
    #     if not module.check_mode:
    #         with open(viptela.params['file'], 'w') as f:
    #             json.dump(policy_export, f, indent=4, sort_keys=True)

    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()