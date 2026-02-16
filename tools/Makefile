# Makefile for Books Database Service and MCP Server
# Author: Generated for Books Database Project
# Date: 2026-01-01

.PHONY: help build-all build-book-service build-mcp-service \
        build-test build-test-book-service build-test-mcp-service \
        push-all push-book-service push-mcp-service \
        run-local-book-service run-local-mcp-service \
        run-test-all run-test-book-service run-test-mcp-service \
        stop-test-all stop-test-book-service stop-test-mcp-service \
        logs-test-book-service logs-test-mcp-service \
        test test-book-service test-mcp-service test-local test-coverage \
        test-bookdbtool test-bookdbtool-coverage \
        up-book-service up-mcp-server down-book-service down-mcp-server \
        clean clean-images clean-test-records stop-all info

# Variables
HOSTNAME := $(shell hostname)
REGISTRY := localhost:5000
BOOK_SERVICE_IMAGE := book-service
MCP_SERVICE_IMAGE := booksmcp-service
BOOK_TEST_IMAGE := book-service-test
MCP_TEST_IMAGE := bookmcp-service-test
VERSION := latest

# Detect if we're on lambda-dual
ifeq ($(HOSTNAME),lambda-dual)
    USE_REGISTRY := true
    BOOK_SERVICE_TAG := $(REGISTRY)/$(BOOK_SERVICE_IMAGE):$(VERSION)
    MCP_SERVICE_TAG := $(REGISTRY)/$(MCP_SERVICE_IMAGE):$(VERSION)
    BOOK_TEST_TAG := $(BOOK_TEST_IMAGE):$(VERSION)
    MCP_TEST_TAG := $(MCP_TEST_IMAGE):$(VERSION)
else
    USE_REGISTRY := false
    BOOK_SERVICE_TAG := $(BOOK_SERVICE_IMAGE)
    MCP_SERVICE_TAG := $(MCP_SERVICE_IMAGE)
    BOOK_TEST_TAG := $(BOOK_TEST_IMAGE)
    MCP_TEST_TAG := $(MCP_TEST_IMAGE)
endif

# Directories
BOOK_SERVICE_DIR := book_service
BOOKS_API_DIR := $(BOOK_SERVICE_DIR)/books
MCP_DIR := $(BOOK_SERVICE_DIR)/booksmcp
BOOKSDB_DIR := $(BOOK_SERVICE_DIR)/booksdb
CONFIG_DIR := $(BOOK_SERVICE_DIR)/config
TEST_DIR := $(BOOK_SERVICE_DIR)/test_books

# Default target
help:
	@echo "==================================================================="
	@echo "Books Database Service - Makefile"
	@echo "==================================================================="
	@echo "Detected hostname: $(HOSTNAME)"
	@echo "Using registry: $(USE_REGISTRY)"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "  BUILD TARGETS:"
	@echo "    build-all                - Build all Docker images (production)"
	@echo "    build-book-service       - Build book service Docker image"
	@echo "    build-mcp-service        - Build MCP server Docker image"
	@echo "    build-test               - Build test Docker images (both services)"
	@echo "    build-test-book-service  - Build book service test image"
	@echo "    build-test-mcp-service   - Build MCP server test image"
	@echo ""
	@echo "  PUSH TARGETS (to local registry):"
	@echo "    push-all                 - Push all images to registry"
	@echo "    push-book-service        - Push book service to registry"
	@echo "    push-mcp-service         - Push MCP server to registry"
	@echo ""
	@echo "  LOCAL RUN TARGETS (without Docker):"
	@echo "    run-local-book-service   - Run book service locally with poetry"
	@echo "    run-local-mcp-service    - Run MCP server locally with poetry"
	@echo ""
	@echo "  TEST CONTAINER TARGETS:"
	@echo "    run-test-all             - Run all test containers locally"
	@echo "    run-test-book-service    - Run book service test container (port 9999)"
	@echo "    run-test-mcp-service     - Run MCP server test container (port 3005)"
	@echo "    stop-test-all            - Stop all test containers"
	@echo "    stop-test-book-service   - Stop book service test container"
	@echo "    stop-test-mcp-service    - Stop MCP server test container"
	@echo "    logs-test-book-service   - View book service test logs"
	@echo "    logs-test-mcp-service    - View MCP server test logs"
	@echo ""
	@echo "  TEST EXECUTION TARGETS:"
	@echo "    test                     - Run all tests against Docker instances"
	@echo "    test-book-service        - Run book service tests only"
	@echo "    test-mcp-service         - Run MCP server tests only"
	@echo "    test-local               - Run tests locally with pytest (no Docker)"
	@echo "    test-coverage            - Run tests with coverage report"
	@echo "    test-bookdbtool          - Run bookdbtool unit tests"
	@echo "    test-bookdbtool-coverage - Run bookdbtool tests with coverage"
	@echo ""
	@echo "  UTILITY TARGETS:"
	@echo "    stop-all                 - Stop all running containers (prod & test)"
	@echo "    clean                    - Clean Python cache files"
	@echo "    clean-images             - Remove all built Docker images"
	@echo "    clean-test-records       - Remove test records from the database"
	@echo "    logs-book-service        - View book service container logs"
	@echo "    logs-mcp-service         - View MCP server container logs"
	@echo "    info                     - Show configuration and status"
	@echo ""
	@echo "==================================================================="
	@echo "COMMON WORKFLOWS:"
	@echo ""
	@echo "  Development & Testing:"
	@echo "    make run-test-all      # Start both test containers"
	@echo "    make test              # Run tests against containers"
	@echo "    make stop-test-all     # Clean up test containers"
	@echo ""
	@echo "  Production Build & Deploy:"
	@echo "    make build-all         # Build production images"
	@echo "    make push-all          # Push to registry (if on lambda-dual)"
	@echo ""
	@echo "  Quick Test Individual Service:"
	@echo "    make test-book-service # Build, run, and test book service"
	@echo "    make test-mcp-service   # Build, run, and test MCP server"
	@echo ""
	@echo "==================================================================="

