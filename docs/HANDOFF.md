# Handoff: session 17 (v0.1.0 tagged locally, not pushed)

## 1. Done
- docs/demo.mp4 (1.5 MB, H.264 crf 28, 720 px high, AAC, cropped to the app column) and docs/demo.gif (6.8 MB, 12 s from 12 s to 24 s, 640 px, 10 fps, palettegen). Raw recording stays in Downloads.
- README: Demo section (GIF plus "Full clip with sound" link), Status line fixed. TASKS, BRIEFING, OWNER_TODO updated.
- Tag v0.1.0 (annotated), not pushed.

## 2. Decisions and deviations
- Cropped both assets to the app column (crop 960x970 at 480,110 of the 1080p recording); the mp4 is the full 40.6 s recording, not trimmed (it is all playback).
- The recording opens on the finished job, so the GIF shows playback and commentary highlight, not the progress bar.

## 3. Results
pytest 130 passed; eslint clean; vite build OK.

## 4. Not verified
- GIF/mp4 rendering on GitHub after push; audio in the mp4 by ear.

## 5. Open issues
- None new.

## 6. Suggested next session
v0.1.1: HTTP 400 fallback for response_format, sequential crop sampling (12 s extract), 35B and long-clip measurements.
