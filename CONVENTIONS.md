# Project Conventions & Documentation Rules

## Documentation
1. **Documentation Updates**: Whenever you modify API routes, update status flows, add validation, or alter backend services, update `README.md` to reflect the changes.
2. **Current Capabilities Sync**: Keep the "What is already implemented" and "What is missing or incomplete" sections in `README.md` accurate after every code change.
   > Note: this file is loaded read-only and is not always enough on its own to trigger doc updates — prompts that change routes, status flows, or services should explicitly include "update README.md per CONVENTIONS.md" as a numbered step.

## WebSocket Message Contract
All `/ws/analyze` messages from backend to frontend use this shape:
```json
{
  "status": "uploading" | "extracting" | "analyzing" | "synthesizing" | "completed" | "error",
  "progress": 0-100,
  "message": "optional human-readable detail, required when status is 'error'"
}
```
- The field is always `status` — do not also check `msg.phase` or fall back to `msg.message` for the phase value.
- Frontend listeners should switch on `msg.status` directly.

## Canonical Processing Phases
The full, ordered list of phases used across frontend and backend:
```
idle -> uploading -> extracting -> analyzing -> synthesizing -> completed
                                                               -> error
```
- Use these exact strings everywhere (state values, WebSocket payloads, UI labels). Don't introduce new phase names or reorder without updating this list.

## Library / API Pins
- **react-toastify**: use string literals for position, e.g. `toast.error(msg, { position: "top-right" })`. Do NOT use `toast.POSITION.TOP_RIGHT` (deprecated).
- (Add further pins here as they come up — package name, the deprecated/wrong pattern to avoid, and the correct one.)

## Backend Error & Cleanup Pattern
- Any upload/processing failure path must delete temporary/uploaded files before raising.
- Raise `HTTPException` with a JSON body shaped as `{"detail": "<clear message>"}`.
- Validation (filename sanitization, extension/size limits, corruption checks) happens before any file write is considered final.

## File & Folder Layout
- Backend business logic / processing helpers: `backend/app/services/`
- Backend routes/entrypoints: `backend/app/main.py`
- Backend tests: `backend/tests/`
- Frontend components: `frontend/src/components/`
- Frontend top-level app/state: `frontend/src/App.jsx`
- (Fill in additional paths as the project grows — new service modules, new component subfolders, etc.)