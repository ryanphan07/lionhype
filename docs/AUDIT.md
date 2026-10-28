# LionHype audit 3 (2026-10-28)

Third full audit, after sessions 7, 7b and 9. Read every service, the job API, both frontend files and the tests again, re-ran tests/lint/build/audit, and probed the SDK and server behavior directly. No live LLM run this time: llama-server, uvicorn and Vite were all stopped. Audit 2 (kept below as history) still holds for everything not mentioned here.
Tags: BLOCKS-DEMO / SHOULD-FIX / POLISH / INFO. Line refs are relative to `backend/app/` unless a path is given.

## Baseline

| Check | Result |
|---|---|
| `pytest backend/tests -q` | 95 passed, 10.5 s (was 3 s: see N5; fixed in session 11) |
| `npm run lint` / `build` / `audit --omit=dev` | clean / ok / 0 vulnerabilities |
| Working tree | clean except ignored files; HEAD `4faf1b7` |
| Services | none running; llama-server not reachable, so F1-F3 fixes are tested but not re-run live |
| Fresh-venv install | not done (requirements are pinned and `websockets` added, but never built from scratch) |

## Goal check

| Goal | Status | Notes |
|---|---|---|
| Upload a clip, see progress | Done in code | Browser check still pending since session 6 |
| Real vision-LLM commentary | Done; quality on real motion unjudged | Last live run: 44.7 s per 10 s window (9B) |
| Synced, non-overlapping TTS | Done; timing recalibrated, not re-run live | 4.5 s gap vs measured 4.5 s for an 8-word line |
| Long clips (10+ min, D1) | Limits allow it; **the system is not yet robust for it** | N1, N2, N3, N6 below. 60 windows x 45 s is about 45 min on the 9B |
| Local, few commands | Mostly | Root README exists; needs llama-server, internet for TTS, a fresh-venv check |
| README + demo GIF, LICENSE, tag | README done; GIF, LICENSE, tag missing | |
| Honest (no fake output) | Yes | Enforced end to end |

## New findings

| # | Tag | Finding | Evidence |
|---|---|---|---|
| N1 | PARTLY FIXED (session 11: polling fallback; refresh-resume open) | **The browser gives up after about 25 s without a WebSocket and cannot recover the job.** Reconnect is 5 tries at 1, 2, 4, 8, 10 s, then "Lost connection" and the job id is dropped. There is no polling fallback and the id is not persisted, so a laptop sleep or tab throttle during a 45-minute job loses a result the server still finishes. The video is a blob URL, so a reload loses the file too | `frontend/src/App.jsx:10-11,104-115` |
| N2 | FIXED (session 11) | **The OpenAI SDK silently retries.** `AsyncOpenAI` defaults to `max_retries=2` (verified: 2). A hung window can take 3 x 300 s = 15 min to fail, and a down server retries with backoff. This contradicts the docstring ("no retry: a slow model would double the wait") | `services/llm.py:18-22,134-137` |
| N3 | SHOULD-FIX (long clips) | **All-or-nothing job.** Nothing is returned until every window and every TTS clip is done, and one failed window fails the job after up to 45 minutes of work. No checkpointing and a restart loses it. Needs a design decision (DECISIONS D4) | `services/commentary.py:83-105,110-135` |
| N4 | FIXED (session 11) | **Every failure shows the same message**, "Commentary generation failed": LLM server down, unusable JSON, unreadable video and TTS bugs are indistinguishable to the user and in a demo. Safe categories ("The AI model is not reachable", "The model returned unusable output") would help without leaking details | `services/pipeline.py:59-65` |
| N5 | FIXED (session 11) | **A test hits the real network.** `test_second_upload_while_a_job_runs_is_rejected` completes a real upload without the `fake_ai` fixture, so the pipeline tries 127.0.0.1:8080 (7.7 s of SDK retries now; it would run a real analysis if llama-server were up). Non-deterministic and slow | `backend/tests/test_api.py` (last test) |
| N6 | FIXED (session 11) | **The one-job guard can wedge.** `has_active()` counts any non-terminal job forever. If a pipeline never reaches `complete`/`fail` (hang outside the LLM timeout, a crash that is not an `Exception`), every upload returns 409 until the server restarts | `services/jobs.py` `has_active` |
| N7 | POLISH | **Long clips will repeat jokes.** Only the last two quip texts carry across windows, and the model's own `seen` summary is logged but discarded. Over 60 windows expect "blue lion bows" repeatedly. Passing the last 2-3 `seen` lines is a small prompt change | `services/llm.py:148`, `services/commentary.py:106-108` |
| N8 | POLISH | **Throughput levers for long clips, none tried:** fewer or smaller frames (`FRAMES_PER_WINDOW`, `FRAME_WIDTH` 640), longer windows (20 s), fewer quips, and parallel windows with `llama-server -np 2` (requires dropping the previous-quips dependency). Cost per window is prefill (about 3.2k tokens) plus decode (about 160 tokens) | `config.py` |
| N9 | POLISH | **CLAUDE.md contradicts the decisions:** it still says clips of 90 s or less and names only the 35B model. Owner's file, so not edited | `CLAUDE.md` |
| N10 | FIXED (session 11) | A shifted last quip can start after the video ends (not clamped after scheduling); the mp3 of a dropped quip stays until the job expires | `services/commentary.py` `schedule_quips` |
| N11 | INFO | Still open from audit 2: F7 (edge-tts is an unofficial endpoint), F9 (Docker files stale; deletion needs your OK), F12 (partly), F13, F14 (volume ducking, timeupdate jitter), F16, F17, no LICENSE | see history below |

