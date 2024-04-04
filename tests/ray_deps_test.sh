#!/bin/bash
set -x

poetry lock --no-update
poetry export --without-hashes --format requirements.txt --only ray > .requirements.txt

rm -drf venv-ray-deps
python -m venv venv-ray-deps
source venv-ray-deps/bin/activate
pip install toml  # only for the sake of this test setup and version check that have access to pyproject.toml
pip install -r .requirements.txt

python -c "from ray_on_golem.provider.node_provider import GolemNodeProvider"
exit $?