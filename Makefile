IMAGE   := fala-gavea
PORT    := 8000
DATA    := $(CURDIR)/local-data
SECRET  := local-dev-secret

.PHONY: build run stop rm restart logs shell clean help

build:
	docker build -t $(IMAGE) .

run:
	powershell -Command "New-Item -ItemType Directory -Force '$(DATA)' | Out-Null"
	docker run -d --name $(IMAGE) -p $(PORT):$(PORT) \
		-v "$(DATA):/data" \
		-e DATABASE_URL=sqlite:////data/fala_gavea.db \
		-e CHROMA_DATA_DIR=/data/chromadb \
		-e JWT_SECRET=$(SECRET) \
		$(IMAGE)
	@echo "App running at http://localhost:$(PORT)"

stop:
	docker stop $(IMAGE)

rm: stop
	docker rm $(IMAGE)

restart: rm run

logs:
	docker logs -f $(IMAGE)

shell:
	docker exec -it $(IMAGE) /bin/sh

clean:
	docker rmi $(IMAGE)

rebuild: clean build

help:
	@echo "Targets:"
	@echo "  build    — build the Docker image"
	@echo "  run      — start the container (detached)"
	@echo "  stop     — stop the container"
	@echo "  rm       — stop and remove the container"
	@echo "  restart  — rm + run"
	@echo "  logs     — follow container logs"
	@echo "  shell    — open a shell inside the container"
	@echo "  clean    — remove the image"
	@echo "  rebuild  — clean + build"
