import pytest
from click import ClickException
import subprocess
from getpass import getuser

from local_head_command_runner import LocalHeadCommandRunner, InvalidLocalHeadArg

#   Command, expected output, additional arguments
test_cases_test_run = [
    ('whoami', getuser() + '\n', {}),
    ('echo foo', 'foo\n', {}),
    ('echo "$USER"', getuser() + '\n', {}),
    ('echo "$BAR"', '\n', {}),
    ('echo "$BAR"', 'baz\n', {'environment_variables': {'BAR': 'baz'}}),
]

@pytest.mark.parametrize('cmd, output, kwargs', test_cases_test_run)
def test_run(cmd, output, kwargs):
    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    assert runner.run(cmd, **kwargs) == output

@pytest.mark.parametrize('kwargs', (
    {'shutdown_after_run': True},
    {'port_forward': [(7878, 7979)]},
    {'ssh_options_override_ssh_key': 'FooBar'},
    {'run_env': 'FooBar'},
    {'timeout': 121},
))
def test_invalid_kwargs(kwargs):
    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    with pytest.raises(InvalidLocalHeadArg):
        runner.run('echo foo', **kwargs)


test_cases_test_failing_command = [
    ('FooBar', {'exit_on_fail': True}),
]
@pytest.mark.parametrize('cmd, kwargs', test_cases_test_failing_command)
def test_failing_command(cmd, kwargs):
    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    with pytest.raises(ClickException):
        runner.run(cmd, **kwargs)
