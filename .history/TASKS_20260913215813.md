This file tracks active development tasks, known gaps, and the roadmap for LionHype.

## What is missing or incomplete

The repo is not yet production-grade. The current state is best described as a working prototype with a few critical gaps.

### 1. Production hardening
Missing or incomplete areas include:
- stronger input validation for uploaded files
- safe handling of missing or invalid videos
- more robust logging and monitoring

### 2. Real LLM/TTS production integration
The current code anticipates external AI services but also includes offline fallbacks.

This means:
- LLM calls can work if a compatible local or remote service is available
- TTS output is generated locally as a fallback pattern, but real production deployment still needs a finalized choice of model/provider and audio storage strategy

### 3. End-to-end real-world validation
The project is tested with mock objects, but it is not yet proven against:
- real uploaded lion dance footage
- real OpenCV capture edge cases
- high-volume processing
- long videos
- actual WebSocket stress/load conditions

### 4. Frontend polish
The frontend is functional and handles core pipeline states, but still relatively minimal:
- limited playback orchestration beyond timestamp-based triggers
- no deeper visual dashboard or timeline analytics
- quip highlighting and timeline scrubbing could be improved

### 5. Deployment and infrastructure
The repo does not yet present a fully defined deployment strategy for:
- backend hosting
- frontend hosting
- audio/static asset serving in production
- environment variables and configuration separation
- containerization or cloud deployment

### 6. Security and operational concerns
Potential follow-ups include:
- limiting upload size and file extensions
- securing WebSocket access
- avoiding direct trust of user-supplied file paths
- sanitizing and validating generated filenames
- controlling backend access to AI services and external endpoints

## Recommended next steps

### Priority 2: Harden backend reliability & logging
- [ ] Add comprehensive logging across the commentary pipeline
- [ ] Add more unit tests around failure cases and invalid video files
- [ ] Ensure WebSocket clients handle reconnects gracefully (already partially implemented)

### Priority 4: Improve frontend UX & playback
- [ ] Add timeline scrubbing and better quip highlighting during playback
- [ ] Implement loading and empty states for smoother UX
- [ ] Consider adding a visual dashboard for pipeline analytics

### Priority 5: Validate on real content & prepare for deployment
- [ ] Test against actual lion dance footage to measure runtime and performance
- [ ] Tune the frame sampling strategy for quality vs. latency vs. cost
