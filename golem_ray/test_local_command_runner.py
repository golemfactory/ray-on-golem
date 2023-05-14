import pytest
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
