#!/usr/bin/env bash
# A Reboot todo app after its first build: one commit on main, the
# accepted design recorded, no workflow chosen in AGENTS.md.
set -euo pipefail
mkdir -p api/todo/v1 tests design backend/src/servicers
printf 'dev run --application-name=todo\ngenerate api/ --python=backend/api\n' > .rbtrc
cat > AGENTS.md <<'MD'
# Todo — map for a coding agent

A Reboot app (Python backend, React web app).

## Run, test, deploy

- **Test:** `uv run pytest`.
- **Deploy:** `scripts/deploy.sh`, with the plugin's `deploy` skill.
- **Workflow:** not chosen yet. At the first change after the first
  build the agent asks whether changes go straight onto `main` or onto
  a branch each, and writes the answer here.
MD
cat > api/todo/v1/todo.py <<'PY'
from reboot.api import API, Field, Methods, Model, Reader, Type, Writer


class TodoState(Model):
    title: str = Field(tag=1, default="", description="What needs doing.")
    done: bool = Field(tag=2, default=False, description="Whether it is finished.")


api = API(
    Todo=Type(
        state=TodoState,
        description="One thing a user wants to get done.",
        methods=Methods(
            get=Reader(request=None, response=TodoState, description="Read the todo.", mcp=None),
            complete=Writer(request=None, response=None, description="Mark the todo finished.", mcp=None),
        ),
    ),
)
PY
cat > tests/todos.feature <<'FEATURE'
Feature: Todos
  Rule: A todo can be completed
    Scenario: Completing a todo
      Given a todo "Buy milk"
      When it is completed
      Then it is done
FEATURE
echo '{"accepted_at": "2026-10-01"}' > design/accepted.json
git init -q -b main
git -c user.email=dev@example.com -c user.name=Dev add -A
git -c user.email=dev@example.com -c user.name=Dev commit -q -m "Design accepted: Todo list"
git remote add origin https://github.com/example/todo.git