# ===================================================================
# BUILD TARGETS
# ===================================================================

build-all: build-book-service build-mcp-service build-test
	@echo "✓ All images built successfully"

build-book-service:
	@echo "Building book service Docker image..."
	@echo "Tag: $(BOOK_SERVICE_TAG)"
	docker build \
		-f book_service/books/Dockerfile \
		-t $(BOOK_SERVICE_TAG) \
		.
	@echo "✓ Book service image built: $(BOOK_SERVICE_TAG)"

build-mcp-service:
	@echo "Building MCP server Docker image..."
	@echo "Tag: $(MCP_SERVICE_TAG)"
	cd $(BOOK_SERVICE_DIR) && docker build \
		-f booksmcp/Dockerfile \
		-t $(MCP_SERVICE_TAG) \
		.
	@echo "✓ MCP server image built: $(MCP_SERVICE_TAG)"

build-test-book-service:
	@echo "Building book service test Docker image..."
	@echo "Tag: book-service-test:latest"
	docker build \
		-f book_service/books/Dockerfile \
		-t ${BOOK_TEST_TAG} \
		.
	@echo "✓ Book service test image built: $(BOOK_TEST_TAG)"

build-test-mcp-service:
	@echo "Building MCP server test Docker image..."
	@echo "Tag: ${MCP_TEST_TAG}:${VERSION}"
	cd $(BOOK_SERVICE_DIR) && docker build \
		-f booksmcp/Dockerfile \
		-t ${MCP_TEST_TAG} \
		.
	@echo "✓ MCP server test image built: $(MCP_TEST_TAG)"

build-test: build-test-book-service build-test-mcp-service
	@echo "✓ All test images built"

# ===================================================================
# PUSH TARGETS
# ===================================================================

push-all: push-book-service push-mcp-service
	@echo "✓ All images pushed to registry"

push-book-service:
ifeq ($(USE_REGISTRY),true)
	@echo "Pushing book service to registry: $(BOOK_SERVICE_TAG)"
	docker push $(BOOK_SERVICE_TAG)
	@echo "✓ Book service pushed to registry"
else
	@echo "⚠ Not on lambda-dual, skipping registry push"
	@echo "  To push manually, run: docker push $(BOOK_SERVICE_TAG)"
endif

push-mcp-service:
ifeq ($(USE_REGISTRY),true)
	@echo "Pushing MCP server to registry: $(MCP_SERVICE_TAG)"
	docker push $(MCP_SERVICE_TAG)
	@echo "✓ MCP server pushed to registry"
else
	@echo "⚠ Not on lambda-dual, skipping registry push"
	@echo "  To push manually, run: docker push $(MCP_SERVICE_TAG)"
endif

# ===================================================================
# LOCAL RUN TARGETS (without Docker)
# ===================================================================

run-local-book-service:
	@echo "Starting book service locally (without Docker)..."
	@echo "Make sure you have poetry installed and dependencies installed"
	@echo "Running on http://localhost:8084"
	cd $(BOOK_SERVICE_DIR) && \
		export PYTHONPATH=$(BOOK_SERVICE_DIR) && \
		export BOOKSDB_CONFIG=./config/configuration.json && \
		poetry run uwsgi --ini books/api.ini

