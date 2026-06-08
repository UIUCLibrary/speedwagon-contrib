pipeline {
    agent none
    parameters {
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
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
            }
        }
    }
}