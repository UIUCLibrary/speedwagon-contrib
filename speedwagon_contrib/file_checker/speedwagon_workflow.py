import os.path
from typing import List, Mapping, Any, Optional, TypedDict, Dict, Union

import speedwagon
from speedwagon import workflow
from speedwagon.tasks import Result, TaskBuilder
from datetime import date

from . import file_checker


UserArgs = TypedDict("UserArgs", {"Report File": str, "Input Directory": str, "File Type": str})
JobArgs = TypedDict(
    "JobArgs",
    {
        "access_directory": str,
        "pres_directory": str,
        "directories": list[str],
        "report_location": str,
        "file_type": str,
    }
)
ResultArgs = TypedDict("ResultArgs", {"errors": List[str]})

def contains_required_folders(value: Union[str, None], expected_folder: str) -> bool:
    if value is None:
        return False
    return os.path.exists(os.path.join(value, expected_folder))


def _get_default_report_location() -> str:
    day = str(date.today())
    report_title = f"{day}_file_checker_report.txt"
    desktop_path = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
    return os.path.join(desktop_path, report_title)


def is_valid_location_for_log(value: str) -> bool:
    dir_path = os.path.dirname(value)
    return os.path.exists(dir_path)


class FileCheckerWorkflow(speedwagon.Workflow[UserArgs]):
    name = "File Checker"
    description = """This program checks that files are consistent with DS conventions for archival and cataloged collections:
    - All files are either .tifs or .jp2s
    - File names do not contain any spaces
    - File names contain a hyphen
    - File names contain the appropriate level of padding (3 or 8 digits)
    - File names are sequential
    - All files that are in the access directory are also present in the corresponding preservation directory,
      and vice versa.
      
Settings:

    Input Directory: Path to validate.
    File Type: Either archival or cataloged
    Report File: Location to save report. By default, this will be saved to the desktop with a name in the format YYYY-MM-DD_file_checker_report.txt
    
Created by Anna Smith
"""

    def job_options(self) -> List[workflow.AbsOutputOptionDataType]:
        input_directory = speedwagon.workflow.DirectorySelect(
            "Input Directory", required=True
        )
        input_directory.add_validation(
            speedwagon.validators.CustomValidation(
                query=lambda value, _: (
                        value is not None and
                        (os.path.exists(value) and os.path.isdir(value))
                ),
                failure_message_function=lambda *_: "Not a valid directory.",
            )
        )

        input_directory.add_validation(
            speedwagon.validators.CustomValidation(
                query=lambda value, _: contains_required_folders(
                    value, expected_folder="access"
                ),
                failure_message_function=lambda *_: (
                    "Does not contain required access folder."
                ),
            ),
            condition=lambda candidate, _: os.path.exists(candidate),
        )

        input_directory.add_validation(
            speedwagon.validators.CustomValidation(
                query=lambda value, _: contains_required_folders(
                    value, expected_folder="preservation"
                ),
                failure_message_function=lambda *_: (
                    "Does not contain required preservation folder."
                ),
            ),
            condition=lambda candidate, _: os.path.exists(candidate),
        )

        file_type = workflow.ChoiceSelection("File Type", required=True)
        file_type.add_selection("Archival")
        file_type.add_selection("Cataloged")
        report_file = workflow.FileSave("Report File", required=True)
        report_file.filter = "Text files (*.txt)"
        report_file.value = _get_default_report_location()
        report_file.add_validation(
            speedwagon.validators.CustomValidation(
                query=lambda value, _: value is not None and
                                       is_valid_location_for_log(value),
                failure_message_function=lambda value: (
                    f"invalid file location {os.path.dirname(value) if value else ''}"
                ),
            )
        )
        return [
            input_directory, file_type,
            report_file
        ]

    def discover_task_metadata(
        self,
        initial_results: List[Result],
        additional_data: Mapping[str, Any],
        user_args: UserArgs,
    ) -> List[JobArgs]:
        access_directory, directories, pres_directory, _ = file_checker.get_directories(
            user_args["Input Directory"]
        )
        return [
            {
                "access_directory": access_directory,
                "directories": directories,
                "pres_directory": pres_directory,
                "report_location": user_args["Report File"],
                "file_type": user_args["File Type"],
            }
        ]

    def generate_report(cls, results: List[Result], user_args: UserArgs) -> Optional[str]:
        total_errors = len(results[0].data["errors"])
        report_location = user_args["Report File"]

        return (
            f"{total_errors} discrepancies were discovered. "
            f"Detailed report saved to {report_location}"
        )

    def create_new_task(self, task_builder: TaskBuilder, job_args: JobArgs) -> None:
        task_builder.add_subtask(
            check_files(
                access_directory=job_args["access_directory"],
                pres_directory=job_args["pres_directory"],
                directories=job_args["directories"],
                report_location=job_args["report_location"],
                file_type=job_args["file_type"],
            )
        )


@speedwagon.tasks.workflow_task(description="Checking files")
def check_files(
    access_directory: str,
    directories: List[str],
    pres_directory: str,
    report_location: str,
    file_type: str,
) -> Dict[str, str]:
    with open(report_location, "a") as outfile:
        file_checker.make_report_header(directories, outfile)

        for directory in directories:
            outfile.write(f"\nREPORT FOR {directory}")
            error_list = file_checker.check_filenames(directory, file_type)
            for error in error_list:
                outfile.write(f"\n{error}")

        access_list_trimmed, pres_list_trimmed = file_checker.make_file_number_lists(
            access_directory, pres_directory
        )
        matching_error_list = file_checker.validate_files(
            access_list_trimmed, pres_list_trimmed
        )

        for error in matching_error_list:
            outfile.write(f"\n{error}")
        return {
            "errors": error_list + matching_error_list,
            "report location": report_location,
        }
