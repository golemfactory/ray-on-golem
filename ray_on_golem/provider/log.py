from ray.autoscaler._private.cli_logger import cli_logger  # noqa

from ray_on_golem.ctl.log import RayOnGolemCtlLogger


class NodeProviderCliLogger(RayOnGolemCtlLogger):
    def info(self, msg: str):
        cli_logger.print(msg)

    def warning(self, msg: str):
        cli_logger.warning(msg)

    def verbose(self, msg: str):
        cli_logger.verbose(msg)

    def error(self, msg: str):
        cli_logger.abort(msg)
