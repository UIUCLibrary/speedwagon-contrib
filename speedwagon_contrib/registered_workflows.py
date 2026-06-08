from typing import Dict, Any, Type

import speedwagon

from speedwagon_contrib.file_checker.speedwagon_workflow import FileCheckerWorkflow

@speedwagon.hookimpl
def registered_workflows() -> Dict[str, Type[speedwagon.Workflow[Any]]]:
    return {"File Checker": FileCheckerWorkflow}
