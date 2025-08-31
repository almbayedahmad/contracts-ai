# Migration Notes

- Original project copied into `legacy/` for safe reference.
- Streamlit UI migrated from: `/mnt/data/work_a99a9a2e/Contracts_v_full/app/ui_streamlit.py` → `frontend/ui_streamlit.py`.
- FastAPI scaffold created in `backend/app`. Include your routers and handlers.
- Update requirements as needed and move domain logic from legacy into `backend/app/domain`.
- Adjust imports and gradually delete migrated files from `legacy/` once covered by tests.
