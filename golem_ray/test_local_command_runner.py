import os, shutil
import pytest

from pathlib import Path

from click import ClickException
import subprocess
from getpass import getuser

from local_head_command_runner import LocalHeadCommandRunner, InvalidLocalHeadArg

#   Command, expected output, additional arguments
test_cases_test_run = [
    ('whoami', getuser() + '\n', {'with_output': True}),
    ('echo foo', 'foo\n', {'with_output': True}),
    ('echo "$USER"', getuser() + '\n', {'with_output': True}),
    ('echo "$BAR"', '\n', {'with_output': True}),
    ('echo "$BAR"', 'baz\n', {'environment_variables': {'BAR': 'baz'}, 'with_output': True}),
    ('whoami', 0, {'with_output': False}),
]


@pytest.mark.parametrize('cmd, output, kwargs', test_cases_test_run)
def test_run(cmd, output, kwargs):
    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    assert runner.run(cmd, **kwargs) == output


@pytest.mark.parametrize('kwargs', (
        {'shutdown_after_run': True, 'with_output': True},
        {'port_forward': [(7878, 7979)], 'with_output': True},
        {'ssh_options_override_ssh_key': 'FooBar', 'with_output': True},
        {'run_env': 'FooBar', 'with_output': True},
        {'timeout': 121, 'with_output': True},
))
def test_invalid_kwargs(kwargs):
    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    with pytest.raises(InvalidLocalHeadArg):
        runner.run('echo foo', **kwargs)


test_cases_test_failing_command = [
    ('FooBar', {'exit_on_fail': True, 'with_output': True}),
]


@pytest.mark.parametrize('cmd, kwargs', test_cases_test_failing_command)
def test_failing_command(cmd, kwargs):
    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    with pytest.raises(ClickException):
        runner.run(cmd, **kwargs)


def _prep_file(parent: Path, file_name: str, content: str) -> Path:
    file_path = parent / file_name
    file_path.touch()
    file_path.write_text(content)
    return file_path


def _prep_dir(parent: Path, dir_name: str) -> Path:
    dir_path = parent / dir_name
    dir_path.mkdir()
    return dir_path


def _prepare_testing_directory():
    file_data = [
        {
            'filename': 'file0.txt',
            'initial_data': 'I am file No.0.',
            'updated_data': 'I am file No.0 and somebody updated me :O.'
        },
        {
            'filename': 'file1.txt',
            'initial_data': 'I am file No.1.',
            'updated_data': 'I am file No.1 and somebody updated me :O.'
        },
    ]

    cwd = Path.cwd()
    print(cwd)

    number = 0
    while (cwd / f'testing_dir_{number}').exists():
        number += 1
    testing_files_path = _prep_dir(cwd, f'testing_dir_{number}')

    dir0_path = _prep_dir(testing_files_path, 'dir0')
    dir0_file0_path = _prep_file(parent=dir0_path, file_name=file_data[0]['filename'],
                                 content=file_data[0]['initial_data'])
    dir0_file1_path = _prep_file(parent=dir0_path, file_name=file_data[1]['filename'],
                                 content=file_data[1]['initial_data'])

    dir01_path = _prep_dir(dir0_path, 'dir01')
    dir01_file0_path = _prep_file(parent=dir01_path, file_name=file_data[0]['filename'],
                                 content=file_data[0]['initial_data'])

    dir1_path = _prep_dir(testing_files_path, 'dir1')
    dir1_file0_path = _prep_file(parent=dir1_path, file_name=file_data[0]['filename'],
                                 content=file_data[0]['updated_data'])
    dir1_file1_path = _prep_file(parent=dir1_path, file_name=file_data[1]['filename'],
                                 content=file_data[1]['updated_data'])

    return {
        'file_data': file_data,
        'dirs': [testing_files_path, dir0_path, dir01_path, dir1_path],
        'files': [dir0_file0_path, dir0_file1_path, dir01_file0_path, dir1_file0_path, dir1_file1_path],
    }

def are_files_the_same(file1: Path, file2: Path) -> bool:
    with open(file1, 'r') as f1:
        with open(file2, 'r') as f3:
            return f1.read() == f3.read()