## Verified good this time
- Sweep, one-job guard, source deletion and 409 path behave as documented (tests).
- Timeline: never truncates text, rounds timestamps, 4.5 s gap; `schedule_quips` logs every shift/drop.
- Real WebSocket upgrade works under uvicorn with the pinned `websockets` (101).
- Security spot check: filenames sanitized, `job_id` validated before use in audio paths, only `uploads/audio` is mounted, CORS limited to configured origins, client errors generic.
- Docs match the code as of this audit (STATE, TASKS, README, CONVENTIONS, DECISIONS updated).

## Plan
See `docs/TASKS.md`. Order: (1) robustness before any long-clip run: N2, N5, N6, N4, N1 (about one session, all small); (2) decide D4 (partial results and failure policy); (3) real footage in the browser, short then 10+ min, on 9B then 35B; (4) GIF, LICENSE, fresh-venv check, tag v0.1.0.

---
# History

### Audit 2 baseline (historical)

| Check | Result |
|---|---|
| `pytest backend/tests -q` | 92 passed (about 3 s) |
| `npm run lint` / `npm run build` | clean / ok |
| `npm audit --omit=dev` | 1 high: `follow-redirects` (transitive via axios; not reachable from browser XHR; `npm audit fix` resolves it) |
| Services running locally | uvicorn :8000 (started before session 6: restart it), Vite :5173, llama-server :8080 with **Qwen3.5-9B Q4_K_M** (not the 35B-A3B named in CLAUDE.md) |
| venv `edge-tts` | was 7.2.8, which gets 403 from Bing, although requirements.txt pins >=7.3.1. Upgraded during this audit to 7.3.1; real TTS now works |

### Audit 2 goal check (historical) (CONVENTIONS "Project context")

| MVP goal | Status | Evidence |
|---|---|---|
| Upload a clip, 90 s or less | **Mismatch**: limit is 60 s | `config.py:39` `MAX_VIDEO_SECONDS = 60`; the goal text says 90. Decide which, then align config, docs and error text |
| See progress | Done | Job API + `WS /ws/analyze/{job_id}`, per-window "Analyzing part i of n". Needs a visual check in the browser |
| Real vision-LLM commentary | Done in code; run live on a still-frame clip only | Live run: 6 frames, 3248 prompt tokens, 44.7 s for one 10 s window on the 9B model. Quality on real motion not judged by this audit |
| Synced, non-overlapping TTS | Done and measured | Live run shifted one quip by 1.6 s and dropped one. Playback sync in the browser unverified |
| Runs locally in a few commands | Partly | Works, but needs llama-server + internet for edge-tts, and there is **no root README.md** (README lives at `docs/README.md`, stale and cut off) |
| Clean README + demo GIF | Not started | |
| Honest | Yes | No canned LLM text, no fake audio; TTS failure shows "(no audio)" and a notice |

### Audit 2 live run (2026-10-28, in-process, real LLM + real edge-tts)