run-local-mcp-service:
	@echo "Starting MCP server locally (without Docker)..."
	@echo "Make sure you have dependencies installed"
	@echo "Running on http://localhost:3005"
	cd $(BOOK_SERVICE_DIR) && \
		export PYTHONPATH=$(BOOK_SERVICE_DIR) && \
		export PORT=3005 && \
		export HOST=0.0.0.0 && \
		export BOOKDB_CONFIG=./config/configuration.json && \
		poetry run python -m booksmcp.server

# ===================================================================
# TEST TARGETS - Local Docker Instances
# ===================================================================

run-test-book-service: build-test-book-service
	@echo "Starting book service test container..."
	@echo "Running on http://localhost:9999"
	-docker stop ${BOOK_TEST_IMAGE} 2>/dev/null || true
	-docker rm ${BOOK_TEST_IMAGE} 2>/dev/null || true
	docker run -d \
		--name ${BOOK_TEST_IMAGE} \
		-p 127.0.0.1:9999:8084 \
		${BOOK_TEST_TAG}
	@echo "✓ Book service test container running at http://localhost:9999"
	@echo "  Container name: ${BOOK_TEST_IMAGE}"
	@echo "  To view logs: make logs-test-book-service"
	@echo "  To stop: make stop-test-book-service"

run-test-mcp-service: build-test-mcp-service
	@echo "Starting MCP server test container..."
	@echo "Running on http://localhost:3005"
	-docker stop ${MCP_TEST_IMAGE} 2>/dev/null || true
	-docker rm ${MCP_TEST_IMAGE} 2>/dev/null || true
	docker run -d \
		--name ${MCP_TEST_IMAGE} \
		-p 127.0.0.1:3005:3005 \
		-e BOOKDB_CONFIG=/app/config/configuration.json \
		--add-host=host.docker.internal:host-gateway \
	    ${MCP_TEST_TAG}
	@echo "✓ MCP server test container running at http://localhost:3005"
	@echo "  Container name: ${MCP_TEST_IMAGE}"
	@echo "  To view logs: make logs-test-mcp-service"
	@echo "  To stop: make stop-test-mcp-service"

run-test-all: run-test-book-service run-test-mcp-service
	@echo "✓ All test containers running"
	@echo ""
	@echo "Services:"
	@echo "  Book Service: http://localhost:9999"
	@echo "  MCP Server:   http://localhost:3005"

stop-test-book-service:
	@echo "Stopping book service test container..."
	-docker stop ${BOOK_TEST_IMAGE} 2>/dev/null || true
	-docker rm ${BOOK_TEST_IMAGE} 2>/dev/null || true
	@echo "✓ Book service test container stopped"

stop-test-mcp-service:
	@echo "Stopping MCP server test container..."
	-docker stop ${MCP_TEST_IMAGE} 2>/dev/null || true
	-docker rm ${MCP_TEST_IMAGE} 2>/dev/null || true
	@echo "✓ MCP server test container stopped"

stop-test-all: stop-test-book-service stop-test-mcp-service
	@echo "✓ All test containers stopped"

logs-test-book-service:
	@echo "Viewing book service test container logs..."
	docker logs -f ${BOOK_TEST_IMAGE}

logs-test-mcp-service:
	@echo "Viewing MCP server test container logs..."
	docker logs -f ${MCP_TEST_IMAGE}

# ===================================================================
# TEST EXECUTION TARGETS
# ===================================================================

test: run-test-all
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Running tests against local Docker instances..."
	cd $(BOOK_SERVICE_DIR) && \
		export PYTHONPATH=$(BOOK_SERVICE_DIR) && \
		poetry run pytest test_books/test_docker_api.py -v
	cd $(BOOK_SERVICE_DIR) && \
		export PYTHONPATH=$(BOOK_SERVICE_DIR) && \
		poetry run pytest test_books/test_booksmcp.py -v
	@echo "✓ Tests completed"

test-book-service: run-test-book-service
	@echo "Waiting for book service to be ready..."
	@sleep 3
	@echo "Running book service tests..."
	cd $(BOOK_SERVICE_DIR) && \
		export PYTHONPATH=$(BOOK_SERVICE_DIR) && \
		poetry run pytest test_books/test_docker_api.py -v
		poetry run python test_books/generate_api_docs.py > ./api_test_commands.sh
	@echo "Test cUrl commands saved to ./api_test_commands.sh"

test-mcp-service: run-test-mcp-service
	@echo "Waiting for MCP server to be ready..."
	@sleep 3
	@echo "Running MCP server tests..."
	cd $(BOOK_SERVICE_DIR) && \
		export PYTHONPATH=$(BOOK_SERVICE_DIR) && \
		poetry run pytest test_books/test_booksmcp.py -v

test-local:
	@echo "Running tests locally with pytest (without Docker)..."
	cd $(BOOK_SERVICE_DIR) && \
		export PYTHONPATH=$(BOOK_SERVICE_DIR) && \
		poetry run pytest test_books/test_api_util.py -v

