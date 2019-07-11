#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.viptela import viptelaModule, viptela_argument_spec
from collections import OrderedDict

def run_module():
    # define available arguments/parameters a user can pass to the module
    argument_spec = viptela_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
                         file=dict(type='str'),
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

    if not module.check_mode:
        response = viptela.request('/dataservice/device/action/software/package', method='POST',
                                   files={'file': open(module.params['file'], 'rb')},
                                   data={'validity':'valid', 'upload':'true'},
                                   headers=None)

        viptela.result['msg'] = response.json['vedgeListUploadStatus']
        if 'successfully' in response.json['vedgeListUploadStatus']:
            viptela.result['changed'] = True

    viptela.exit_json(**viptela.result)


def main():
    run_module()


if __name__ == '__main__':
    main()