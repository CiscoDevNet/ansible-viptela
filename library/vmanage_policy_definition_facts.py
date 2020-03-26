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
    policy_definitions = []
    policy_list_dict = viptela.get_policy_list_dict('all', key_name='listId')
    for list_type in viptela.POLICY_DEFINITION_TYPES:
        definition_list = viptela.get_policy_definition_list(list_type)
        for definition in definition_list:
            definition_detail = viptela.get_policy_definition(list_type, definition['definitionId'])
            for sequence in definition_detail['sequences']:
                for entry in sequence['match']['entries']:
                    entry['listName'] = policy_list_dict[entry['ref']]['name']
                    entry['listType'] = policy_list_dict[entry['ref']]['type']
            policy_definitions.append(definition_detail)

    viptela.result['policy_definitions'] = policy_definitions

    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()