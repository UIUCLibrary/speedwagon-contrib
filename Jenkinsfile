import groovy.json.JsonOutput
library(
        identifier: 'JenkinsPythonHelperLibrary@2024.12.0',
        retriever: modernSCM(
            [
                $class: 'GitSCMSource',
                remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git'
            ]
        )
    )

def getPypiConfig() {
    retry(conditions: [agent()], count: 3) {
        node(){
            configFileProvider([configFile(fileId: 'pypi_config', variable: 'CONFIG_FILE')]) {
                def config = readJSON( file: CONFIG_FILE)
                return config['deployment']['indexes']
            }
        }
    }
}


def createWindowUVConfig(){
    def scriptFile = "ci\\jenkins\\scripts\\new-uv-global-config.ps1"
    if(! fileExists(scriptFile)){
        checkout scm
    }
    return powershell(
        label: 'Setting up uv.toml config file',
        script: "& ${scriptFile} \$env:UV_INDEX_URL \$env:UV_EXTRA_INDEX_URL",
        returnStdout: true
    ).trim()
}

def createUnixUvConfig(){

    def scriptFile = 'ci/jenkins/scripts/create_uv_config.sh'
    if(! fileExists(scriptFile)){
        checkout scm
    }
    return sh(label: 'Setting up uv.toml config file', script: "sh ${scriptFile} " + '$UV_INDEX_URL $UV_EXTRA_INDEX_URL', returnStdout: true).trim()
}

def getSupportedPythonVersions(){
    try{
        configFileProvider([configFile(fileId: 'python_config', variable: 'CONFIG_FILE')]) {
            def config = readJSON( file: CONFIG_FILE)
            return config['supported_python_versions']
        }
    } catch (e){
        return ['3.10', '3.11', '3.12', '3.13', '3.14', '3.14t']
    }
}


