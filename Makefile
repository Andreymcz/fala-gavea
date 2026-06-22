IMAGE   := fala-gavea
PORT    := 8000
DATA    := $(CURDIR)/local-data
SECRET  := local-dev-secret

# Dev-only admin bootstrap credentials (created on backend startup).
# Override on the command line for non-dev use, e.g.:
#   make run-backend ADMIN_EMAIL=me@example.com ADMIN_PASSWORD=secret
ADMIN_EMAIL    := admin@gavea.br
ADMIN_PASSWORD := admin12345!
ADMIN_NAME     := Admin

# Ollama local LLM — override on the command line, e.g.:
#   make run-backend OLLAMA_URL=http://localhost:11434 OLLAMA_MODEL=llama3:8b
OLLAMA_URL   := http://localhost:11434
OLLAMA_MODEL := qwen2.5:7b

# Log level for the fala_gavea package (DEBUG shows LLM request/response traces).
# Override: make run-backend LOG_LEVEL=INFO
LOG_LEVEL := DEBUG

.PHONY: build run-backend run-frontend run-docker stop rm restart logs shell clean rebuild help

build:
	docker build -t $(IMAGE) .

run-backend: export DATABASE_URL := sqlite:///$(DATA)/fala_gavea.db
run-backend: export CHROMA_DATA_DIR := $(DATA)/chromadb
run-backend: export JWT_SECRET := $(SECRET)
run-backend: export FALA_GAVEA_ADMIN_EMAIL := $(ADMIN_EMAIL)
run-backend: export FALA_GAVEA_ADMIN_PASSWORD := $(ADMIN_PASSWORD)
run-backend: export FALA_GAVEA_ADMIN_NAME := $(ADMIN_NAME)
run-backend: export FALA_GAVEA_OLLAMA_URL := $(OLLAMA_URL)
run-backend: export FALA_GAVEA_OLLAMA_MODEL := $(OLLAMA_MODEL)
run-backend: export FALA_GAVEA_LOG_LEVEL := $(LOG_LEVEL)
run-backend:
	@echo "Running backend locally with SQLite database at $(DATA)/fala_gavea.db"
	@echo "Admin bootstrap: $(ADMIN_EMAIL) / $(ADMIN_PASSWORD)"
	@echo "Ollama: $(OLLAMA_URL) model=$(OLLAMA_MODEL)"
	powershell -Command "New-Item -ItemType Directory -Force '$(DATA)' | Out-Null"
	uv run uvicorn fala_gavea.presentation.api.main:app --reload --log-level $(shell powershell -Command "'$(LOG_LEVEL)'.ToLower()")

run-frontend:
	@echo "Running frontend locally at http://localhost:3000"
	cd frontend && npm install && npm run dev

run-docker:
	powershell -Command "New-Item -ItemType Directory -Force '$(DATA)' | Out-Null"
	docker run -d --name $(IMAGE) -p $(PORT):$(PORT) \
		-v "$(DATA):/data" \
		-e DATABASE_URL=sqlite:////data/fala_gavea.db \
		-e CHROMA_DATA_DIR=/data/chromadb \
		-e JWT_SECRET=$(SECRET) \
		-e FALA_GAVEA_ADMIN_EMAIL=$(ADMIN_EMAIL) \
		-e FALA_GAVEA_ADMIN_PASSWORD=$(ADMIN_PASSWORD) \
		-e FALA_GAVEA_ADMIN_NAME=$(ADMIN_NAME) \
		-e FALA_GAVEA_OLLAMA_URL=$(OLLAMA_URL) \
		-e FALA_GAVEA_OLLAMA_MODEL=$(OLLAMA_MODEL) \
		$(IMAGE)
	@echo "App running at http://localhost:$(PORT)"
	@echo "Admin bootstrap: $(ADMIN_EMAIL) / $(ADMIN_PASSWORD)"

stop:
	docker stop $(IMAGE)

rm: stop
	docker rm $(IMAGE)

restart: rm run-docker

logs:
	docker logs -f $(IMAGE)

shell:
	docker exec -it $(IMAGE) /bin/sh

clean:
	docker rmi $(IMAGE)

rebuild: clean build

help:
	@echo "Targets:"
	@echo "  run-backend   — run the FastAPI backend locally (uv + uvicorn --reload)"
	@echo "  run-frontend  — run the Vite frontend locally (http://localhost:3000)"
	@echo "  build         — build the Docker image"
	@echo "  run-docker    — start the container (detached)"
	@echo "  stop     — stop the container"
	@echo "  rm       — stop and remove the container"
	@echo "  restart  — rm + run"
	@echo "  logs     — follow container logs"
	@echo "  shell    — open a shell inside the container"
	@echo "  clean    — remove the image"
	@echo "  rebuild  — clean + build"
