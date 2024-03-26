#!/bin/bash
echo STOP GOTH
kill $GOTH_PID

echo STOP DOCKER CONTAINERS
docker rm --force $(docker ps -a -q)