def test_run_rsync_up_dir_not_exists():
    files_data = _prepare_testing_directory()
    dir0 = files_data['dirs'][1]
    dir2 = files_data['dirs'][0] / "dir2"

    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    runner.run_rsync_up(str(dir0)+'/', str(dir2))

    assert True == are_files_the_same(dir0 / 'file0.txt', dir2 / 'file0.txt')
    assert True == are_files_the_same(dir0 / 'file1.txt', dir2 / 'file1.txt')
    assert True == are_files_the_same(dir0 / 'dir01' / 'file0.txt', dir2 / 'dir01' / 'file0.txt')

    shutil.rmtree(files_data['dirs'][0])

def test_run_rsync_up_dir_exists_files_not_exist():
    files_data = _prepare_testing_directory()
    dir0 = files_data['dirs'][1]
    dir2 = _prep_dir(files_data['dirs'][0], 'dir2')

    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    runner.run_rsync_up(str(dir0)+'/', str(dir2))

    assert True == are_files_the_same(dir0 / 'file0.txt', dir2 / 'file0.txt')
    assert True == are_files_the_same(dir0 / 'file1.txt', dir2 / 'file1.txt')
    assert True == are_files_the_same(dir0 / 'dir01' / 'file0.txt', dir2 / 'dir01' / 'file0.txt')

    shutil.rmtree(files_data['dirs'][0])

def test_run_rsync_up_dir_exists_files_updated():
    files_data = _prepare_testing_directory()
    dir0 = files_data['dirs'][1]
    dir1 = files_data['dirs'][3]
    dir2 = files_data['dirs'][0] / "dir2"
    shutil.copytree(dir0, str(dir2)+"/")
    assert os.path.exists(dir0 / 'dir01')

    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    runner.run_rsync_up(str(dir1)+'/', str(dir2))

    assert True == are_files_the_same(dir1 / 'file0.txt', dir2 / 'file0.txt')
    assert True == are_files_the_same(dir1 / 'file1.txt', dir2 / 'file1.txt')
    assert True == are_files_the_same(dir0 / 'dir01' / 'file0.txt', dir2 / 'dir01' / 'file0.txt')

    shutil.rmtree(files_data['dirs'][0])

def test_run_rsync_down_dir_not_exists():
    files_data = _prepare_testing_directory()
    dir0 = files_data['dirs'][1]
    dir2 = files_data['dirs'][0] / "dir2"

    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    runner.run_rsync_down(str(dir0)+'/', str(dir2))

    assert True == are_files_the_same(dir0 / 'file0.txt', dir2 / 'file0.txt')
    assert True == are_files_the_same(dir0 / 'file1.txt', dir2 / 'file1.txt')
    assert True == are_files_the_same(dir0 / 'dir01' / 'file0.txt', dir2 / 'dir01' / 'file0.txt')

    shutil.rmtree(files_data['dirs'][0])

def test_run_rsync_down_dir_exists_files_not_exist():
    files_data = _prepare_testing_directory()
    dir0 = files_data['dirs'][1]
    dir2 = _prep_dir(files_data['dirs'][0], 'dir2')

    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    runner.run_rsync_down(str(dir0)+'/', str(dir2))

    assert True == are_files_the_same(dir0 / 'file0.txt', dir2 / 'file0.txt')
    assert True == are_files_the_same(dir0 / 'file1.txt', dir2 / 'file1.txt')
    assert True == are_files_the_same(dir0 / 'dir01' / 'file0.txt', dir2 / 'dir01' / 'file0.txt')

    shutil.rmtree(files_data['dirs'][0])

def test_run_rsync_down_dir_exists_files_updated():
    files_data = _prepare_testing_directory()
    dir0 = files_data['dirs'][1]
    dir1 = files_data['dirs'][3]
    dir2 = files_data['dirs'][0] / "dir2"
    shutil.copytree(dir0, str(dir2)+"/")
    assert os.path.exists(dir0 / 'dir01')

    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    runner.run_rsync_down(str(dir1)+'/', str(dir2))

    assert True == are_files_the_same(dir1 / 'file0.txt', dir2 / 'file0.txt')
    assert True == are_files_the_same(dir1 / 'file1.txt', dir2 / 'file1.txt')
    assert True == are_files_the_same(dir0 / 'dir01' / 'file0.txt', dir2 / 'dir01' / 'file0.txt')

    shutil.rmtree(files_data['dirs'][0])