import json
import sys
import subprocess

from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple

import click

from ray.autoscaler._private.cli_logger import cf, cli_logger
from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler._private.subprocess_output_util import (
    ProcessRunnerError,
    is_output_redirected,
    run_cmd_redirected,
)

_config = {"use_login_shells": True,
           "silent_rsync": True}


def is_rsync_silent():
    return _config["silent_rsync"]


def set_rsync_silent(val):
    """Choose whether to silence rsync output.

    Most commands will want to list rsync'd files themselves rather than
    print the default rsync spew.
    """
    _config["silent_rsync"] = val


def is_using_login_shells():
    return _config["use_login_shells"]


def set_using_login_shells(val: bool):
    """Choose between login and non-interactive shells.

    Non-interactive shells have the benefit of receiving less output from
    subcommands (since progress bars and TTY control codes are not printed).
    Sometimes this can be significant since e.g. `pip install` prints
    hundreds of progress bar lines when downloading.

    Login shells have the benefit of working very close to how a proper bash
    session does, regarding how scripts execute and how the environment is
    setup. This is also how all commands were ran in the past. The only reason
    to use login shells over non-interactive shells is if you need some weird
    and non-robust tool to work.

    Args:
        val: If true, login shells will be used to run all commands.
    """
    _config["use_login_shells"] = val


class InvalidLocalHeadArg(Exception):
    def __init__(self, arg, val):
        msg = f"LocalHeadCommandRunner doesn't work with {arg} = {val}"
        super().__init__(msg)


def _with_environment_variables(cmd: str, environment_variables: Dict[str, object]):
    """Prepend environment variables to a shell command.

    Args:
        cmd: The base command.
        environment_variables (Dict[str, object]): The set of environment
            variables. If an environment variable value is a dict, it will
            automatically be converted to a one line yaml string.
    """

    as_strings = []
    for key, val in environment_variables.items():
        val = json.dumps(val, separators=(",", ":"))
        s = "export {}={};".format(key,
                                   val)  # TODO W oryginale było to "quote(val)" zamiast "val" - czy myślisz,że to jakoś bardzo ważne, bo zadziałało xd?
        as_strings.append(s)
    all_vars = "".join(as_strings)
    return all_vars + cmd