Clip: 10 s slideshow built from `spike_frames/w896_none_t*.jpg` (real lion dance stills, so it exercises plumbing and prompt, not motion understanding).
- Crop box found, one LLM call, 3 quips returned (JSON parsed first time). Pipeline total 46.2 s.
- TTS real: 8-word lines measure about 4.5 s, a 2-word line 1.9 s, a 21-word line 5.4 s. edge-tts writes 48 kbps CBR mp3 with no Xing header, so mutagen computes duration from file size; that matches the frame count, so it is exact for CBR. About 0.5 s of silence padding is included.
- Scheduler: quip at 4.00 s moved to 5.61 s, quip at 7.20 s dropped (needed 3.22 s shift, max 2.0).
- Defects seen: F1, F2, F3 below.

### Audit 2 findings and current status

| # | Tag | Finding | Evidence |
|---|---|---|---|
| F1 | BLOCKS-DEMO | **Quips are cut mid-sentence.** `finalize_timeline` truncates text to `gap * QUIP_WORDS_PER_SECOND` words. Live result: "Yellow lion bows its head. A deep, theatrical" was spoken aloud as a fragment | `services/commentary.py:35-38` |
| F2 | BLOCKS-DEMO | **Timing constants contradict real TTS.** Config assumes 2.5 words/s and a 2.5 s gap; measured speech is about 1.8 words/s including padding (8 words = 4.5 s). The prompt also tells the model "at least 2.5 seconds apart". Result: most second quips get shifted or dropped, so a 10 s window yields about 2 spoken lines | `config.py:24-25`, `prompts/commentary_system.txt` (OUTPUT section), `services/commentary.py:44` |
| F3 | BLOCKS-DEMO | **Float noise in timestamps reaches the UI**: shifted quips carry values like 5.611999999999999 and VideoPlayer prints `{quip.timestamp}s` | `services/commentary.py:53-60`; `frontend/src/components/VideoPlayer.jsx:150` |
| F4 | FIXED (session 9) | **Orphaned uploads survive restarts.** The job store is in memory, so a restart forgets jobs and nothing deletes their files. Currently `backend/uploads/` holds 6 videos (about 130 MB) and 4 audio dirs, 3 of them full of 10-byte `fake-audio` mp3s from pre-session-6 runs. (Not touched: CLAUDE.md forbids editing uploads/) | `main.py:25-33` (cleanup only covers jobs in the store) |
| F5 | FIXED (session 9) | Source video is kept for `JOB_TTL_SECONDS` (1 h) after a job completes although nothing reads it again and the browser plays its own blob URL | `services/pipeline.py:33,39`: only the failure path calls `cleanup_job_files` |
| F6 | FIXED (session 9) | No concurrency guard. Two uploads run two pipelines against a `-np 1` llama-server, doubling latency toward the 300 s timeout. The frontend disables the input, but a second tab does not | `main.py:111` `background_tasks.add_task` |
| F7 | SHOULD-FIX | Demo depends on the unofficial Bing edge-tts endpoint, which already broke once (403 on 7.2.8). If it breaks on demo day the app degrades to text only. The failure is honest, but the demo needs a fallback plan (pre-recorded GIF with audio; optionally an offline TTS, which needs your approval as a new feature) | `services/tts.py` |
| F8 | FIXED (session 9) | `requirements.txt` has no version pins and still lists `pytest-asyncio` (not installed, unused; tests use anyio) and test deps as runtime deps | `backend/requirements.txt` |
| F9 | SHOULD-FIX | Docker files are untested and stale: `frontend/Dockerfile` uses node:18 (Vite 8 needs 20.19+), compose has no env, no LLM host mapping, and mounts source over the image | `docker-compose.yml`, `frontend/Dockerfile`, `backend/Dockerfile` |
| F10 | SHOULD-FIX | Docs were stale and misleading (STATE.md described removed code, TASKS.md said the frontend still used the old API, README cut off, at `docs/README.md` rather than the repo root). Rewritten in this session | `docs/` |
| F11 | FIXED (session 9) | `vision_spike.py` carries its own copy of `motion_box`; will drift from `video_processor.motion_box` | `backend/scripts/vision_spike.py:33` |
| F12 | POLISH | `spike_frames/` (32 untracked jpgs) not in .gitignore; `frontend/README.md` is the Vite template; `TTS_PROVIDER` setting is unused; `LLM_MODEL` default `qwen-coder` is misleading (llama-server ignores it); `temperature=0.8` is hardcoded | `config.py:27,15`, `services/llm.py:111` |
| F13 | POLISH | `.avi`/HEVC `.mov` uploads are accepted but most browsers cannot play them, so the preview is blank while commentary is generated | `services/video_processor.py:14`, `App.jsx` `accept="video/*"` |
| F14 | POLISH, partly fixed | VideoPlayer: audio is not stopped when the video ends; ducking overwrites a volume change the user makes mid-clip; `timeupdate` fires about 4 times a second so a line can start up to 250 ms late | `VideoPlayer.jsx:37-60` |
| F15 | POLISH, partly fixed | `tests/test_main.py` actually tests commentary orchestration (rename `test_commentary.py`); `conftest.py` writes a dummy `test_video.mp4` into the cwd that no test uses; no frontend tests; no test that runs real `motion_box` on a moving-subject fixture | `backend/tests/` |
| F16 | POLISH | Upload size limit (100 MB) is checked after Starlette has spooled the whole body; fine for a local app | `main.py:77-85` |
| F18 | BLOCKS-DEMO, FIXED (session 9) | **No WebSocket library in requirements.** A venv built from requirements.txt had neither `websockets` nor `wsproto`, so real uvicorn logged "No supported WebSocket library" and `/ws/analyze/{id}` returned 404: progress would never reach the browser. Route tests missed it because Starlette's TestClient does not need one. Fixed by adding `websockets`; verified with a real upgrade request (101) | `backend/requirements.txt` |
| F17 | IGNORE | CORS headers are missing on the generic 500 response (ServerErrorMiddleware sits outside CORS); only affects the error path of a local app | `main.py:63-66` |

