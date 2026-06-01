#!/usr/bin/env bash

set -uo pipefail

mode="${1:-}"
workspace="${2:-/workspace}"

if [[ -z "$mode" ]]; then
  echo "Usage: $0 <unit|integration|e2e|unit+integration|all|coverage> [workspace]" >&2
  exit 1
fi

cd "$workspace"

total=0
passed=0
failed=0
failures=()

print_banner() {
  local subject="$1"
  local scope="$2"
  local blue='\033[0;34m'
  local red='\033[0;31m'
  local nc='\033[0m'
  local color="$blue"

  if [[ "$scope" == FAILED* ]]; then
    color="$red"
  fi

  printf "\n${color}============================================================${nc}\n"
  printf "${color}==  %s | %s${nc}\n" "$subject" "$scope"
  printf "${color}============================================================${nc}\n\n"
}

require_test_databases() {
  # Integration tests skip themselves when their *_TEST_DATABASE_URL is unset.
  # Inside the matrix the URLs always come from the test-runner environment, so a
  # missing one means a broken setup (e.g. reused volume without bootstrap) that
  # would otherwise hide as a silent skip. Fail loudly instead.
  local -a missing=()
  local var
  for var in \
    USER_SERVICE_TEST_DATABASE_URL \
    RESTAURANT_SERVICE_TEST_DATABASE_URL \
    ORDER_SERVICE_TEST_DATABASE_URL \
    DELIVERY_SERVICE_TEST_DATABASE_URL \
    REVIEW_SERVICE_TEST_DATABASE_URL; do
    if [[ -z "${!var:-}" ]]; then
      missing+=("$var")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "ERROR: integration matrix requires test database URLs to be set." >&2
    printf '  missing: %s\n' "${missing[*]}" >&2
    echo "Run 'make test-deps-up' to bootstrap test databases, or check the" >&2
    echo "test-runner environment in infrastructure/docker-compose.yml." >&2
    exit 1
  fi
}

has_test_files() {
  local path

  for path in "$@"; do
    if find "$path" -type f -name "test_*.py" 2>/dev/null | grep -q .; then
      return 0
    fi
  done

  return 1
}

run_pytest() {
  local label="$1"
  local subject="$2"
  local scope="$3"
  local workdir="$4"
  shift 4

  total=$((total + 1))
  print_banner "$subject" "$scope"
  echo "Running ${label}..."

  # Keep pytest cache off the bind-mounted workspace: flock deadlocks (EDEADLK)
  # on macOS bind mounts. /tmp is the container's own fs, where locking works.
  local cache_dir="/tmp/pytest-cache/${subject}"

  # -ra surfaces skip/xfail reasons in the summary so unexpected skips are visible.
  if (cd "$workdir" && /opt/venv/bin/pytest -ra -o cache_dir="$cache_dir" "$@"); then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    failures+=("$label")
  fi
}

run_repo_tests() {
  local -a repo_paths=()

  case "$mode" in
    unit)
      [[ -d tests/unit ]] && repo_paths+=(tests/unit)
      ;;
    integration)
      [[ -d tests/integration ]] && repo_paths+=(tests/integration)
      ;;
    e2e)
      [[ -d tests/e2e ]] && repo_paths+=(tests/e2e)
      ;;
    unit+integration)
      [[ -d tests/unit ]] && repo_paths+=(tests/unit)
      [[ -d tests/integration ]] && repo_paths+=(tests/integration)
      ;;
    all)
      [[ -d tests ]] && repo_paths+=(tests)
      ;;
    coverage)
      return 0
      ;;
    *)
      echo "Unknown test matrix mode: ${mode}" >&2
      exit 1
      ;;
  esac

  if [[ ${#repo_paths[@]} -gt 0 ]] && has_test_files "${repo_paths[@]}"; then
    run_pytest \
      "repo ${mode} tests in ./tests" \
      "REPO" \
      "$mode" \
      "$workspace" \
      "${repo_paths[@]}"
  fi
}

run_service_tests() {
  local svc

  for svc in services/*; do
    [[ -d "$svc" ]] || continue

    local label=""
    local -a paths=()
    local -a full_paths=()

    case "$mode" in
      unit)
        [[ -d "$svc/tests/unit" ]] && paths+=(tests/unit)
        label="unit tests in ${svc}"
        ;;
      integration)
        [[ -d "$svc/tests/integration" ]] && paths+=(tests/integration)
        label="integration tests in ${svc}"
        ;;
      e2e)
        [[ -d "$svc/tests/e2e" ]] && paths+=(tests/e2e)
        label="e2e tests in ${svc}"
        ;;
      unit+integration)
        [[ -d "$svc/tests/unit" ]] && paths+=(tests/unit)
        [[ -d "$svc/tests/integration" ]] && paths+=(tests/integration)
        label="unit+integration tests in ${svc}"
        ;;
      all|coverage)
        [[ -d "$svc/tests" ]] && paths+=(tests)
        label="all tests in ${svc}"
        ;;
      *)
        echo "Unknown test matrix mode: ${mode}" >&2
        exit 1
        ;;
    esac

    if [[ ${#paths[@]} -gt 0 ]]; then
      local rel_path
      for rel_path in "${paths[@]}"; do
        full_paths+=("$workspace/$svc/$rel_path")
      done
    fi

    if [[ ${#paths[@]} -gt 0 ]] && has_test_files "${full_paths[@]}"; then
      run_pytest \
        "$label" \
        "$(basename "$svc")" \
        "$mode" \
        "$workspace/$svc" \
        -c pyproject.toml \
        "${paths[@]}"
    fi
  done
}

print_summary() {
  echo
  print_banner "MATRIX SUMMARY" "completed"
  printf '✅ Executed:    %s\n' "$total"
  printf '✅ Passed:      %s\n' "$passed"
  printf '❌ Failed:      %s\n' "$failed"

  if [[ "$failed" -gt 0 ]]; then
    echo
    print_banner "FAILED TARGETS" "see list below"
    local label
    for label in "${failures[@]}"; do
      printf -- '- %s\n' "$label"
    done
  fi
}

case "$mode" in
  integration | unit+integration | all | coverage)
    require_test_databases
    ;;
esac

run_repo_tests
run_service_tests
print_summary

if [[ "$failed" -gt 0 ]]; then
  exit 1
fi
