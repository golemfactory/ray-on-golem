from ray.autoscaler._private.cli_logger import cli_logger  # noqa

from ray_on_golem.ctl.log import RayOnGolemCtlLogger


class NodeProviderCliLogger(RayOnGolemCtlLogger):
    def info(self, msg: str):
        cli_logger.print(msg, no_format=True)

    def warning(self, msg: str):
        cli_logger.warning(msg, no_format=True)

    def verbose(self, msg: str):
        cli_logger.verbose(msg, no_format=True)

    def error(self, msg: str):
        cli_logger.abort(msg, no_format=True)
