#!/bin/bash

cd /home/TolaActivity
git pull origin docker
docker-compose up mysqldb
sleep 5
docker-compose up

