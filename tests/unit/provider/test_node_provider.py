from pathlib import Path
from unittest import mock

import pytest
import yaml

from ray_on_golem.ctl.ctl import RayOnGolemCtl
from ray_on_golem.provider.node_provider import GolemNodeProvider
from ray_on_golem.server.models import ProviderConfigData

ROOT_PATH = Path(__file__).parents[3]

CLUSTER_CONFIG_STUB = {
    "cluster_name": "test",
    "provider": {
        "parameters": {
            "node_config": {},
        },
    },
}


@pytest.fixture
def disable_webserver(monkeypatch):
    monkeypatch.setattr(RayOnGolemCtl, "start_webserver", mock.Mock())


@pytest.fixture
def patch_path(monkeypatch):
    monkeypatch.setattr(Path, "open", mock.MagicMock())
    monkeypatch.setattr(Path, "exists", mock.Mock(return_value=True))


@pytest.mark.parametrize(
    "cluster_config",
    (
        yaml.safe_load(open(ROOT_PATH / "golem-cluster.mini.yaml")),
        yaml.safe_load(open(ROOT_PATH / "golem-cluster.yaml")),
        CLUSTER_CONFIG_STUB,
    ),
)
def test_node_provider_defaults(disable_webserver, patch_path, cluster_config):
    resolved_config = GolemNodeProvider.bootstrap_config(cluster_config)

    provider_params = resolved_config["provider"]["parameters"]
    provider_params = GolemNodeProvider._map_ssh_config(provider_params)

    ProviderConfigData(**provider_params)
