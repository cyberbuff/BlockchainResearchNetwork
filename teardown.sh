#! /bin/sh

RED='\033[0;31m'
NC='\033[0m'

docker ps

echo -e "${RED}killing containers,${NC}"
docker stop iroha
docker stop some-postgres

echo -e "${RED}removing rest${NC}"
docker rm iroha
docker rm some-postgres

docker volume rm blockstore
docker network prune -f 

echo -e "${RED}check the processes${NC}"
docker container ls
echo -e "${RED}Images${NC}"
docker image ls
echo -e "${RED}Volumes${NC}"
docker volume ls
echo -e "${RED}Network${NC}"
docker network ls
