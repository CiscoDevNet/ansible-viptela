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
- Attach Templates
- Get Template facts
- Get Device facts

## Modules

### Export device and feature templates:
```yaml
- viptela_template_export:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    factory_default: no
    file: "{{ file }}"
```

### Import device and feature templates:
```yaml
- viptela_template_import:
    host: "{{ vmanage_ip }}"
    user: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    file: "{{ file }}"
```

### Attach template to device:
```yaml
- viptela_device_attachment:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    device: "{{ inventory_hostname }}"
    template: "{{ viptela.template.name }}"
    variables: "{{ viptela.template.variables | default(omit) }}"
    wait: no
    state: "{{ state }}"
```

### Get status of a device action:
```yaml
- viptela_device_action_status:
    user: "{{ ansible_user }}"
    host: "{{ vmanage_ip }}"
    password: "{{ ansible_password }}"
    id: "{{ attachment_results.action_id }}"
```

### Get template facts:
```yaml
- viptela_template_facts:
    user: "{{ ansible_user }}"
    host: "{{ ansible_host }}"
    password: "{{ ansible_password }}"
    factory_default: no
```

### Get device facts:
```yaml
- viptela_device_facts:
    user: "{{ ansible_user }}"
    host: "{{ ansible_host }}"
    password: "{{ ansible_password }}"
```

### Upload serial number file:
```yaml
- viptela_fileupload:
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