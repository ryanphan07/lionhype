# LionHype: agent instructions

**Project:** local-first app that turns lion dance videos into humorous, time-synced AI commentary with TTS audio. FastAPI backend (OpenCV frame extraction, OpenAI-compatible multimodal LLM client, edge-tts) + React/Vite frontend with WebSocket progress. The LLM is a local Qwen3.6-35B-A3B served by llama-server (multimodal via --mmproj) at http://127.0.0.1:8080/v1. For the MVP it runs natively on Windows, no Docker.

**Why this matters:** this is the last project going on the owner's resume before recruiting starts, and they want to begin applying ASAP, so speed matters. The goal is a credible, demoable, honest resume-ready MVP, not a finished product: upload a clip (90s or less), see progress, get real vision-LLM commentary played in sync with non-overlapping TTS audio, runnable locally in a few commands, with a clean README and demo GIF. Do not add features beyond docs/AUDIT.md and TASKS.md without asking.

**Code quality warning:** most of the existing code was written by Aider with a weak local Qwen model and only has mock-based tests. It has never run end to end on real footage. Verify claims against the code instead of trusting STATE.md, README.md or old comments.

**Rules**
- Follow CONVENTIONS.md. Never read or edit .history/, node_modules/, venv/, uploads/.
- Be concise: no recaps, never paste large files back, plan in 10 lines or fewer and then proceed.
- Run tests before each commit (commands are in CONVENTIONS.md). One logical change per commit. Never push.

**Workflow:** the owner plans in a separate chat that cannot see this repo, then runs you one scoped session at a time. Session prompts may contain wrong file names or assumptions. Verify against the code and adapt minimally. Stop and ask only if the fix would change a public API shape or delete files the prompt didn't mention. Record every deviation in the handoff.

**End of every session:** batch any doc updates per CONVENTIONS.md, then overwrite docs/HANDOFF.md (30 lines max) with:
1. Done: what changed, by file
2. Decisions and deviations from the prompt
3. Test / lint / build results (pass or fail, counts)
4. Not verified, needs manual testing (what to click or run)
5. Open issues and risks (file:line)
6. Suggested next session
Do not print the handoff in your reply. Just say "handoff written".