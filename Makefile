DOCKER_USERNAME ?= narutosimaha
APPLICATION_NAME ?= lec-chatbot
 
config-dockerd:
	mkdir -p /etc/docker
	cp ./daemon.json /etc/docker

build:
	docker build --tag ${DOCKER_USERNAME}/${APPLICATION_NAME} .

run:
	docker compose up -force-recreate -d

test:
	pytest