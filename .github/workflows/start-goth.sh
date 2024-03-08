#!/bin/bash
echo CLEANUP DOCKER
docker rm --force $(docker ps -a -q)
sudo systemctl restart docker

echo LOGIN TO GHCR.IO
echo $GITHUB_API_TOKEN | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin

echo REMOVING PREBIOUS GOTH SESSION FILES
rm /tmp/goth_interactive.env
rm -rf /root/.cache/
rm -rf /tmp/goth-tests/

echo CREATING VENV
rm -rf .envs/goth
python -m venv .envs/goth
source .envs/goth/bin/activate

echo INSTALLING TOOLS
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel

echo INSTALLING DEPENDENCIES
python -m pip install goth==$GOTH_VERSION pytest pytest-asyncio pexpect

echo CREATING ASSETS
python -m goth create-assets .envs/goth/assets
# disable use-proxy
sed -Ezi 's/("\n.*use\-proxy:\s)(True)/\1False/mg' .envs/goth/assets/goth-config.yml

echo STARTING NETWORK
cat .envs/goth/assets/goth-config.yml
python -m goth start .envs/goth/assets/goth-config.yml &
GOTH_PID=$!
echo "GOTH_PID=$GOTH_PID" | tee "$GITHUB_ENV"

echo WAITING FOR NETWORK
STARTED_WAITING_AT=$((SECONDS + 900))
while [ ! -f /tmp/goth_interactive.env ]; do
  sleep 5
  if ! ps -p $GOTH_PID > /dev/null; then
    echo GOTH NETWORK FAILED TO START SUCESFULLY
    exit 1
  fi
  if [ $SECONDS -gt $STARTED_WAITING_AT ]; then
    echo GOTH NETWORK FAILED TO START IN 15 MINUTES
    exit 1
  fi
done

deactivate
cat /tmp/goth_interactive.env | envsubst | sed "s/^export *//g" | tee "$GITHUB_ENV"
echo STARTUP COMPLETED

cat $GITHUB_ENV