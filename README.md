# testy-zephyr-xml-importer (harness scaffold)

This repo is a scaffold prepared for a **3-phase autonomous loop** (Planner → Worker → Judge) to implement a TestY plugin that imports **Zephyr Scale XML export**.

Original TestY repo: https://gitlab-pub.yadro.com/testy/testy
Plugin examples repo: https://gitlab-pub.yadro.com/testy/plugin-example

Start here:
- `.agent/PROJECT.md` — edit per project/environment
- `.agent/queue.md` — backlog (Judge marks done)
- `docs/spec.md` — concise specification
- `scripts/codex_loop_3phase.sh` — optional loop runner

## Local dev
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

See `docs/dev.md`.
