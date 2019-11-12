pipeline {
    agent {
        dockerfile {
            filename 'Dockerfile'
            args  '-v /etc/passwd:/etc/passwd'
        }
    }
    options {
      disableConcurrentBuilds()
      lock resource: 'jenkins_testing'
    }
    environment {
        VIRL_USERNAME = credentials('cpn-virl-username')
        VIRL_PASSWORD = credentials('cpn-virl-password')
        VIRL_HOST = credentials('cpn-virl-host')
        VIRL_LAB = "jenkins_ansible-viptela"
        VIPTELA_ORG = credentials('viptela-org')
        LICENSE_TOKEN = credentials('license-token')
        HOME = "${WORKSPACE}"
        DEFAULT_LOCAL_TMP = "${WORKSPACE}/ansible"
    }
    stages {
        stage('Checkout Code') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/master']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: scm.extensions + [[$class: 'SubmoduleOption',
                        parentCredentials: true,
                        disableSubmodules: true,
                        recursiveSubmodules: false,
                        reference: '',
                        trackingSubmodules: false]],
                    /* userRemoteConfigs: scm.userRemoteConfigs */
                    userRemoteConfigs: [[url: 'https://github.com/ciscodevnet/sdwan-devops']]
                ])
                checkout([$class: 'GitSCM',
                    branches: [[name: '*/master']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'roles/ansible-virl']],
                    submoduleCfg: [],
                    userRemoteConfigs: [[url: 'https://github.com/ciscodevnet/ansible-virl']]
                ])
                checkout([$class: 'GitSCM',
                    branches: scm.branches,
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'roles/ansible-viptela']],
                    submoduleCfg: [],
                    userRemoteConfigs: scm.userRemoteConfigs
                ])                
            }
        }
        stage('Build VIRL Topology') {
           steps {
                echo 'Create local CA...'
                ansiblePlaybook disableHostKeyChecking: true, playbook: 'build-ca.yml'                    
                echo 'Running build.yml...'
                ansiblePlaybook disableHostKeyChecking: true, playbook: 'build-virl.yml'
           }
        }
        stage('Configure SD-WAN Fabric') {
           steps {
                echo 'Configure Viptela Control Plane...'
                withCredentials([file(credentialsId: 'viptela-serial-file', variable: 'VIPTELA_SERIAL_FILE')]) {
                    ansiblePlaybook disableHostKeyChecking: true, extras: '-e sdwan_serial_file=${VIPTELA_SERIAL_FILE}', playbook: 'config-virl.yml'
                }
                echo 'Deploying edges...'
                ansiblePlaybook disableHostKeyChecking: true, playbook: 'deploy-virl.yml'
           }
        }
        stage('Running Tests') {
           steps {
                echo 'Check SD-WAN...'
                ansiblePlaybook disableHostKeyChecking: true, playbook: 'waitfor-sync.yml'
                echo 'Check SD-WAN...'
                ansiblePlaybook disableHostKeyChecking: true, playbook: 'check-sdwan.yml'
           }
        }  
    }    
    post {
        always {
            ansiblePlaybook disableHostKeyChecking: true, playbook: 'clean-virl.yml'
            cleanWs()
        }
    }          
}

