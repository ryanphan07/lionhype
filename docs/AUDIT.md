# LionHype audit (2026-10-27)

Baseline: `pytest backend/tests -q` = 20 passed (9 test_main, 11 test_jobs). `npm run lint` = FAIL, 3 errors. `npm run build` = FAIL. Real-footage run not done (llama-server was not reachable at :8080, no sample clip in video_input/).
Tags: BLOCKS-MVP / SHOULD-FIX / IGNORE. Line refs: `app/main.py` = backend/app/main.py.

## Your suspicions

| Suspicion | Verdict | Evidence | Tag |
|---|---|---|---|
| backend/main.py is a stale duplicate | CONFIRMED | backend/main.py:1-95 is an older app/main.py with no validation. tests/test_main.py:12,92 import `backend.main`, so route tests cover the dead copy | SHOULD-FIX |
| video_id="default" | CONFIRMED | commentary.py:31; ws never passes job_id (app/main.py:112). Files are `audio/default/audio_<ts>_<texthash>.mp3`, so collisions need the same ts and text. Real harm: no per-job folder, no cleanup | SHOULD-FIX |
| TTS audio dir is cwd-relative | REFUTED | tts.py:46 uses absolute `settings.UPLOAD_DIR` (config.py:26). Only the dead fallback is cwd-relative (commentary.py:101-105) | IGNORE |
| Audio URL hardcodes localhost:8000 | PARTLY REFUTED | tts.py:66 uses `settings.PUBLIC_BASE_URL` (config.py:25, default localhost:8000). Fine for MVP. `.env` is cwd-relative (config.py:7), so it loads only when started from backend/ | IGNORE |
| ws takes client video_path | CONFIRMED | app/main.py:107, and upload returns the server absolute path (app/main.py:65), so any readable path can be opened by OpenCV | BLOCKS-MVP |
| ws job_id never sent by frontend | CONFIRMED | app/main.py:102 makes `job_id` a required query param. Probe: `/ws/analyze` without it is rejected (WebSocketDisconnect). App.jsx:29 never sends it | BLOCKS-MVP |
| frontend uses ws://backend:8000 | CONFIRMED | App.jsx:29, and `http://backend:8000` at App.jsx:99. "backend" only resolves inside the Docker network, not in the browser, so it fails natively and in Docker | BLOCKS-MVP |
| /generate passes video_url as id | CONFIRMED | app/main.py:137-148 -> commentary.py:97-115 looks for `frames/<url>` (path traversal), builds an unused list, then opens nonexistent `frames/video.mp4`. Probe: returns 202, job ends "completed" with 0 quips | SHOULD-FIX (delete) |
| job_tracker defined after use | REFUTED as a bug | app/main.py:143 is resolved at call time. Real issue: no endpoint reads it, it is unbounded, and JobStore (jobs.py) is the intended replacement | IGNORE |
| llm.py sends frames as JSON text | CONFIRMED | llm.py:68-73 `json.dumps({"frames": frames})` in a text message. The model never sees an image, so output is hallucinated | BLOCKS-MVP |
| llm.py own Settings() | CONFIRMED | llm.py:16, tts.py:17 (violates CONVENTIONS single settings object) | SHOULD-FIX |
| 30s LLM timeout | CONFIRMED | config.py:13 used at llm.py:46. A 35B model with many images will exceed it, then retry x3 | BLOCKS-MVP |
| Frames squashed to 224x224 | CONFIRMED | video_processor.py:25: no aspect ratio, too small to see dancers | BLOCKS-MVP |
| Upload extracts frames, pipeline repeats | CONFIRMED | app/main.py:64 -> video_processor.py:94-106 (async def running sync OpenCV, blocks the event loop). Results are never used; commentary.py:42 extracts again. 1s interval there vs 2s here | SHOULD-FIX |
| Presigned endpoint is dead boto3 | CONFIRMED | app/main.py:78-99, bucket 'your-bucket-name' (:89). `import boto3` at :8 crashes startup if boto3 is missing | BLOCKS-MVP (remove) |
| No CORS middleware | CONFIRMED | None in app/main.py. Probe: OPTIONS /api/upload with Origin :5173 gives 405 and no allow-origin header, so browser uploads from Vite fail | BLOCKS-MVP |
| STATE.md starts with chat text | CONFIRMED | STATE.md:1-4 (`[cite: 1, 3]`, stray ```markdown fence, never closed) | SHOULD-FIX |
| README cut off | CONFIRMED | README.md:31 ends inside an open ```bash fence. No frontend steps, routes, or limitations | SHOULD-FIX |
| STATE.md claims Docker/.env | CONFIRMED | STATE.md:103. docker-compose.yml has no env_file/.env, no LLM host mapping, and frontend/Dockerfile uses node:18 with Vite 8 (likely too old, untested) | SHOULD-FIX (docs) |

## Issues you did not list

- BLOCKS-MVP: API does not match CONVENTIONS contract. Upload returns `video_id` (app/main.py:65), not `job_id`; no `GET /api/jobs/{id}`; ws path is `/ws/analyze` (:101); statuses are `"processing"` (:111-114), which App.jsx:42-65 ignores. JobStore (jobs.py) is complete but wired to nothing; only test_jobs.py uses it.
- BLOCKS-MVP: progress is fake. ws sends "extracting/analyzing/synthesizing" only after the whole pipeline finished (app/main.py:112-114); `progress_cb` is never passed.
- BLOCKS-MVP: `react-toastify` imported (App.jsx:4-5) but missing from package.json and node_modules, so build and dev fail. `lucide-react` is listed but unused.
- BLOCKS-MVP: lint fails: unused `React` (App.jsx:1, VideoPlayer.jsx:1), unused `errorMessage` (App.jsx:12).
- BLOCKS-MVP: requirements.txt lacks `pydantic-settings` (config.py:3), so a fresh install fails on import. It lists `boto3` and `pytest*` as runtime deps and pins nothing. Probe: `uvicorn app.main:app` fails here with `No module named 'boto3'`; with boto3 stubbed it starts and serves.
- BLOCKS-MVP: silent fakes. tts.py:59-64 write the bytes `fake-audio` into an .mp3 and return a URL; llm.py:92-100 swallows every LLM error and returns canned "highlight reel energy" text. The UI reports completed with fake output, and commentary.py:91 `all_failed` can never fire.
- BLOCKS-MVP: playback. VideoPlayer.jsx:11-22 never plays quip 0, ignores seeks and pause, and starts a new `Audio` per quip with no overlap control. Clip durations are unknown to the server, so non-overlap is impossible today.
- BLOCKS-MVP: no 90s duration check; only extension and 100MB (video_processor.py:46-47,60-72). `file.filename` None crashes `validate_upload_metadata` (app/main.py:52).
- SHOULD-FIX: all of uploads/ is served statically (app/main.py:21), including raw videos and frames (violates CONVENTIONS). Video is saved under the client filename (:38), so same-name uploads overwrite each other.
- SHOULD-FIX: cleanup gaps. frame_dir is created before validation (app/main.py:40) and survives 400s; the `except HTTPException: raise` (:66) skips cleanup.
- SHOULD-FIX: error handler returns `str(exc)` to clients and logs nothing (app/main.py:24-26); ws also sends `str(exc)` (:124). app/main.py has no logging setup (root main.py did).
- SHOULD-FIX: App.jsx:77-87 `onclose` reads a stale `processingStatus`, so it reconnects forever, including after unmount; no videos path survives reconnect. App.css (184 lines) is unused Vite template.
- SHOULD-FIX: test quality. test_main.py:132,152 use a sync lambda for TTS, which the code awaits, so every clip silently fails and the tests still pass. ws test (:88-104) asserts the stale protocol. conftest.py writes an unused test_video.mp4 into cwd. No tests for llm.py, tts success path, upload route, or validators.
- SHOULD-FIX: 20 `.history/` files and repomix-output.xml are tracked in git despite .gitignore (`.history/,` has a typo). Remove from the index before publishing the repo.
- SHOULD-FIX: jobs.py:34-35 `time.time()` as field default is frozen at import; use default_factory.
- IGNORE: mcp_server.py is a SyntaxError (escaped `\"\"\"` at :12,:19), needs the unlisted `mcp` package, and is not integrated. Not part of the MVP; suggest removing it and its STATE.md section (needs your OK). Also dead: `generate_commentary`/`EventTimeline` (llm.py), `generate_audio_commentary` (tts.py), `CommentaryResponse.video_url`, Docker files.

## Plan (6 sessions)

1. M, make it build and run: add react-toastify, fix lint, fix requirements (add pydantic-settings, drop boto3, split dev deps), remove presigned endpoint, add CORS and a `VITE_API_URL` setting, `.env.example`, untrack .history/repomix, delete backend/main.py and retarget tests.
2. L, job API per CONVENTIONS: upload -> job_id + background task using JobStore, `WS /ws/analyze/{job_id}`, `GET /api/jobs/{id}`, server-owned paths, 90s limit, extract frames once, cleanup on failure, audio-only static mount, generic errors + logging; drop /generate and /mock. Route tests with only LLM/TTS mocked.
3. M, real vision LLM: image_url parts, shared settings, aspect-preserving resize and a frame cap, longer timeout, new prompt, parse and validate output, fail loudly instead of faking. Verify against live llama-server on a real clip.
4. L, TTS and synced playback: remove fake audio, measure clip durations, schedule non-overlapping quips on the server, rewrite VideoPlayer (quip 0, seek, pause, queue), fix ws client per contract.
5. M, end-to-end on 3 real clips, fix what breaks, tune frame interval/prompt, record demo GIF.
6. S, docs: rewrite README (architecture, quickstart, routes, limitations), STATE.md, TASKS.md; mark Docker as untested.
