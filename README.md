# ansible-viptela

An Ansible Role for automating a Viptela Overlay Network.  This is a hybrid role that provided both role tasks and
modules.

This role can perform the following functions:
- Add Controllers
- Set Organization Name
- Set vBond
- Set Enterprise Root CA
- Get Controller CSR
- Install Controller Certificate
- Install Serial File
- Export Templates
- Import Templates
- Add/Change/Delete Templates
- Attach Templates
- Export Policy
- Import Policy
- Add/Change/Delete Policy
- Activate Policy
- Get Template facts
- Get Device facts

### Get Device Template Facts
```yaml
- vmanage_device_template_facts:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    factory_default: no
```

### Feature Template Facts:
```yaml
- vmanage_feature_template_facts:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    factory_default: no
```

### Feature templates operations
```
- vmanage_feature_template:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    state: present
    aggregate: "{{ vmanage_templates.feature_templates }}"
```

### Device template operations
```
- vmanage_device_template:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    state: present
    aggregate: "{{ vmanage_templates.device_templates }}"
```

### Attach template to device:
```yaml
- vmanage_device_attachment:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    device: site1-vedge1
    template: colo_vedge
    variables: 
      vpn11_ipv4_address: 172.22.2.1/24
      vpn10_ipv4_address: 172.22.1.1/24
      vpn0_internet_ipv4_address: 172.16.22.2/24
      vpn0_default_gateway: 172.16.22.1
    wait: yes
    state: "{{ state }}"
```

### Policy List Facts:
```
- vmanage_policy_list_facts:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
  register: policy_list_facts
```

### Policy Definition Facts:
```
- vmanage_policy_definition_facts:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
  register: policy_definition_facts
```

### Import policy lists
```
- vmanage_policy_list:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    type: "{{ item.key }}"
    state: present
    aggregate: "{{ item.value }}"
```

### Import policy definitions
```
- vmanage_policy_definition:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    type: "{{ item.key }}"
    state: present
    aggregate: "{{ item.value }}"
```

### Import central policies
```
- vmanage_central_policy:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    state: present
    aggregate: "{{ vmanage_policy.vmanage_central_policies }}"
```

### Central Policy Facts:
```
- vmanage_central_policy_facts:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
  register: central_policy_facts
```

### Add Central Policy
```
- vmanage_central_policy:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    state: present
    aggregate: "{{ vmanage_central_policy.central_policy }}"
  register: policy_facts
```

### Activate Central Policy
```
- vmanage_central_policy:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    state: activated
    name: central_policy
    wait: yes
    aggregate: "{{ vmanage_central_policy.central_policy }}"
  register: policy_facts
```
### Activate Central Policy
```
- vmanage_central_policy:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    state: activated
    wait: yes
    aggregate: "{{ vmanage_central_policy.central_policy }}"
  register: policy_facts
```

### Get status of a device action:
```yaml
- vmanange_device_action_status:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    id: "{{ attachment_results.action_id }}"
```

### Get device facts:
```yaml
- vmanage_device_facts:
    user: "{{ ansible_user }}"
    host: "{{ ansible_host }}"
    password: "{{ ansible_password }}"
```

### Upload serial number file:
```yaml
- vmanage_fileupload:
    host: "{{ vmanage_ip }}"
    user: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    file: 'licenses/serialFile.viptela'
```



## Role Tasks


### Add vBond Host:
```yaml
- name: Add vBond Hosts
  include_role:
    name: ansible-viptela
    tasks_from: add-controller
  vars:
    device_hostname: "{{ item }}"
    device_ip: "{{ hostvars[item].transport_ip }}"
    device_personality: vbond
  loop: "{{ groups.vbond_hosts }}"
```

### Add vSmart Host:
```yaml
- name: Add vSmart Hosts
  include_role:
    name: ansible-viptela
    tasks_from: add-controller
  vars:
    device_hostname: "{{ item }}"
    device_ip: "{{ hostvars[item].transport_ip }}"
    device_personality: vsmart
  loop: "{{ groups.vsmart_hosts }}"
```

### Set Organization:
```yaml
- name: Set organization
  include_role:
    name: ansible-viptela
    tasks_from: set-org
  vars:
    org_name: "{{ organization_name }}"
```

### Set vBond:
```yaml
- name: Set vBond
  include_role:
    name: ansible-viptela
    tasks_from: set-vbond
  vars:
    vbond_ip: "{{ hostvars[vbond_controller].transport_ip }}"
```

### Set Enterprise Root CA:
```yaml
- name: Set Enterprise Root CA
  include_role:
    name: ansible-viptela
    tasks_from: set-rootca
  vars:
    root_cert: "{{lookup('file', '{{ viptela_cert_dir }}/myCA.pem')}}"
```

### Get Controller CSR:
```yaml
- name: Get Controler CSR
  include_role:
    name: ansible-viptela
    tasks_from: get-csr
  vars:
    device_ip: "{{ hostvars[item].transport_ip }}"
    device_hostname: "{{ item }}"
    csr_filename: "{{ viptela_cert_dir }}/{{ item }}.{{ env }}.csr"
  loop: "{{ groups.viptela_control }}"
```

### Installing Controller Certificates:
```yaml
- name: Install Controller Certificate
  include_role:
    name: ansible-viptela
    tasks_from: install-cert
  vars:
    device_cert: "{{lookup('file', '{{ viptela_cert_dir }}/{{ item }}.{{ env }}.crt')}}"
  loop: "{{ groups.viptela_control }}"
```

### Installing Serial File:
```yaml
- name: Install Serial File
  include_role:
   name: ansible-viptela
   tasks_from: install-serials
  vars:
   viptela_serial_file: 'licenses/viptela_serial_file.viptela'
```

License
-------

CISCO SAMPLE CODE LICENSE