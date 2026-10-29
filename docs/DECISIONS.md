# Design decisions

Owner decisions and the reasoning behind them. Add new entries at the bottom with a date.

## 2026-10-28

### D1. Long clips are a goal (10+ minutes), not a 60/90 s cap
- The owner wants to process clips longer than 10 minutes eventually. The 60 s limit was a temporary MVP guard, not a product decision.
- Consequences, measured on the 9B model: about 54 s per LLM call (docs/BENCHMARKS.md; a 40 s clip took 299 s, about 7x real time), so a 10 minute clip would be roughly 70 minutes: extrapolated, untested. The 35B-A3B model will differ; measure it.
- Windows are independent apart from the two previous quips, so length scales linearly and memory stays flat (frames are sampled per window).
- Limits become settings: `MAX_VIDEO_SECONDS` (default 1800) and `MAX_UPLOAD_MB` (default 2048). They are guards against accidents, not promises of speed.
- Open risks for long jobs (tracked in TASKS): one failed window currently fails the whole job after possibly 40 minutes of work (consider per-window retry or skipping with a logged gap, owner to decide); no persistence, so a server restart loses the job; progress needs an ETA to be tolerable; the README demo should use a short clip.

### D2. Models: develop on Qwen3.5-9B, use Qwen3.6-35B-A3B for real runs
- Defaults and docs must work with either; nothing may hard-code model behavior. Timing numbers in docs are labeled with the model they were measured on (9B so far).
- Prompt and word/gap calibration must be re-checked on the 35B before declaring quality done.

### D3. TTS provider and fallback (owner unsure; current recommendation)
- Today: edge-tts only (unofficial Microsoft endpoint, needs internet, broke once with 403). On any failure the quip is kept as text with no audio and the UI shows a notice. This is honest and already implemented.
- Options considered:
  1. Keep edge-tts only, text-only fallback (current). Zero work; demo depends on internet and an unofficial endpoint.
  2. Add an offline provider (Piper is the usual choice: local, free, decent quality, Windows binaries available) behind `TTS_PROVIDER`. About one session; makes the app fully local, which matches "local-first" and removes demo-day risk.
  3. Windows built-in SAPI via pyttsx3: trivial, but robotic and weak for a comedy demo.
- Recommendation: do option 1 now, finish and ship the MVP, record the demo GIF with sound while edge-tts works, then add option 2 as the first post-MVP task. Revisit if edge-tts breaks again. Nothing here changes the job API: `audio_url` stays nullable.
- Status: decision deferred until after v0.1.0.

### D4. Long-job strategy (open: owner to choose; audit 3 N3)
A 10+ minute clip is one job of about 60 windows. Today one failed window fails everything and nothing is shown until the end.
- A. Keep all-or-nothing (current). Simple and honest, but a late failure wastes up to 45 minutes.
- B. Skip a failed window after one retry, log it, and tell the user which time ranges have no commentary ("skipped 2 of 60 parts"). Small change; still honest because the gap is reported, not faked. Changes the earlier "a failed window ends the job" rule.
- C. Progressive results: synthesize each window as it finishes and let the UI show and play commentary while the rest processes. Best UX for long clips; changes the job result API (partial results) and the player. Larger change.
- Recommendation: B now, C after v0.1.0.

## 2026-10-28 (session 12)

### D4 decision: A
- Keep all-or-nothing for v0.1.0. Revisit B (skip a failed window after one retry, report the gap) and C (progressive results) after release.

### D5. License
- MIT, copyright "Ryan Phan 2026" (name taken from the git user; change `LICENSE` if the owner wants another).
