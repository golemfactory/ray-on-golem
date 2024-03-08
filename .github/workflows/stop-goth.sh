#!/bin/bash
echo STOP GOTH
kill $(ps -aux | grep "[g]oth start" | awk '{print $2}')

echo STOP DOCKER CONTAINERS
docker rm --force $(docker ps -a -q)
