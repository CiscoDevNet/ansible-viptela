pipeline {
    agent {
        dockerfile {
            filename 'Dockerfile'
            args  '-v /etc/passwd:/etc/passwd'
        }
    }
    options {
      disableConcurrentBuilds()
      lock resource: 'jenkins_sdwan'
    }
    environment {
        VIRL_USERNAME = credentials('cpn-virl-username')
        VIRL_PASSWORD = credentials('cpn-virl-password')
        VIRL_HOST = credentials('cpn-virl-host')
        VIRL_SESSION = "jenkins_sdwan"
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
    }          
}

