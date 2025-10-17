Union Action Workflow Integration API

Production-ready FastAPI service providing the workflow endpoints consumed by `chatops-agent`.

Quickstart

```bash
# From union-action directory
pip install -r requirements.txt

# Run API
uvicorn xsrc.main:app --host 0.0.0.0 --port 8000 --reload

# Health
curl http://localhost:8000/health
```

Environment

- `TYPEFORM_API_TOKEN`: Token for Typeform (or leave unset for stub)
- `PYDANTIC_AI_MODEL`: Optional, model hint for AI transformer
- `OPENAI_API_KEY`: Optional, if using the OpenAI-backed transformer
- `LOG_LEVEL`: INFO|DEBUG|WARNING (default INFO)
- `LOG_FORMAT`: json|console (default json)

Docker

```bash
docker build -t union-action:dev .
docker run --rm -p 8000:8000 --env-file .env union-action:dev
```

Compose (dev hot reload)

```bash
cp .env.example .env
docker compose up --build
```

Endpoints

- `GET /health` – basic health
- `POST /escalate` – escalate complaint to ethics (see tests for contract)
- `POST /deploy` – create KOERS survey (see tests for contract)

Notes

- Code lives in `xsrc/`. Uvicorn app is `xsrc.main:app`.
- Tests are under `tests/` and include contract, integration, and unit tests.


