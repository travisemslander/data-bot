IMAGE_NAME = data-bot
CONTAINER_NAME := $(IMAGE_NAME)-instance

.PHONY: build run stop logs clean all

all: build run

build:
	@echo "--- building image: $(IMAGE_NAME) ---"
	docker build -t $(IMAGE_NAME) .

run:
	@echo "-- Starting container $(CONTAINER_NAME) as detatched ---"
	docker run -d --env-file .env --name $(CONTAINER_NAME) $(IMAGE_NAME)
	@echo "Should be running, will begin watching logs."
	@echo "ctrl+c will stop log monitoring, but you must run the following to stop the bot:"
	@echo "make stop"
	@echo "..."
	sleep 2
	docker logs -f $(CONTAINER_NAME)

stop:
	@echo "-- stopping container and removing container ---"
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)


logs:
	@echo "--- Trailing logs for: $(CONTAINER_NAME) (press ctrl+c to exit) ---"
	docker logs $(CONTAINER_NAME)


clean:
	@echo "--- Removing docker image $(IMAGE_NAME) ---"
	docker rmi $(IMAGE_NAME) || true



