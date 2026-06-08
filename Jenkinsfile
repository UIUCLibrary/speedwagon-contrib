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
                    steps {
                        echo 'Running Jenkins Pipeline'
                    }
                }
            }
        }
    }
}