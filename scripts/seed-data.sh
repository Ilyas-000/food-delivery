#!/usr/bin/env bash

set -euo pipefail

echo "Loading seed data..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEED_SCRIPT="$PROJECT_ROOT/scripts/seed-data.py"
RAN_ANY=0

if [ -f "$SEED_SCRIPT" ]; then
  echo "-> Running repository seed script: scripts/seed-data.py"
  python "$SEED_SCRIPT"
  RAN_ANY=1
fi

while IFS= read -r script_path; do
  rel_path="${script_path#"$PROJECT_ROOT"/}"
  echo "-> Running service seed script: $rel_path"

  case "$script_path" in
    *.py)
      python "$script_path"
      ;;
    *)
      bash "$script_path"
      ;;
  esac

  RAN_ANY=1
done < <(find "$PROJECT_ROOT/services" -maxdepth 4 -type f \( -name "seed-data.sh" -o -name "seed.py" \) | sort)

if [ "$RAN_ANY" -eq 0 ]; then
  echo "No seed scripts found in repository or services."
  echo "Current data bootstrap is migration-first; add service seed scripts when fixtures are needed."
fi

echo "Seed loading complete."
