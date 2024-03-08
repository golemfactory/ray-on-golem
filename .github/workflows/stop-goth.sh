#!/bin/bash
echo STOP GOTH
kill $

echo STOP DOCKER CONTAINERS
docker rm --force $(docker ps -a -q)
