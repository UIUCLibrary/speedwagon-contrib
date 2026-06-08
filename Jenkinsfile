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



pipeline {
    agent none
    parameters {
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
        booleanParam(name: 'TEST_RUN_TOX', defaultValue: false, description: 'Run Tox Tests')
    }
    options {
        timeout(time: 1, unit: 'DAYS')
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
    }
}