test-coverage:
	@echo "Running tests with coverage..."
	cd $(BOOK_SERVICE_DIR) && \
		export PYTHONPATH=$(BOOK_SERVICE_DIR) && \
		poetry run pytest test_books/test_api_util.py --cov=books --cov=booksmcp --cov=booksdb --cov-report=html --cov-report=term

test-bookdbtool:
	@echo "Running bookdbtool unit tests..."
	poetry run pytest test/ -v

test-bookdbtool-coverage:
	@echo "Running bookdbtool tests with coverage..."
	@echo "Note: Requires pytest-cov. Install with: poetry add --group dev pytest-cov"
	poetry run pytest test/ -v --cov=bookdbtool --cov-report=html --cov-report=term 2>/dev/null || \
		(echo "pytest-cov not installed. Running tests without coverage..." && poetry run pytest test/ -v)

# ===================================================================
# UTILITY TARGETS
# ===================================================================

stop-all:
	@echo "Stopping all running containers..."
	-docker stop books booksmcp-service ${BOOK_TEST_IMAGE} ${MCP_TEST_IMAGE} 2>/dev/null || true
	-docker rm books booksmcp-service ${BOOK_TEST_IMAGE} ${MCP_TEST_IMAGE} 2>/dev/null || true
	@echo "✓ All containers stopped"

logs-book-service:
	@echo "Viewing book service logs..."
	docker logs -f books

logs-mcp-service:
	@echo "Viewing MCP server logs..."
	docker logs -f booksmcp-service

clean:
	@echo "Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Python cache files cleaned"
	find . -type f -name "api_test_commands.sh" -delete 2>/dev/null || true
	@echo "✓ Test cUlr files removed"
	find . -type f -name "./tmp/*.png" -delete 2>/dev/null || true
	@echo "✓ Downloaded test image (png) files removed"


clean-test-records:
	@echo "Removing test records from database..."
	cd $(BOOK_SERVICE_DIR) && \
		PYTHONPATH=. \
		poetry run python test_books/clean_test_records.py
	@echo "✓ Test records cleaned"

clean-images:
	@echo "Removing all built Docker images..."
	-docker rmi $(BOOK_SERVICE_TAG) 2>/dev/null || true
	-docker rmi $(MCP_SERVICE_TAG) 2>/dev/null || true
	-docker rmi $(BOOK_TEST_TAG) 2>/dev/null || true
	-docker rmi $(MCP_TEST_TAG) 2>/dev/null || true
	@echo "✓ Docker images removed"

install-deps:
	@echo "Installing dependencies with poetry..."
	cd $(BOOK_SERVICE_DIR) && poetry install --no-root
	@echo "✓ Dependencies installed"

# ===================================================================
# PRODUCTION TARGETS
# ===================================================================

build-prod: build-all
	@echo "✓ Production images built"

deploy-prod: build-prod push-all
	@echo "✓ Production images built and pushed"
	@echo "  Run docker-compose up -d to deploy"
	@echo "  or re-pull and restart image in Dockge"

# ===================================================================
# DEVELOPMENT WORKFLOW TARGETS
# ===================================================================

dev-setup: install-deps
	@echo "Development environment setup complete"
	@echo ""
	@echo "To run services locally:"
	@echo "  make run-local-book-service"
	@echo "  make run-local-mcp-service"

dev-rebuild: clean build-all
	@echo "✓ Development rebuild complete"

# ===================================================================
# INFO TARGETS
# ===================================================================

info:
	@echo "==================================================================="
	@echo "Configuration Information"
	@echo "==================================================================="
	@echo "Hostname:               $(HOSTNAME)"
	@echo "Using Registry:         $(USE_REGISTRY)"
	@echo "Registry:               $(REGISTRY)"
	@echo ""
	@echo "Book Service Tag:       $(BOOK_SERVICE_TAG)"
	@echo "MCP Service Tag:        $(MCP_SERVICE_TAG)"
	@echo "Book Test Image Tag:    $(BOOK_TEST_TAG)"
	@echo "MCP Test Image Tag:     $(MCP_TEST_TAG)"
	@echo ""
	@echo "Book Service Dir:       $(BOOK_SERVICE_DIR)"
	@echo "Books Dir:              $(BOOKS_API_DIR)"
	@echo "MCP Dir:                $(MCP_DIR)"
	@echo ""
	@echo "Docker Images:"
	@docker images | grep -E "$(BOOK_SERVICE_IMAGE)|$(MCP_SERVICE_IMAGE)" || echo "  No images found"
	@echo ""
	@echo "Running Containers:"
	@docker ps --filter name=books --filter name=booksmcp || echo "  No containers running"
	@echo "==================================================================="
