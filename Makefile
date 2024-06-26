#!make

PROJECT_NAME = aaq
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
ENDPOINT_URL = localhost:8000
OPENAI_API_KEY := $(shell printenv OPENAI_API_KEY)

## Main targets
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Note: Run `make fresh-env psycopg2-binary=true` to manually replace psycopg with psycopg2-binary
fresh-env :
	conda remove --name $(PROJECT_NAME) --all -y
	conda create --name $(PROJECT_NAME) python==3.10 -y

	$(CONDA_ACTIVATE) $(PROJECT_NAME); \
	pip install -r core_backend/requirements.txt --ignore-installed; \
	pip install -r requirements-dev.txt --ignore-installed; \
	pre-commit install

	if [ "$(psycopg2-binary)" = "true" ]; then \
		$(CONDA_ACTIVATE) $(PROJECT_NAME); \
		pip uninstall -y psycopg2==2.9.9; \
		pip install psycopg2-binary==2.9.9; \
	fi

# Dev requirements
setup-dev: setup-db add-users-to-db setup-llm-proxy
teardown-dev: teardown-db teardown-llm-proxy

## Helper targets

# Add users to db
add-users-to-db:
	$(CONDA_ACTIVATE) $(PROJECT_NAME); \
	python core_backend/add_users_to_db.py

# Dev db
setup-db:
	-@docker stop postgres-local
	-@docker rm postgres-local
	@docker system prune -f
	@sleep 2
	@docker run --name postgres-local \
     -e POSTGRES_PASSWORD=postgres \
     -p 5432:5432 \
     -d pgvector/pgvector:pg16
	cd core_backend && \
	python -m alembic upgrade head

teardown-db:
	@docker stop postgres-local
	@docker rm postgres-local

# Dev LiteLLM Proxy server
setup-llm-proxy:
	-@docker stop litellm-proxy
	-@docker rm litellm-proxy
	@docker system prune -f
	@sleep 2
	@docker pull ghcr.io/berriai/litellm:main-v1.34.6
	@docker run \
		--name litellm-proxy \
		--rm \
		-v "$(CURDIR)/deployment/docker-compose/litellm_proxy_config.yaml":/app/config.yaml \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		-e GEMINI_API_KEY=$(GEMINI_API_KEY) \
		-e EMBEDDINGS_API_KEY=$(EMBEDDINGS_API_KEY) \
		-e EMBEDDINGS_ENDPOINT=$(EMBEDDINGS_ENDPOINT) \
		-p 4000:4000 \
		-d ghcr.io/berriai/litellm:main-v1.34.6 \
		--config /app/config.yaml --detailed_debug


teardown-llm-proxy:
	@docker stop litellm-proxy
	@docker rm litellm-proxy

setup-embeddings:
	-@docker stop embeddings
	-@docker rm embeddings
	@docker system prune -f
	@sleep 2
	@docker build -t embeddings ./optional_components/embeddings
	@docker run \
		--name embeddings \
		-e EMBEDDINGS_API_KEY=$(EMBEDDINGS_API_KEY) \
		-e HUGGINGFACE_MODEL=$(HUGGINGFACE_MODEL) \
		-p 8080:8080 \
		-d embeddings

teardown-embeddings:
	@docker stop embeddings
	@docker rm embeddings
