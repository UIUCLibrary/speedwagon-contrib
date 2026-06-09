"""Checks that files are consistent with DS conventions."""

import os
import sys
from datetime import date
from typing import Tuple, TextIO, Dict


def main() -> None:
    print('This program checks that files are consistent with DS conventions for archival and cataloged collections:'
          '\n\t- All files are either .tifs or .jp2s'
          '\n\t- File names do not contain any spaces'
          '\n\t- File names contain a hyphen'
          '\n\t- File names contain the appropriate level of padding (3 or 8 digits)'
          '\n\t- File names are sequential'
          '\n\t- All files that are in the access directory are also present in the corresponding preservation directory,'
          ' and vice versa.')

    directory, file_type = get_inputs()
    access_directory, directories, pres_directory, report_location = get_directories(directory)

    run_file_type_check(file_type)
    with open(report_location, 'a') as outfile:
        make_report_header(directories, outfile)

        for directory in directories:
            outfile.write(f'\nREPORT FOR {directory}')
            error_list = check_filenames(directory, file_type)
            error_list.sort()
            for error in error_list:
                outfile.write(f'\n{error}')

        access_list_trimmed, pres_list_trimmed = make_file_number_lists(access_directory, pres_directory)
        matching_error_list = validate_files(access_list_trimmed, pres_list_trimmed)

        for error in matching_error_list:
            outfile.write(f'\n{error}')

        total_errors = len(error_list) + len(matching_error_list)

        print(f'{total_errors} discrepancies were discovered. Detailed report saved to {report_location}')


def get_inputs() -> Tuple[str, str]:
    directory = input('\nPlease enter the directory (e.g. /Volumes/digitize/project/QAqueue/session) in which your '
                      'files are stored: ')
    file_type = input('\nEnter file type ["A" for Archival or "C" for Cataloged]: ')
    return directory, file_type


def get_directories(directory: str) -> Tuple[str, list[str], str, str]:
    day = str(date.today())
    report_title = f'{day}_file_checker_report.txt'

    directories = []

    report_location = ''
    access_directory = os.path.join(directory, 'access')
    pres_directory = os.path.join(directory, 'preservation')
    if sys.platform == 'win32':
        desktop_path = os.path.expanduser('~\\Desktop')
        report_location = f'{desktop_path}\\{report_title}'
    if sys.platform == 'darwin':
        desktop_path = os.path.expanduser('~/Desktop')
        report_location = f'{desktop_path}/{report_title}'

    if not os.path.isdir(access_directory) or not os.path.isdir(pres_directory):
        print(f'{access_directory} and/or {pres_directory} does not exist. '
              f'\nThis program is ending. Please run it again with correct input.')
        exit()
    directories.append(access_directory)
    directories.append(pres_directory)
    return access_directory, directories, pres_directory, report_location


def make_report_header(directories: list[str], outfile: TextIO) -> None:
    outfile.write('\nREPORT FOR THE FOLLOWING DIRECTORIES:')
    for directory in directories:
        outfile.write(f'\n\t{directory}')
    outfile.write('\n')


def run_file_type_check(file_type: str) -> str:
    while file_type != 'Archival' and file_type != 'Cataloged':
        print(f'ERROR: Invalid file type. You entered {file_type}.'
              f'\nThis program is ending. Please run it again with correct input.')
        exit()
    return file_type


def check_filenames(directory: str, file_type: str) -> list[str]:
    error_list = []

    file_list = os.listdir(directory)
    file_tree, hyphen_errors = create_file_tree(file_list)
    for file in file_list:
        basic_errors = get_basic_errors(file)
        if basic_errors:
            error_list.extend(basic_errors)
    for prefix, file_number in file_tree.items():
        file_errors = get_prefix_errors(prefix, file_number, file_type)
        if file_errors:
            error_list.extend(file_errors)
    sequence_errors = check_sequential(file_tree)
    if sequence_errors:
        error_list.extend(sequence_errors)
    if hyphen_errors:
        error_list.extend(hyphen_errors)

    return error_list


def create_file_tree(file_list: list[str]) -> Tuple[dict[str, list[str]], list[str]]:
    file_tree = {}
    hyphen_errors = []
    for file in file_list:
        filename = file.split('.')[0]
        if '-' in filename:
            prefix, file_number = filename.split('-')
            if str(prefix) not in file_tree:
                file_tree[str(prefix)] = [file_number]
            else:
                file_tree[prefix].append(file_number)
        else:
            hyphen_errors.append(f'{file} does not adhere to the correct naming '
                               f'conventions (missing hyphen).')
    return file_tree, hyphen_errors


