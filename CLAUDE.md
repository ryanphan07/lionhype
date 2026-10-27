# LionHype: agent instructions

**Project:** local-first app that turns lion dance videos into humorous, time-synced AI commentary with TTS audio. FastAPI + OpenCV + an OpenAI-compatible multimodal LLM (local llama-server) + edge-tts; React/Vite frontend with WebSocket progress.

**Goal:** an honest, demoable, resume-ready MVP. This is the last project going on the owner's resume before recruiting starts, and speed matters. Do not add features beyond `docs/AUDIT.md` and `TASKS.md` without asking.

**Rules**
- Follow `CONVENTIONS.md`. Never read or edit `.history/`, `node_modules/`, `venv/`, `uploads/`.
- Be concise: no recaps, never paste large files back, plan in 10 lines or fewer and then proceed.
- Run tests before each commit (commands are in `CONVENTIONS.md`). One logical change per commit. Never push.

**Workflow**
The owner plans in a separate chat that cannot see this repo, then runs you one scoped session at a time. Session prompts may contain wrong file names or assumptions. Verify against the code and adapt minimally. Stop and ask only if the fix would change a public API shape or delete files the prompt didn't mention. Record every deviation in the handoff.

**End of every session:** batch any doc updates per `CONVENTIONS.md`, then overwrite `docs/HANDOFF.md` (30 lines max) with:
1. Done: what changed, by file
2. Decisions and deviations from the prompt
3. Test / lint / build results (pass or fail, counts)
4. Not verified, needs manual testing (what to click or run)
5. Open issues and risks (file:line)
6. Suggested next session

Do not print the handoff in your reply. Just say "handoff written".