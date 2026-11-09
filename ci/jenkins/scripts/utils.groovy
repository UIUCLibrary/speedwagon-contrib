def createWindowUVConfig(Map args = [:]){
    def scriptFile = args.scriptFile ?: "ci\\jenkins\\scripts\\new-uv-global-config.ps1"
    if(! fileExists(scriptFile)){
        ws("${env.WORKSPACE_TMP}\\scm") {
            checkout scm
            scriptFile = "${env.WORKSPACE_TMP}\\scm\\ci\\jenkins\\scripts\\new-uv-global-config.ps1"
        }
    }
    return powershell(
        label: 'Setting up uv.toml config file',
        script: "& ${scriptFile} \$env:UV_INDEX_URL \$env:UV_EXTRA_INDEX_URL",
        returnStdout: true
    ).trim()
}

def createUnixUvConfig(Map args = [:]){
    def scriptFile = args.scriptFile ?: 'ci/jenkins/scripts/create_uv_config.sh'
    if(! fileExists(scriptFile)){
        ws("${env.WORKSPACE_TMP}//scm") {
            checkout scm
            scriptFile = "${env.WORKSPACE_TMP}/ci/jenkins/scripts/create_uv_config.sh"
        }
    }
    return sh(label: 'Setting up uv.toml config file', script: "sh ${scriptFile} " + '$UV_INDEX_URL $UV_EXTRA_INDEX_URL', returnStdout: true).trim()
}

return this