def get_basic_errors(file: str) -> list[str]:
    basic_errors = []
    prefix, suffix = file.split('.')
    if suffix != 'tif' and suffix != 'tiff' and suffix != 'jp2':
        basic_errors.append(f'{file} is not a tif or jp2 file.')
    if ' ' in prefix:
        basic_errors.append(
            f'{file} does not adhere to the correct naming convention (no spaces allowed).')
    return basic_errors


def get_prefix_errors(prefix: str, file_number: list[str], file_type: str ) -> list[str]:
    prefix_errors = []
    if file_type == 'Archival':
        archival_errors = check_archival_file(file_number, prefix)
        if archival_errors:
            prefix_errors.extend(archival_errors)

    if file_type == 'Cataloged':
        cat_errors = check_cat_errors(file_number, prefix)
        if cat_errors:
            prefix_errors.extend(cat_errors)

    return prefix_errors


def check_cat_errors(file_number: list[str], prefix: str) -> list[str]:
    cat_errors = []
    for number in file_number:
        if len(number) != 8:
            cat_errors.append(
                f'{prefix}-{number} does not adhere to the correct naming convention (8 '
                f'digits after hyphen).')
    return cat_errors


def check_archival_file(file_number: list[str], prefix: str) -> list[str]:
    archival_errors = []
    for number in file_number:
        if len(number) != 3:
            archival_errors.append(
                f'{prefix}-{number} does not adhere to the correct naming convention (3 '
                f'digits after hyphen).')
        prefix_parts = prefix.split('_')
        if len(prefix_parts) != 4:
            archival_errors.append(
                f'{prefix}-{number} does not adhere to the correct naming convention (collection_box_folder_item-pad)')
        for position_counter, part in enumerate(prefix_parts):
            if position_counter != 0 and len(part) != 3:
                archival_errors.append(f'{prefix}-{number} does not adhere to the correct naming '
                                   f'convention (3 digits for box number, folder number, and item number).')
    return archival_errors


def check_sequential(file_tree: Dict[str, list[str]]) -> list[str]:
    sequence_errors = []
    for prefix in file_tree:
        prefix_sequence_errors = prefix_sequential(file_tree, prefix)
        if prefix_sequence_errors:
            sequence_errors.extend(prefix_sequence_errors)
    return sequence_errors


def prefix_sequential(file_tree: Dict[str, list[str]], prefix: str) -> list[str]:
    file_numbers = file_tree[prefix]
    numbers_only_list = []
    prefix_sequence_errors = []
    for file_number in file_numbers:
        stripped_file = str(file_number).lstrip('0')
        if stripped_file != '':
            numbers_only_list.append(int(stripped_file))
    numbers_only_list.sort()
    for position_counter, file in enumerate(numbers_only_list):
        if position_counter != 0:
            if int(file) != (int(position_counter) + 1):
                prefix_sequence_errors.append(
                    f'Files with the prefix {prefix} ending in {position_counter} and '
                    f'{file} are not sequential.')
        else:
            pass
    return prefix_sequence_errors


def validate_files(access_list_trimmed, pres_list_trimmed):
    matching_error_list = []

    pres_missing = list(filter(lambda x: x not in pres_list_trimmed, access_list_trimmed))
    access_missing = list(filter(lambda x: x not in access_list_trimmed, pres_list_trimmed))

    if pres_missing:
        matching_error_list.append(f'The following files are present in the access directory, but are not present in '
              f'the preservation directory: {pres_missing}')

    if access_missing:
        matching_error_list.append(f'The following files are present in the preservation directory, but are not present '
              f'in the access directory: {access_missing}')

    return matching_error_list


def make_file_number_lists(access_directory: str, pres_directory: str) -> Tuple[list[str], list[str]]:
    access_list = os.listdir(access_directory)
    access_list_trimmed = []
    for file in access_list:
        if file.startswith('.'):
            access_list_trimmed.append(file)
        else:
            trimmed_file = file.split('.')[0]
            access_list_trimmed.append(trimmed_file)
    pres_list = os.listdir(pres_directory)
    pres_list_trimmed = []
    for file in pres_list:
        if file.startswith('.'):
            pres_list_trimmed.append(file)
        else:
            trimmed_file = file.split('.')[0]
            pres_list_trimmed.append(trimmed_file)
    return access_list_trimmed, pres_list_trimmed


if __name__ == '__main__':
    main()
