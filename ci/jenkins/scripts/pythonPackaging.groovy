def testLinuxPackage = { Map args = [:] ->
    // ========================================================================
    //      Args Parsing:
    // ========================================================================

    if(!args.arch){
        error "Missing required parameter: arch"
    }
    def arch = args.arch

    if(!args.pythonVersion){
        error "Missing required parameter: pythonVersion"
    }
    def pythonVersion = args.pythonVersion

    if(!args.packageType){
        error "Missing required parameter: packageType"
    }
    def packageType = args.packageType

    def dockerImage = args.dockerImage ? args.dockerImage : 'ghcr.io/astral-sh/uv:debian'
    def retryAmount = args.retryAmount ?: 3
    def stashName = args.stashName ?: 'PYTHON_PACKAGES'
    // ========================================================================

    node("linux && ${arch} && docker"){
        try{
            checkout scm
            def utils = load('ci/jenkins/scripts/utils.groovy')
            unstash "${stashName}"
            docker.image(dockerImage)
                .inside(
                    "--label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\" " +
                    '--mount source=python-tmp-speedwagon-contrib,target=/tmp --tmpfs /.local/share:exec --tmpfs /.local/bin:exec'
                ){
                withEnv([
                    'PIP_CACHE_DIR=/tmp/pipcache',
                    'UV_TOOL_DIR=/tmp/uvtools',
                    'UV_PYTHON_CACHE_DIR=/tmp/uvpython',
                    'UV_CACHE_DIR=/tmp/uvcache',
                    "UV_CONFIG_FILE=${utils.createUnixUvConfig()}"
                ]){
                    sh(label: 'Installing required Python version if not already installed', script: "uv python find cpython-${pythonVersion} --quiet 2>/dev/null || uv python install cpython-${pythonVersion}")
                    def attempt = 0
                    findFiles(glob: packageType == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz').each{
                        retry(retryAmount){
                            attempt += 1
                            withEnv([(attempt == 1) ? 'UV_OFFLINE=1' : 'UV_OFFLINE=0']){
                                sh(
                                    label: "Testing with tox: ${(attempt == 1) ? 'Offline' : 'Online'}",
                                    script: "uv run --only-group=tox-uv --isolated --frozen tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"
                                )
                            }
                        }
                    }
                }
            }
        } finally {
            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
        }
    }
}

def testMacOsPackage = { Map args = [:] ->
    // ========================================================================
    //      Args Parsing:
    // ========================================================================

    if(!args.arch){
        error "Missing required parameter: arch"
    }
    def arch = args.arch

    if(!args.pythonVersion){
        error "Missing required parameter: pythonVersion"
    }
    def pythonVersion = args.pythonVersion

    if(!args.packageType){
        error "Missing required parameter: packageType"
    }
    def packageType = args.packageType
    def retryAmount = args.retryAmount ?: 3
    def stashName = args.stashName ?: 'PYTHON_PACKAGES'

    // ========================================================================

    node("macos && ${arch} && python3"){
        try{
            checkout scm
            def utils = load('ci/jenkins/scripts/utils.groovy')
            unstash "${stashName}"
            withEnv([
                "TOX_UV_PATH=${env.WORKSPACE}/venv/bin/uv",
                "UV_CONFIG_FILE=${utils.createUnixUvConfig()}"
            ]){
                sh """python3 -m venv venv --clear
                      ./venv/bin/pip install --disable-pip-version-check uv
                   """
               sh(label: 'Installing required Python version if not already installed', script: "./venv/bin/uv python find cpython-${pythonVersion} --quiet 2>/dev/null || ./venv/bin/uv python install cpython-${pythonVersion}")
                def attempt = 0
                findFiles(glob: packageType == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz').each{
                    retry(retryAmount){
                        attempt += 1
                        withEnv([(attempt == 1) ? 'UV_OFFLINE=1' : 'UV_OFFLINE=0']){
                            sh(
                                label: "Testing with tox: ${(attempt == 1) ? 'Offline' : 'Online'}",
                                script: "./venv/bin/uv run --only-group=tox-uv --isolated --frozen tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"
                            )
                        }
                    }
                }
            }
        } finally {
            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
        }
    }
}

def testWindowsPackage = { Map args = [:] ->
    // ========================================================================
    //      Args Parsing:
    // ========================================================================

    if(!args.arch){
        error "Missing required parameter: arch"
    }
    def arch = args.arch

    if(!args.pythonVersion){
        error "Missing required parameter: pythonVersion"
    }
    def pythonVersion = args.pythonVersion

    if(!args.packageType){
        error "Missing required parameter: packageType"
    }
    def packageType = args.packageType

    def dockerImage = args.dockerImage ? args.dockerImage : 'python'
    def retryAmount = args.retryAmount ?: 3
    def stashName = args.stashName ?: 'PYTHON_PACKAGES'

    // ========================================================================

    node("windows && ${arch} && docker"){
        try{
            checkout scm
            def utils = load('ci/jenkins/scripts/utils.groovy')
            unstash "${stashName}"
            docker.image(dockerImage).inside(
                "--label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\" " +
                '--mount type=volume,source=uv_python_cache_dir,target=c:\\Users\\ContainerUser\\Documents\\cache\\uvpython'
                + ' --mount type=volume,source=pipcache,target=c:\\Users\\ContainerUser\\Documents\\cache\\pipcache'
                + ' --mount type=volume,source=uv_cache_dir,target=c:\\Users\\ContainerUser\\Documents\\cache\\uvcache'
            ){
                withEnv([
                    'PIP_CACHE_DIR=c:\\Users\\ContainerUser\\Documents\\cache\\pipcache',
                    'UV_TOOL_DIR=c:\\Users\\ContainerUser\\Documents\\uvtools',
                    'UV_PYTHON_CACHE_DIR=c:\\Users\\ContainerUser\\Documents\\cache\\uvpython',
                    'UV_CACHE_DIR=c:\\Users\\ContainerUser\\Documents\\cache\\uvcache',
                    'UV_LINK_MODE=copy',
                    "TOX_UV_PATH=${env.WORKSPACE}\\venv\\Scripts\\uv.exe",
                    "UV_CONFIG_FILE=${utils.createWindowUVConfig()}"
                ]){
                    bat '''python -m venv venv
                           .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                           .\\venv\\Scripts\\uv python update-shell
                        '''
                    bat(label: 'Installing required Python version if not already installed', script: ".\\venv\\Scripts\\uv python find cpython-${pythonVersion} --quiet 2>nul || .\\venv\\Scripts\\uv python install cpython-${pythonVersion}")
                    findFiles(glob: packageType == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz').each{
                        def attempt = 0
                        retry(retryAmount){
                            attempt += 1
                            withEnv([(attempt == 1) ? 'UV_OFFLINE=1' : 'UV_OFFLINE=0']){
                                bat(
                                    label: "Testing with tox: ${(attempt == 1) ? 'Offline' : 'Online'}",
                                    script: ".\\venv\\Scripts\\uv run --frozen --only-group=tox-uv --isolated tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"
                                )
                            }
                        }
                    }
                }
            }
        } finally {
            bat "${tool(name: 'Default', type: 'git')} clean -dfx"
        }
    }
}

return [
    testLinuxPackage: testLinuxPackage,
    testMacOsPackage: testMacOsPackage,
    testWindowsPackage: testWindowsPackage
]