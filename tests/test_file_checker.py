import pytest

from speedwagon_contrib.file_checker import file_checker


def test_make_report_header(tmp_path):
    output = tmp_path / "output"
    output.touch()

    a = tmp_path / "src" / "a"
    a.mkdir(parents=True)
    b = tmp_path / "src" / "b"
    b.mkdir(parents=True)
    with output.open("w") as f:
        file_checker.make_report_header([a, b], f)
    with output.open("r") as f:
        content = f.read()
        assert content.startswith('\nREPORT FOR THE FOLLOWING DIRECTORIES')
        assert content.split('\n')[2] == f'\t{a}'
        assert content.split('\n')[3] == f'\t{b}'


def test_check_filenames_check_empty_dir(tmp_path):
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    assert file_checker.check_filenames(empty_dir, 'Cataloged') == []


def test_check_filenames_check_not_tiff(tmp_path):
    csv = tmp_path / "9999-00000001.csv"
    csv.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Cataloged')) == 1


def test_check_filenames_check_whitespace(tmp_path):
    csv = tmp_path / " 9999-00000001.tiff"
    csv.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Cataloged')) == 1


def test_check_filenames_no_errors(tmp_path):
    csv = tmp_path / "9999-00000001.tiff"
    csv.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Cataloged')) == 0


def test_check_filenames_no_errors_arc(tmp_path):
    csv = tmp_path / "9999_001_001_001-001.tiff"
    csv.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Archival')) == 0


def test_check_filenames_suffix_cat(tmp_path):
    cat = tmp_path / "9999-0000001.tiff"
    cat.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Cataloged')) == 1


def test_check_filenames_suffix_arc(tmp_path):
    arc = tmp_path / "9999_001_001_001-01.tiff"
    arc.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Archival')) == 1


def test_check_filenames_no_hyphen(tmp_path):
    file = tmp_path / "0000001.tiff"
    file.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Cataloged')) == 1


def test_check_filenames_no_item_number_arc(tmp_path):
    file = tmp_path / "9999_001_001-001.tiff"
    file.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Archival')) == 1


def test_check_filenames_two_digit_item_number_arc(tmp_path):
    file = tmp_path / "9999_001_001_01-001.tiff"
    file.touch()
    assert len(file_checker.check_filenames(tmp_path, 'Archival')) == 1


def test_not_sequential(tmp_path):
    file_tree = {'999': ['001', '003']}
    assert len(file_checker.check_sequential(file_tree)) == 1


def test_sequential(tmp_path):
    file_tree = {'999': ['001', '002']}
    assert len(file_checker.check_sequential(file_tree)) == 0


def test_path_not_exists(tmp_path):
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    with pytest.raises(SystemExit) as e:
        file_checker.get_directories(empty_dir)
    assert e.type == SystemExit


def test_invalid_file_type(tmp_path):
    with pytest.raises(SystemExit) as e:
        file_checker.run_file_type_check('b')
    assert e.type == SystemExit

def test_valid_file_type(tmp_path):
    assert file_checker.run_file_type_check('Cataloged') == 'Cataloged'


def test_missing_access_file(tmp_path):
    output = tmp_path / "output"
    output.touch()
    pres_list_trimmed = [1, 2, 3]
    access_list_trimmed = [1, 2]

    assert len(file_checker.validate_files(access_list_trimmed, pres_list_trimmed)) == 1


def test_missing_files(tmp_path):
    output = tmp_path / "output"
    output.touch()
    pres_list_trimmed = [1, 2, 4]
    access_list_trimmed = [2, 3, 4, 5]

    assert len(file_checker.validate_files(access_list_trimmed, pres_list_trimmed)) == 2


def test_make_file_number_lists(tmp_path):
    access_dir = tmp_path / "access_dir"
    access_dir.mkdir()
    access_file = access_dir / "access_file.tif"
    access_file.touch()
    access_file_2 = access_dir / "access_file_2.tif"
    access_file_2.touch()

    pres_dir = tmp_path / "pres_dir"
    pres_dir.mkdir()
    pres_file = pres_dir / "pres_file.tif"
    pres_file.touch()
    pres_file_2 = pres_dir / "pres_file_2.tif"
    pres_file_2.touch()

    access_list_trimmed, pres_list_trimmed = file_checker.make_file_number_lists(access_dir, pres_dir)

    assert access_list_trimmed == ['access_file', 'access_file_2']
    assert pres_list_trimmed == ['pres_file', 'pres_file_2']
