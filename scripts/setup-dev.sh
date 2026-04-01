#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
  echo -e "${BLUE}ℹ ${1}${NC}"
}

log_success() {
  echo -e "${GREEN}✓ ${1}${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠ ${1}${NC}"
}

log_error() {
  echo -e "${RED}✗ ${1}${NC}"
}

check_command() {
  if command -v "$1" &> /dev/null; then
    log_success "$1 is installed"
    return 0
  else
    log_error "$1 is not installed"
    return 1
  fi
}

# Banner
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Food Delivery - Development Setup     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

MISSING_DEPS=0

if ! check_command "python3"; then
  log_error "Python 3 is required. Install from https://www.python.org/"
  MISSING_DEPS=1
fi

if ! check_command "docker"; then
  log_error "Docker is required. Install from https://www.docker.com/"
  MISSING_DEPS=1
fi

if ! check_command "docker-compose"; then
  log_warning "docker-compose not found as standalone. Checking docker compose..."
  if ! docker compose version &> /dev/null; then
    log_error "Docker Compose is required"
    MISSING_DEPS=1
  else
    log_success "Docker Compose (plugin) is available"
  fi
else
  log_success "docker-compose is installed"
fi

if ! check_command "git"; then
  log_error "Git is required"
  MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
  log_error "Please install missing dependencies and try again"
  exit 1
fi

# Resolve Docker Compose command (standalone binary or Docker plugin)
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
  DOCKER_COMPOSE_CMD="docker compose"
fi
log_info "Using Docker Compose command: ${DOCKER_COMPOSE_CMD}"

# Check Python version
log_info "Checking Python version..."
REQUIRED_VERSION="3.12"
PYTHON_BIN="python3"
PYTHON_VERSION=$($PYTHON_BIN --version | cut -d' ' -f2)

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
  if command -v python3.12 &> /dev/null; then
    PYTHON_BIN="python3.12"
    PYTHON_VERSION=$($PYTHON_BIN --version | cut -d' ' -f2)
    log_warning "python3 is < $REQUIRED_VERSION; using $PYTHON_BIN for setup checks."
  elif [ -x "/opt/homebrew/opt/python@3.12/bin/python3" ]; then
    export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_warning "python3 is < $REQUIRED_VERSION; using Homebrew python@3.12 for setup checks."
  fi
fi

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" == "$REQUIRED_VERSION" ]]; then
  log_success "Python $PYTHON_VERSION is compatible - required: $REQUIRED_VERSION+"
else
  log_error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
  exit 1
fi

# Install uv if not present
if ! check_command "uv"; then
  log_info "Installing uv (Python package manager)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$PATH"
  log_success "uv installed successfully"
fi

# Create .env file
log_info "Setting up environment variables..."
if [ ! -f ".env" ]; then
  cp .env.example .env
  log_success "Created .env file from .env.example"
  log_warning "Please update .env with your local configuration"
else
  log_warning ".env file already exists, skipping..."
fi

# Install Python dependencies
log_info "Installing Python dependencies with uv..."
uv sync --all-extras --all-packages
log_success "Python dependencies installed"

# Install pre-commit hooks
log_info "Installing pre-commit hooks..."
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
log_success "Pre-commit hooks installed"

# Create necessary directories
log_info "Creating project directories..."
mkdir -p services shared infrastructure/postgres infrastructure/kafka tests/integration tests/e2e
log_success "Directories created"

# Start Docker infrastructure
log_info "Starting Docker infrastructure..."
log_warning "This will start PostgreSQL, Redis, Kafka, Zookeeper, Kafka UI, and pgAdmin"
read -p "Do you want to start infrastructure now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  if [ -f "infrastructure/docker-compose.yml" ]; then
    $DOCKER_COMPOSE_CMD --env-file .env -f infrastructure/docker-compose.yml up -d
    log_success "Infrastructure started"

    log_info "Waiting for services to be healthy..."
    sleep 10

    # Check if services are running
    if $DOCKER_COMPOSE_CMD -f infrastructure/docker-compose.yml ps | grep -q "Up"; then
      log_success "Services are running"
    else
      log_warning "Some services may not be running. Check with: $DOCKER_COMPOSE_CMD -f infrastructure/docker-compose.yml ps"
    fi
  else
    log_warning "docker-compose.yml not found. Will create it in Phase 0.2"
  fi
else
  log_info "Skipping infrastructure startup. Run 'make up' when ready."
fi

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup Complete! 🎉                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Update .env file with your configuration"
echo "  2. Start infrastructure: ${GREEN}make up${NC}"
echo "  3. Check service health: ${GREEN}make health${NC}"
echo "  4. Run tests: ${GREEN}make test${NC}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  make help          - Show all available commands"
echo "  make dev-install   - Reinstall dev dependencies"
echo "  make format        - Format code"
echo "  make lint          - Run linters"
echo "  make test-cov      - Run tests with coverage"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  README.md          - Project overview"
echo "  CLAUDE.md          - AI agent guidance"
echo "  CONTRIBUTING.md    - Contribution guidelines"
echo "  PROGRESS.md        - Development progress"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
