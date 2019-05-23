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
    argument_spec.update(file = dict(type='str', required=True),
                         factory_default=dict(type='str', default=False),
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

    feature_template_export = viptela.get_feature_template_list(factory_default=viptela.params['factory_default'])
    device_template_export = viptela.get_device_template_list(factory_default=viptela.params['factory_default'])

    template_export = {
        'feature_templates': feature_template_export,
        'device_templates': device_template_export
    }

    if not module.check_mode:
        with open(viptela.params['file'], 'w') as f:
            json.dump(template_export, f, indent=4, sort_keys=True)

    viptela.exit_json(**viptela.result)

def main():
    run_module()

if __name__ == '__main__':
    main()