### Status of the 2026-10-27 audit (audit 1)

All BLOCKS-MVP items are resolved except where noted.

| Old finding | Now |
|---|---|
| stale `backend/main.py`, `/generate`, `/mock`, boto3/presigned endpoint, mcp_server | Removed |
| ws took a client `video_path`; `job_id` missing; `ws://backend:8000` | Job API: server-owned paths, `WS /ws/analyze/{job_id}`, `GET /api/jobs/{id}`, `VITE_API_BASE` |
| No CORS | Added, configurable (`CORS_ORIGINS`) |
| Frames sent as JSON text, 224x224, 30 s timeout | Real `image_url` parts, crop + aspect-preserving 896 px, 300 s timeout |
| Fake LLM text, fake audio bytes | Removed; errors fail the job, TTS failure gives `audio_url: null` |
| Fake progress | Real per-phase progress via `progress_cb` |
| No duration limit, all of uploads/ served, error strings leaked, cleanup gaps | Fixed (60 s limit, audio-only mount, generic errors, cleanup on failure). Restart orphans remain: F4 |
| Playback ignored seek/pause, no overlap control, durations unknown | VideoPlayer rewritten (queue, seek, pause, ducking); durations measured; server-side scheduling |
| react-toastify missing, lint failing, requirements missing pydantic-settings | Fixed. Pins still missing: F8 |
| `.history/`, repomix tracked | Untracked |
| Docs: STATE chat text, README cut off, Docker claims | STATE/TASKS/README rewritten now; Docker marked untested |
| `jobs.py` frozen `time.time()` defaults | Fixed (`default_factory`) |
| sync-lambda TTS fakes that silently failed | Tests rewritten with async fakes |

### What was in good shape

- Pipeline separation is clean (video_processor, llm, tts, commentary, jobs, pipeline), single shared `settings`, generic client errors with server-side logging, validation before final write, job files cleaned on failure.
- JobStore and the WebSocket handler have behavior tests (replay on reconnect, 4404, idle disconnect, terminal handling).
- Tests now use real tiny video files and a hand-built real mp3 rather than only mocks; mocks sit at the LLM and edge-tts boundaries.
- The "no fake output" rule is enforced end to end, which is the strongest honesty story for a resume project.

### Audit 2 plan (historical)

See `docs/TASKS.md`. Short version: (1) tune timing so spoken lines are not cut or dropped (F1-F3, one session); (2) real-footage runs in the browser on 3 clips, tune prompt, pick the demo model; (3) hygiene (F4-F9); (4) README at repo root, demo GIF, tag a release.
