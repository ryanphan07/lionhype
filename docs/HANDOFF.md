# Handoff: session 13 TTS hardening (2026-10-28)

## 1. Done
- tts.py: NoAudioReceived/WebSocketError retried once (TTS_RETRIES, TTS_RETRY_DELAY_SECONDS); 401/403 and other 4xx never. Failure log has exception class, text length, voice, rate, file size. Unreadable duration is re-measured once after 0.2 s; if still unreadable the log adds file size and first 4 bytes (hex).
- config.py: TTS_CONCURRENCY default 4 -> 1; new TTS_START_STAGGER_SECONDS (0.3). commentary.py: stagger lock before each clip start (semaphore already existed).
- backend/scripts/tts_check.py: 6 lines through generate_audio_clip, prints OK/fail with bytes, deletes its temp folder, exit 1 on any failure.
- .env.example, README troubleshooting, CONVENTIONS, STATE, BRIEFING updated; test count 112.
- Tests (+7): NoAudioReceived retry, 403 no retry, duration re-check (recovers / fails after two tries with diagnostics), failure-log diagnostics, concurrency 1 vs 2.

## 2. Decisions and deviations
- TTS_CONCURRENCY and TTS_RETRIES already existed; only the default changed. Stagger lives in commentary.py (where the semaphore is), so tts_check.py runs sequentially without it. Added setting name TTS_START_STAGGER_SECONDS (prompt gave none).

## 3. Results
- pytest (backend venv): 112 passed. Frontend untouched.

## 4. Not verified
- tts_check.py against real edge-tts (run: `python backend\scripts\tts_check.py`); a real two-clip app run; whether the duration failure was a flush race.

## 5. Open issues and risks
- Untracked backend/t1-t8.mp3 are leftovers from CLI tests; not committed, delete if unwanted.

## 6. Suggested next session
Owner live run with tts_check.py then a full clip; send numbers and bugs; README limitations, GIF, tag v0.1.0.
