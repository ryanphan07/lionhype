# Design decisions

Owner decisions and the reasoning behind them. Add new entries at the bottom with a date.

## 2026-10-28

### D1. Long clips are a goal (10+ minutes), not a 60/90 s cap
- The owner wants to process clips longer than 10 minutes eventually. The 60 s limit was a temporary MVP guard, not a product decision.
- Consequences, measured on the 9B model: about 45 s per 10 s window, so a 10 minute clip is about 60 windows and 45 minutes of processing. The 35B-A3B model will differ; measure it.
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
