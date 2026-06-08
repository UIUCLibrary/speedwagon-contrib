import speedwagon

from speedwagon_contrib.file_checker.speedwagon_workflow import FileCheckerWorkflow

@speedwagon.hookimpl
def registered_workflows():
    return {"File Checker": FileCheckerWorkflow}