class LocalHeadCommandRunner(CommandRunnerInterface):
    def __init__(self, log_prefix: str, cluster_name: str, process_runner: ModuleType):
        #   NOTE: We have here a subset of things passed to 
        #   `NodeProvider.get_command_runner` that I think might be useful.
        #   Ommited arguments:
        #   *   node_id, as it's always the same node
        #   *   auth_config, as we're not authenticating
        #   *   use_internal_ip - I don't know what is this for
        #   *   docker_config - we decided to run only non-docker ray
        self.log_prefix = log_prefix
        self.cluster_name = cluster_name
        self.process_runner = process_runner

    def _run_helper(
            self, final_cmd, with_output=False, exit_on_fail=False, silent=False
    ):
        """Run a command that was already setup with SSH and `bash` settings.

        Args:
            cmd (List[str]):
                Full command to run. Should include SSH options and other
                processing that we do.
            with_output (bool):
                If `with_output` is `True`, command stdout will be captured and
                returned.
            exit_on_fail (bool):
                If `exit_on_fail` is `True`, the process will exit
                if the command fails (exits with a code other than 0).

        Raises:
            ProcessRunnerError if using new log style and disabled
                login shells.
            click.ClickException if using login shells.
        """
        try:
            # For now, if the output is needed we just skip the new logic.
            # In the future we could update the new logic to support
            # capturing output, but it is probably not needed.
            if not with_output:
                return run_cmd_redirected(
                    final_cmd,
                    process_runner=self.process_runner,
                    silent=silent,
                    use_login_shells=is_using_login_shells(),
                )
            else:
                return self.process_runner.check_output(final_cmd)
        except subprocess.CalledProcessError as e:
            joined_cmd = " ".join(final_cmd)
            if not is_using_login_shells():
                raise ProcessRunnerError(
                    "Command failed",
                    "ssh_command_failed",
                    code=e.returncode,
                    command=joined_cmd,
                )

            if exit_on_fail:
                raise click.ClickException(
                    "Command failed:\n\n  {}\n".format(joined_cmd)
                ) from None
            else:
                fail_msg = "SSH command failed."
                if is_output_redirected():
                    fail_msg += " See above for the output from the failure."
                raise click.ClickException(fail_msg) from None
        finally:
            # Do our best to flush output to terminal.
            # See https://github.com/ray-project/ray/pull/19473.
            sys.stdout.flush()
            sys.stderr.flush()

    def run(
            self,
            cmd: Optional[str] = None,
            timeout: int = 120,
            exit_on_fail: bool = False,
            port_forward: List[Tuple[int, int]] = None,
            with_output: bool = False,
            environment_variables: Optional[Dict[str, object]] = None,
            run_env: str = "auto",
            ssh_options_override_ssh_key: str = "",
            shutdown_after_run: bool = False,
    ) -> str:
        if timeout != 120:
            raise InvalidLocalHeadArg('timeout', timeout)
        if port_forward is not None:
            raise InvalidLocalHeadArg('port_forward', port_forward)
        if run_env != 'auto':
            raise InvalidLocalHeadArg('run_env', run_env)
        if ssh_options_override_ssh_key:
            raise InvalidLocalHeadArg('ssh_options_override_ssh_key', ssh_options_override_ssh_key)
        if shutdown_after_run:
            raise InvalidLocalHeadArg('shutdown_after_run', shutdown_after_run)

        if cmd:
            if environment_variables:
                cmd = _with_environment_variables(cmd=cmd, environment_variables=environment_variables)

        try:
            if not with_output:
                return run_cmd_redirected(
                    cmd,
                    process_runner=self.process_runner,
                    silent=True,
                    use_login_shells=is_using_login_shells(),
                )
            else:
                bytes_output = self.process_runner.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            joined_cmd = " ".join(cmd)
            if not is_using_login_shells():
                raise ProcessRunnerError(
                    "Command failed",
                    "ssh_command_failed",
                    code=e.returncode,
                    command=joined_cmd,
                )

            if exit_on_fail:
                raise click.ClickException(
                    "Command failed:\n\n  {}\n".format(joined_cmd)
                ) from None
            else:
                fail_msg = "SSH command failed."
                if is_output_redirected():
                    fail_msg += " See above for the output from the failure."
                raise click.ClickException(fail_msg) from None
        finally:
            # Do our best to flush output to terminal.
            # See https://github.com/ray-project/ray/pull/19473.
            sys.stdout.flush()
            sys.stderr.flush()

        return bytes_output.decode()

    def _create_rsync_filter_args(self, options):
        if not options:
            rsync_excludes, rsync_filters = [], []
        else:
            rsync_excludes = options.get("rsync_exclude")
            rsync_filters = options.get("rsync_filter")

        exclude_args = [
            ["--exclude", rsync_exclude] for rsync_exclude in rsync_excludes
        ]
        filter_args = [
            ["--filter", "dir-merge,- {}".format(rsync_filter)]
            for rsync_filter in rsync_filters
        ]

        # Combine and flatten the two lists
        return [arg for args_list in exclude_args + filter_args for arg in args_list]

    def _run_rsync(
            self, source: str, target: str, options: Optional[Dict[str, Any]] = None
    ) -> None:
        if source == target:
            return

        command = ["rsync"]
        command += ["-avz"]
        command += self._create_rsync_filter_args(options=options)
        command += [source, target]
        cli_logger.verbose("Running `{}`", cf.bold(" ".join(command)))
        final_cmd = ''
        for index in range(len(command)):
            final_cmd += command[index]
            if index != len(command):
                final_cmd += ' '
        self.run(cmd=final_cmd, with_output=not is_rsync_silent())

    def run_rsync_up(
            self, source: str, target: str, options: Optional[Dict[str, Any]] = None
    ) -> None:
        """Rsync files up to the cluster node.

        Args:
            source: The (local) source directory or file.
            target: The (remote) destination path.
            options:
        """
        self._run_rsync(source=source, target=target, options=options)

    def run_rsync_down(
            self, source: str, target: str, options: Optional[Dict[str, Any]] = None
    ) -> None:
        """Rsync files down from the cluster node.

        Args:
            source: The (remote) source directory or file.
            target: The (local) destination path.
        """
        self._run_rsync(source=source, target=target, options=options)