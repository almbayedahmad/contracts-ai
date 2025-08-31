# contracts-ai (Modular Monolith)

## Quickstart
```bash
make setup
make run-api
make run-ui
```

## Structure
- backend/app: FastAPI app (api, core, domain, application, infrastructure, schemas)
- frontend: Streamlit UI
- data: temp + outputs
- docs: ADRs, guides, runbooks, references
- tests: backend tests (unit, integration, e2e)

## Notes
- Configure via `.env` (see `.env.example`)
- Structured JSON logging + unified error middleware included.
- Add routers under `backend/app/api/v1` and include in `main.py`.
