#!/bin/bash

sudo docker-compose stop
sudo docker-compose rm

echo "Creating Docker network"
sudo docker network create --gateway 172.39.0.1 --subnet 172.39.0.2/24 --scope local internal
sudo docker network create --gateway 172.21.0.1 --subnet 172.21.0.2/24 --scope local proxy

echo "Creating configuration"
read -p "`echo -e 'Make a choice: \n 1) Above proxy \n 2) Standalone \n 3) Local \n>'`" decision
if [ "$decision" == "1" ]; then
    cp zones/.env-above-proxy .env 
    cp zones/docker-compose-insecure.yml docker-compose.yml
fi
if [ "$decision" == "2" ]; then
    cp zones/.env-standalone .env 
    cp zones/docker-compose-secure-test.yml docker-compose.yml
    echo "Stop Apache"
    sudo systemctl stop apache2
fi
if [ "$decision" == "3" ]; then
    cp zones/.env-local-secure .env 
    cp zones/docker-compose-secure.yml docker-compose.yml
    echo "Stop Apache"
    sudo systemctl stop apache2
fi

echo "Docker-Compose building..."
sudo docker-compose up --build -d