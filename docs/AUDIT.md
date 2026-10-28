# LionHype audit 2 (2026-10-28)

Second full audit, after sessions 1 to 6. Everything below was checked against the code, and the pipeline was run with the real llama-server and real edge-tts (see "Live run").
Tags: BLOCKS-DEMO (fix before recording the demo or applying) / SHOULD-FIX / POLISH / IGNORE. Line refs are relative to `backend/app/` unless a path is given.

## Baseline

| Check | Result |
|---|---|
| `pytest backend/tests -q` | 92 passed (about 3 s) |
| `npm run lint` / `npm run build` | clean / ok |
| `npm audit --omit=dev` | 1 high: `follow-redirects` (transitive via axios; not reachable from browser XHR; `npm audit fix` resolves it) |
| Services running locally | uvicorn :8000 (started before session 6: restart it), Vite :5173, llama-server :8080 with **Qwen3.5-9B Q4_K_M** (not the 35B-A3B named in CLAUDE.md) |
| venv `edge-tts` | was 7.2.8, which gets 403 from Bing, although requirements.txt pins >=7.3.1. Upgraded during this audit to 7.3.1; real TTS now works |

## Goal check (CONVENTIONS "Project context")

| MVP goal | Status | Evidence |
|---|---|---|
| Upload a clip, 90 s or less | **Mismatch**: limit is 60 s | `config.py:39` `MAX_VIDEO_SECONDS = 60`; the goal text says 90. Decide which, then align config, docs and error text |
| See progress | Done | Job API + `WS /ws/analyze/{job_id}`, per-window "Analyzing part i of n". Needs a visual check in the browser |
| Real vision-LLM commentary | Done in code; run live on a still-frame clip only | Live run: 6 frames, 3248 prompt tokens, 44.7 s for one 10 s window on the 9B model. Quality on real motion not judged by this audit |
| Synced, non-overlapping TTS | Done and measured | Live run shifted one quip by 1.6 s and dropped one. Playback sync in the browser unverified |
| Runs locally in a few commands | Partly | Works, but needs llama-server + internet for edge-tts, and there is **no root README.md** (README lives at `docs/README.md`, stale and cut off) |
| Clean README + demo GIF | Not started | |
| Honest | Yes | No canned LLM text, no fake audio; TTS failure shows "(no audio)" and a notice |

## Live run (2026-10-28, in-process, real LLM + real edge-tts)

Clip: 10 s slideshow built from `spike_frames/w896_none_t*.jpg` (real lion dance stills, so it exercises plumbing and prompt, not motion understanding).
- Crop box found, one LLM call, 3 quips returned (JSON parsed first time). Pipeline total 46.2 s.
- TTS real: 8-word lines measure about 4.5 s, a 2-word line 1.9 s, a 21-word line 5.4 s. edge-tts writes 48 kbps CBR mp3 with no Xing header, so mutagen computes duration from file size; that matches the frame count, so it is exact for CBR. About 0.5 s of silence padding is included.
- Scheduler: quip at 4.00 s moved to 5.61 s, quip at 7.20 s dropped (needed 3.22 s shift, max 2.0).
- Defects seen: F1, F2, F3 below.

## New findings

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
| F14 | POLISH | VideoPlayer: audio is not stopped when the video ends; ducking overwrites a volume change the user makes mid-clip; `timeupdate` fires about 4 times a second so a line can start up to 250 ms late | `VideoPlayer.jsx:37-60` |
| F15 | POLISH | `tests/test_main.py` actually tests commentary orchestration (rename `test_commentary.py`); `conftest.py` writes a dummy `test_video.mp4` into the cwd that no test uses; no frontend tests; no test that runs real `motion_box` on a moving-subject fixture | `backend/tests/` |
| F16 | POLISH | Upload size limit (100 MB) is checked after Starlette has spooled the whole body; fine for a local app | `main.py:77-85` |
| F18 | BLOCKS-DEMO, FIXED (session 9) | **No WebSocket library in requirements.** A venv built from requirements.txt had neither `websockets` nor `wsproto`, so real uvicorn logged "No supported WebSocket library" and `/ws/analyze/{id}` returned 404: progress would never reach the browser. Route tests missed it because Starlette's TestClient does not need one. Fixed by adding `websockets`; verified with a real upgrade request (101) | `backend/requirements.txt` |
| F17 | IGNORE | CORS headers are missing on the generic 500 response (ServerErrorMiddleware sits outside CORS); only affects the error path of a local app | `main.py:63-66` |

## Status of the 2026-10-27 audit

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

## What is in good shape

- Pipeline separation is clean (video_processor, llm, tts, commentary, jobs, pipeline), single shared `settings`, generic client errors with server-side logging, validation before final write, job files cleaned on failure.
- JobStore and the WebSocket handler have behavior tests (replay on reconnect, 4404, idle disconnect, terminal handling).
- Tests now use real tiny video files and a hand-built real mp3 rather than only mocks; mocks sit at the LLM and edge-tts boundaries.
- The "no fake output" rule is enforced end to end, which is the strongest honesty story for a resume project.

## Plan

See `docs/TASKS.md`. Short version: (1) tune timing so spoken lines are not cut or dropped (F1-F3, one session); (2) real-footage runs in the browser on 3 clips, tune prompt, pick the demo model; (3) hygiene (F4-F9); (4) README at repo root, demo GIF, tag a release.
