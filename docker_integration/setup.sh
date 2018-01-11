#!/bin/bash
#gcloud docker -a
docker login
docker stack deploy --with-registry-auth -c docker-stack.yml threatapi