pipeline {
    agent none
    parameters {
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
        booleanParam(name: 'TEST_RUN_TOX', defaultValue: false, description: 'Run Tox Tests')
        booleanParam(name: 'BUILD_PACKAGES', defaultValue: false, description: 'Build Python packages')
        booleanParam(name: 'TEST_PACKAGES', defaultValue: false, description: 'Test packages')
        booleanParam(name: 'INCLUDE_LINUX-ARM64', defaultValue: false, description: 'Include ARM architecture for Linux')
        booleanParam(name: 'INCLUDE_LINUX-X86_64', defaultValue: true, description: 'Include x86_64 architecture for Linux')
        booleanParam(name: 'INCLUDE_MACOS-ARM64', defaultValue: false, description: 'Include ARM(m1) architecture for Mac')
        booleanParam(name: 'INCLUDE_MACOS-X86_64', defaultValue: false, description: 'Include x86_64 architecture for Mac')
        booleanParam(name: 'INCLUDE_WINDOWS-X86_64', defaultValue: false, description: 'Include x86_64 architecture for Windows')
        booleanParam(name: 'DEPLOY_PYPI', defaultValue: false, description: 'Deploy to pypi')
        booleanParam(name: 'CREATE_GITHUB_RELEASE', defaultValue: false, description: 'Deploy to Github Release. Requires the current commit to be tagged. Note: This is experimental')
    }
    options {
        timeout(time: 1, unit: 'DAYS')
        preserveStashes()
    }
    stages {
        stage('Checks') {
            stages{
                stage('Code Quality'){
                    when{
                        equals expected: true, actual: params.RUN_CHECKS
                        beforeAgent true
                    }
                    agent {
                        docker{
                            image 'ghcr.io/astral-sh/uv:debian'
                            label 'docker && linux && x86_64'
                            args "--label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\" --mount source=python-tmp-uiucpreson_workflows,target=/tmp -e PIP_CACHE_DIR=/tmp/pipcache -e UV_TOOL_DIR=/tmp/uvtools -e UV_PYTHON_CACHE_DIR=/tmp/uvpython -e UV_CACHE_DIR=/tmp/uvcache --tmpfs /.config:exec --tmpfs /.local/share:exec --tmpfs /.local/bin:exec --tmpfs /.tree-sitter:exec --tmpfs /.cache/pylint"
                        }
                    }
                    stages{
                        stage('Test') {
                            stages{
                                stage('Configuring Testing Environment'){
                                    steps{
                                        sh(
                                            label: 'Create virtual environment',
                                            script: 'uv sync --active --locked --extra gui'
                                        )
                                        sh(
                                            label: 'Creating logging and report directories',
                                            script: '''mkdir -p logs
                                                       mkdir -p reports
                                                    '''
                                        )
                                    }
                                }
                                stage('Run Tests'){
                                    parallel {
                                        stage('Run PyTest Unit Tests'){
                                            steps{
                                                sh(script: 'PYTHONFAULTHANDLER=1 uv run coverage run --parallel-mode --source=speedwagon_contrib -m pytest --junitxml=./reports/tests/pytest/pytest-junit.xml --capture=no')
                                            }
                                            post {
                                                always {
                                                    junit(allowEmptyResults: true, testResults: 'reports/tests/pytest/pytest-junit.xml')
                                                }
                                            }
                                        }
                                        stage('Task Scanner'){
                                            steps{
                                                recordIssues(tools: [taskScanner(highTags: 'FIXME', includePattern: 'speedwagon_contrib/**/*.py', normalTags: 'TODO')])
                                            }
                                        }
                                        stage('Audit Requirement Freeze File'){
                                            steps{
                                                catchError(buildResult: 'UNSTABLE', message: 'uv audit', stageResult: 'UNSTABLE') {
                                                    sh 'uv audit'
                                                }
                                            }
                                        }
                                        stage('Ruff Static Analysis') {
                                            steps{
                                                catchError(buildResult: 'SUCCESS', message: 'Ruff found issues', stageResult: 'UNSTABLE') {
                                                    sh(
                                                     label: 'Running Ruff',
                                                     script: '''uv run ruff check --config=pyproject.toml -o reports/ruffoutput.txt --output-format pylint --exit-zero
                                                                uv run ruff check --config=pyproject.toml -o reports/ruffoutput.json --output-format json
                                                             '''
                                                     )
                                                }
                                            }
                                            post{
                                                always{
                                                    script{
                                                        if (fileExists('reports/ruffoutput.json')) {
                                                            echo( readFile('reports/ruffoutput.txt'))
                                                            recordIssues(tools: [pyLint(pattern: 'reports/ruffoutput.txt', name: 'Ruff')])
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        stage('MyPy'){
                                            steps{
                                                catchError(buildResult: 'SUCCESS', message: 'MyPy found issues', stageResult: 'UNSTABLE') {
                                                    tee('logs/mypy.log'){
                                                        sh(label: 'Running MyPy',
                                                           script: 'uv run mypy -p speedwagon_contrib --html-report reports/mypy/html'
                                                        )
                                                    }
                                                }
                                            }
                                            post {
                                                always {
                                                    recordIssues(tools: [myPy(pattern: 'logs/mypy.log')])
                                                    publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                                }
                                            }
                                        }
                                    }
                                    post{
                                        always{
                                            sh '''uv run coverage combine &&
                                                  uv run coverage xml -o reports/coverage.xml
                                                  uv run coverage html -d reports/coverage
                                               '''
                                            stash includes: 'reports/coverage.xml', name: 'COVERAGE_REPORT_DATA'
                                            recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                stage('Run Tox'){
                    when{
                        equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    parallel{
                        stage('Linux') {
                            when{
                                expression {return nodesByLabel('linux && docker').size() > 0}
                            }
                            environment{
                                PIP_CACHE_DIR='/tmp/pipcache'
                                UV_TOOL_DIR='/tmp/uvtools'
                                UV_PYTHON_CACHE_DIR='/tmp/uvpython'
                                UV_CACHE_DIR='/tmp/uvcache'
                            }
                            steps{
                                script{
                                    def envs = []
                                    node('docker && linux'){
                                        checkout scm
                                        try{
                                            docker.image('ghcr.io/astral-sh/uv:debian').inside(
                                                "--label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\"  --mount source=python-tmp-speedwagon-contrib,target=/tmp"
                                            ){
                                                withEnv(["UV_CONFIG_FILE=${createUnixUvConfig()}"]){
                                                    envs = sh(
                                                        label: 'Get tox environments',
                                                        script: 'uv run --isolated --only-group=tox --frozen --quiet tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\n')
                                                }
                                            }
                                        } finally{
                                            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                        }
                                    }
                                    parallel(
                                        envs.collectEntries{toxEnv ->
                                            def version = toxEnv.replaceAll(/py(\d)(\d+).*/, '$1.$2')
                                            [
                                                "Tox Environment: ${toxEnv}",
                                                {
                                                    node('docker && linux && x86_64'){
                                                        checkout scm
                                                        retry(3){
                                                            try{
                                                                docker.image('ghcr.io/astral-sh/uv:debian').inside(
                                                                    "--label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\" --mount source=python-tmp-speedwagon-contrib,target=/tmp --tmpfs /.local/share:exec --tmpfs /.local/bin:exec"
                                                                ){
                                                                    withEnv(["UV_CONFIG_FILE=${createUnixUvConfig()}"]){
                                                                        sh "uv python install cpython-${version}"
                                                                        sh( label: 'Running Tox',
                                                                            script: "uv run -p ${version} --frozen --only-group=tox-uv --isolated tox run --runner uv-venv-lock-runner -e ${toxEnv} --recreate"
                                                                            )
                                                                    }
                                                                }
                                                            } finally {
                                                                sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            }
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    )
                                }
                             }
                        }
                        stage('Windows') {
                            when{
                                expression {return nodesByLabel('windows && docker && x86').size() > 0}
                            }
                            environment{
                                 PIP_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\pipcache'
                                 UV_TOOL_DIR='C:\\Users\\ContainerUser\\Documents\\uvtools'
                                 UV_PYTHON_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\uvpython'
                                 UV_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\uvcache'
                            }
                            steps{
                                script{
                                    def envs = []
                                    node('docker && windows'){
                                        try{
                                            checkout scm
                                            docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python').inside(
                                                "--label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\" --mount source=uv_python_cache_dir,target=${env.UV_PYTHON_CACHE_DIR}"
                                            ){
                                                withEnv(["UV_CONFIG_FILE=${createWindowUVConfig()}"]){
                                                    bat(script: 'python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv')
                                                    envs = bat(
                                                        label: 'Get tox environments',
                                                        script: '@.\\venv\\Scripts\\uv run --isolated --only-group tox --frozen --quiet tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\r\n')
                                                }
                                            }
                                        } finally{
                                            bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                        }
                                    }
                                    parallel(
                                        envs.collectEntries{toxEnv ->
                                            def version = toxEnv.replaceAll(/py(\d)(\d+).*/, '$1.$2')
                                            [
                                                "Tox Environment: ${toxEnv}",
                                                {
                                                    node('docker && windows'){
                                                        try{
                                                            checkout scm
                                                            docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python').inside(
                                                                  " --label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\""
                                                                + " --mount type=volume,source=uv_python_cache_dir,target=${env.UV_PYTHON_CACHE_DIR}"
                                                                + " --mount type=volume,source=pipcache,target=${env.PIP_CACHE_DIR}"
                                                                + " --mount type=volume,source=uv_cache_dir,target=${env.UV_CACHE_DIR}"
                                                            ){
                                                                retry(3){
                                                                    try{
                                                                        withEnv([
                                                                            "TOX_UV_PATH=${env.WORKSPACE}\\venv\\Scripts\\uv.exe",
                                                                            "UV_CONFIG_FILE=${createWindowUVConfig()}"
                                                                        ]){
                                                                            powershell(script: """python -m venv venv
                                                                                                  venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                                  venv\\Scripts\\uv python update-shell
                                                                                                  venv\\Scripts\\uv python install cpython-${version}
                                                                                              """
                                                                                )
                                                                            bat(label: 'Running Tox',
                                                                                script: "venv\\Scripts\\uv run -p ${version} --frozen --only-group=tox-uv --isolated tox run --runner uv-venv-lock-runner -e ${toxEnv} --recreate"
                                                                            )
                                                                        }
                                                                    } catch(e) {
                                                                        cleanWs(
                                                                            patterns: [
                                                                                [pattern: 'venv', type: 'INCLUDE'],
                                                                                [pattern: '.tox', type: 'INCLUDE'],
                                                                            ]
                                                                        )
                                                                        throw e
                                                                    }
                                                                }
                                                            }
                                                        } finally{
                                                            bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
        stage('Packaging'){
            when{
                equals expected: true, actual: params.BUILD_PACKAGES
                beforeAgent true
            }
            stages{
                stage('Python Packages'){
                    stages{
                        stage('Packaging sdist and wheel'){
                            agent {
                                docker{
                                    image 'ghcr.io/astral-sh/uv:debian'
                                    label 'linux && docker'
                                    args '--mount source=python-tmp-speedwagon-contrib,target=/tmp'
                                  }
                            }
                            environment{
                                PIP_CACHE_DIR='/tmp/pipcache'
                                UV_CACHE_DIR='/tmp/uvcache'
                            }
                            options {
                                retry(2)
                            }
                            steps{
                                timeout(5){
                                    sh(
                                        label: 'Package',
                                        script: 'uv build'
                                    )
                                }
                            }
                            post{
                                always{
                                    stash includes: 'dist/*.whl,dist/*.tar.gz,dist/*.zip', name: 'PYTHON_PACKAGES'
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        patterns: [
                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                            [pattern: 'dist/', type: 'INCLUDE']
                                        ]
                                    )
                                }
                            }
                        }
                        stage('Testing Packages'){
                            when{
                                equals expected: true, actual: params.TEST_PACKAGES
                            }
                            stages{
                                stage('Packages Test Matrix'){
                                    steps{
                                        customMatrix(
                                            axes: [
                                                [
                                                    name: 'PYTHON_VERSION',
                                                    values: getSupportedPythonVersions()
                                                ],
                                                [
                                                    name: 'OS',
                                                    values: ['linux','macos', 'windows']
                                                ],
                                                [
                                                    name: 'ARCHITECTURE',
                                                    values: ['x86_64', 'arm64']
                                                ],
                                                [
                                                    name: 'PACKAGE_TYPE',
                                                    values: ['wheel', 'sdist'],
                                                ]
                                            ],
                                            excludes: [
                                                [
                                                    [
                                                        name: 'OS',
                                                        values: 'windows'
                                                    ],
                                                    [
                                                        name: 'ARCHITECTURE',
                                                        values: 'arm64',
                                                    ]
                                                ]
                                            ],
                                            when: {entry -> "INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase() && params["INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()]},
                                            stages: [
                                                { entry ->
                                                    stage('Test Package') {
                                                        node("${entry.OS} && ${entry.ARCHITECTURE} ${['linux', 'windows'].contains(entry.OS) ? '&& docker': ''}"){
                                                            try{
                                                                checkout scm
                                                                unstash 'PYTHON_PACKAGES'
                                                                if(['linux', 'windows'].contains(entry.OS) && params.containsKey("INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()]){
                                                                    docker.image(isUnix() ? 'ghcr.io/astral-sh/uv:debian': 'python')
                                                                        .inside(
                                                                            "--label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\" " +
                                                                            (
                                                                                isUnix() ?
                                                                                    '--mount source=python-tmp-speedwagon-contrib,target=/tmp --tmpfs /.local/share:exec --tmpfs /.local/bin:exec'
                                                                                :
                                                                                    '--mount type=volume,source=uv_python_cache_dir,target=c:\\Users\\ContainerUser\\Documents\\cache\\uvpython'
                                                                                    + ' --mount type=volume,source=pipcache,target=c:\\Users\\ContainerUser\\Documents\\cache\\pipcache'
                                                                                    + ' --mount type=volume,source=uv_cache_dir,target=c:\\Users\\ContainerUser\\Documents\\cache\\uvcache'
                                                                            )
                                                                        ){
                                                                         if(isUnix()){
                                                                            withEnv([
                                                                                'PIP_CACHE_DIR=/tmp/pipcache',
                                                                                'UV_TOOL_DIR=/tmp/uvtools',
                                                                                'UV_PYTHON_CACHE_DIR=/tmp/uvpython',
                                                                                'UV_CACHE_DIR=/tmp/uvcache',
                                                                                "UV_CONFIG_FILE=${createUnixUvConfig()}"
                                                                            ]){
                                                                                sh "uv python install cpython-${entry.PYTHON_VERSION}"
                                                                                def attempt = 0
                                                                                retry(2){
                                                                                    attempt += 1
                                                                                    withEnv([(attempt == 1) ? 'UV_OFFLINE=1' : 'UV_OFFLINE=0']){
                                                                                        sh(
                                                                                            label: "Testing with tox: ${(attempt == 1) ? 'Offline' : 'Online'}",
                                                                                            script: "uv run --only-group=tox-uv --isolated --frozen tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}"
                                                                                        )
                                                                                    }
                                                                                }
                                                                            }
                                                                         } else {
                                                                            withEnv([
                                                                                'PIP_CACHE_DIR=c:\\Users\\ContainerUser\\Documents\\cache\\pipcache',
                                                                                'UV_TOOL_DIR=c:\\Users\\ContainerUser\\Documents\\uvtools',
                                                                                'UV_PYTHON_CACHE_DIR=c:\\Users\\ContainerUser\\Documents\\cache\\uvpython',
                                                                                'UV_CACHE_DIR=c:\\Users\\ContainerUser\\Documents\\cache\\uvcache',
                                                                                'UV_LINK_MODE=copy',
                                                                                "TOX_UV_PATH=${env.WORKSPACE}\\venv\\Scripts\\uv.exe",
                                                                                "UV_CONFIG_FILE=${createWindowUVConfig()}"
                                                                            ]){
                                                                                bat """python -m venv venv
                                                                                       .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                       .\\venv\\Scripts\\uv python update-shell
                                                                                       .\\venv\\Scripts\\uv python install cpython-${entry.PYTHON_VERSION}
                                                                                    """
                                                                                def attempt = 0
                                                                                retry(2){
                                                                                    attempt += 1
                                                                                    withEnv([(attempt == 1) ? 'UV_OFFLINE=1' : 'UV_OFFLINE=0']){
                                                                                        bat(
                                                                                            label: "Testing with tox: ${(attempt == 1) ? 'Offline' : 'Online'}",
                                                                                            script: ".\\venv\\Scripts\\uv run --frozen --only-group=tox-uv --isolated tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}"
                                                                                        )
                                                                                    }
                                                                                }
                                                                            }
                                                                         }
                                                                    }
                                                                } else {
                                                                    if(isUnix()){
                                                                        withEnv([
                                                                            "TOX_UV_PATH=${env.WORKSPACE}/venv/bin/uv",
                                                                            "UV_CONFIG_FILE=${createUnixUvConfig()}"
                                                                        ]){
                                                                            sh """python3 -m venv venv
                                                                                  ./venv/bin/pip install --disable-pip-version-check uv
                                                                                  ./venv/bin/uv python install cpython-${entry.PYTHON_VERSION}
                                                                               """
                                                                            def attempt = 0
                                                                            retry(2){
                                                                                attempt += 1
                                                                                withEnv([(attempt == 1) ? 'UV_OFFLINE=1' : 'UV_OFFLINE=0']){
                                                                                    sh(
                                                                                        label: "Testing with tox: ${(attempt == 1) ? 'Offline' : 'Online'}",
                                                                                        script: "./venv/bin/uv run --only-group=tox-uv --isolated --frozen tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}"
                                                                                    )
                                                                                }
                                                                            }
                                                                        }
                                                                    } else {
                                                                        withEnv([
                                                                            "TOX_UV_PATH=${env.WORKSPACE}\\venv\\Scripts\\uv.exe",
                                                                            "UV_CONFIG_FILE=${createWindowUVConfig()}"
                                                                        ]){
                                                                            def attempt = 0
                                                                            retry(2){
                                                                                attempt += 1
                                                                                withEnv([(attempt == 1) ? 'UV_OFFLINE=1' : 'UV_OFFLINE=0']){
                                                                                    bat(
                                                                                        label: "Testing with tox: ${(attempt == 1) ? 'Offline' : 'Online'}",
                                                                                        script: """python -m venv venv
                                                                                                   .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                                   .\\venv\\Scripts\\uv python install cpython-${entry.PYTHON_VERSION}
                                                                                                   .\\venv\\Scripts\\uv run --only-group=tox-uv --isolated --frozen tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                                """
                                                                                    )
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            } finally{
                                                                if(isUnix()){
                                                                    sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                                } else {
                                                                    bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            ]
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        stage('Deploy'){
            when{
                anyOf{
                    equals expected: true, actual: params.DEPLOY_PYPI
                    equals expected: true, actual: params.CREATE_GITHUB_RELEASE
                }
            }
            parallel{
                stage('Deploy to pypi') {
                    environment{
                        PIP_CACHE_DIR='/tmp/pipcache'
                        UV_TOOL_DIR='/tmp/uvtools'
                        UV_PYTHON_CACHE_DIR='/tmp/uvpython'
                        UV_CACHE_DIR='/tmp/uvcache'
                    }
                    agent {
                        docker{
                            image 'ghcr.io/astral-sh/uv:debian'
                            label 'docker && linux'
                            args "--label=purpose=ci --label \"JOB_NAME=\$JOB_NAME\" --label \"absoluteUrl=${currentBuild.absoluteUrl}\" --label \"BUILD_NUMBER=${currentBuild.number}\" --mount source=uv_python_cache_dir,target=/tmp/uvpython"
                        }
                    }
                    when{
                        allOf{
                            equals expected: true, actual: params.DEPLOY_PYPI
                            equals expected: true, actual: params.BUILD_PACKAGES
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                        retry(3)
                    }
                    input {
                        message 'Upload to pypi server?'
                        parameters {
                            choice(
                                choices: getPypiConfig(),
                                description: 'Url to the pypi index to upload python packages.',
                                name: 'SERVER_URL'
                            )
                        }
                    }
                    steps{
                        unstash 'PYTHON_PACKAGES'
                        withEnv(
                            [
                                "UV_PUBLISH_URL=${SERVER_URL}",
                            ]
                        ){
                            withCredentials(
                                [
                                    usernamePassword(
                                        credentialsId: 'jenkins-nexus',
                                        passwordVariable: 'UV_PUBLISH_PASSWORD',
                                        usernameVariable: 'UV_PUBLISH_USERNAME'
                                    )
                                ]
                            ){
                                sh(
                                    label: 'Uploading to pypi',
                                    script: 'uv publish dist/*'
                                )
                            }
                        }
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE']
                                    ]
                            )
                        }
                    }
                }
                stage('GitHub Release'){
                    agent any
                    when{
                        beforeInput true
                        beforeAgent true
                        beforeOptions true
                        allOf{
                          equals expected: true, actual: params.CREATE_GITHUB_RELEASE
                          tag '*'
                        }
                    }
                    input {
                        message 'Create GitHub Release'
                        id 'GITHUB_DEPLOYMENT'
                        parameters {
                            credentials(
                                credentialType: 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl',
                                description: 'GitHub credential Id',
                                name: 'GITHUB_CREDENTIALS_ID',
                                required: true
                            )
                        }
                    }
                    environment{
                        GITHUB_REPO='UIUCLibrary/speedwagon-contrib'
                    }
                    options{
                        lock("${env.JOB_NAME}")
                    }
                    steps{
                        script {
                            def projectMetadata = readTOML( file: 'pyproject.toml')['project']
                            withCredentials([string(credentialsId: GITHUB_CREDENTIALS_ID, variable: 'GITHUB_TOKEN')]) {
                                def requestBody = JsonOutput.toJson([
                                    tag_name: env.BRANCH_NAME,
                                    name: "Version ${projectMetadata.version}",
                                    generate_release_notes: false,
                                    draft: false,
                                    prerelease: false
                                ])
                                def createReleaseResponse = httpRequest(
                                    httpMode: 'POST',
                                    contentType: 'APPLICATION_JSON',
                                    url: "https://api.github.com/repos/UIUCLibrary/speedwagon-contrib/releases",
                                    customHeaders: [
                                        [name: 'Authorization', value: "token ${GITHUB_TOKEN}"]
                                    ],
                                    requestBody: requestBody,
                                    validResponseCodes: '201' // Expect a 201 Created status code
                                    )
                                if (params.BUILD_PACKAGES){
                                    unstash 'PYTHON_PACKAGES'
                                    def releaseData = readJSON text: createReleaseResponse.content
                                    findFiles(glob: 'dist/*').each{
                                        def uploadResponse = httpRequest(
                                            url: "${releaseData.upload_url.replace('{?name,label}', '')}?name=${it.name}",
                                            httpMode: 'POST',
                                            uploadFile: it.path,
                                            customHeaders: [[name: 'Authorization', value: "token ${GITHUB_TOKEN}"]],
                                            wrapAsMultipart: false
                                        )
                                        if (uploadResponse.status >= 200 && uploadResponse.status < 300) {
                                            echo "File uploaded successfully to GitHub release."
                                        } else {
                                            error "Failed to upload file: ${uploadResponse.status} - ${uploadResponse.content}"
                                        }
                                    }
                                }
                            }
                        }
                    }
                    post{
                        cleanup{
                            script{
                                if(isUnix()){
                                    sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                } else {
                                    bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}