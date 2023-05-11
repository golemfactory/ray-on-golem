import pytest
import subprocess
from getpass import getuser

from local_head_command_runner import LocalHeadCommandRunner, InvalidLocalHeadArg

#   Command, expected output, additional arguments
test_cases = [
    ('whoami', getuser() + '\n', {}),
    ('echo foo', 'foo\n', {}),
    ('echo "$USER"', getuser() + '\n', {}),
    ('echo "$BAR"', '\n', {}),
    ('echo "$BAR"', 'baz\n', {'environment_variables': {'BAR': 'baz'}}),
]

@pytest.mark.parametrize('cmd, output, kwargs', test_cases)
def test_run(cmd, output, kwargs):
    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    assert runner.run(cmd, **kwargs) == output

@pytest.mark.parametrize('kwargs', (
    {'shutdown_after_run': True},
    {'port_forward': [(7878, 7979)]},
    {'ssh_options_override_ssh_key': 'FooBar'},
))
def test_invalid_kwargs(kwargs):
    runner = LocalHeadCommandRunner(log_prefix="", cluster_name="some_cluster", process_runner=subprocess)
    with pytest.raises(InvalidLocalHeadArg):
        runner.run('echo foo', **kwargs)
