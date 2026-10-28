"""Vision spike: send N real frames from a video to llama-server and print what the model says.

Usage (from the repo root, venv active):
    python backend/scripts/vision_spike.py path\\to\\clip.mp4 --width 224
    python backend/scripts/vision_spike.py path\\to\\clip.mp4 --width 448 --n 8

Saves the exact frames the model saw to ./spike_frames/ so you can judge them yourself.
"""
import argparse
import base64
import json
import os
import re
import time

import cv2
from openai import OpenAI

SYSTEM = (
    "You are an energetic, funny lion dance sports commentator. You are shown frames from "
    "a lion dance video, each labeled with its timestamp in seconds. Reply with ONLY JSON: "
    '{"what_is_happening": "<2 sentences describing the visible action>", '
    '"commentary": [{"timestamp": <seconds>, "text": "<max 12 words>"}]}'
)


def sample_frames(path: str, n: int, width: int):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"Could not open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps
    frames = []
    try:
        for i in range(n):
            t = duration * (i + 0.5) / n
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, frame = cap.read()
            if not ok:
                continue
            h, w = frame.shape[:2]
            height = max(1, int(h * width / w))
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok:
                frames.append((round(t, 2), frame, base64.b64encode(buf).decode()))
    finally:
        cap.release()
    return duration, frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--n", type=int, default=8, help="number of frames to send")
    ap.add_argument("--width", type=int, default=224, help="frame width in px (aspect preserved)")
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="qwen-coder", help="llama-server mostly ignores this")
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--think", action="store_true", help="leave the model's thinking mode on")
    args = ap.parse_args()

    duration, frames = sample_frames(args.video, args.n, args.width)
    if not frames:
        raise SystemExit("No frames could be read from the video.")
    print(f"Video: {duration:.1f}s | sending {len(frames)} frames at width {args.width}")

    os.makedirs("spike_frames", exist_ok=True)
    content = [{"type": "text", "text": "Frames follow, in order."}]
    for t, frame, b64 in frames:
        cv2.imwrite(os.path.join("spike_frames", f"w{args.width}_t{t:06.2f}.jpg"), frame)
        content.append({"type": "text", "text": f"Frame at t={t}s:"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

    client = OpenAI(base_url=args.base_url, api_key="local-key", timeout=args.timeout)
    extra = {} if args.think else {"chat_template_kwargs": {"enable_thinking": False}}

    start = time.time()
    resp = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}],
        temperature=0.7,
        max_tokens=1200,
        extra_body=extra,
    )
    elapsed = time.time() - start

    text = resp.choices[0].message.content or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    print(f"\nLatency: {elapsed:.1f}s | usage: {resp.usage}")
    print("\n--- RAW OUTPUT ---")
    print(text)

    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        json.loads(cleaned)
        print("\nJSON parse: OK")
    except json.JSONDecodeError as exc:
        print(f"\nJSON parse: FAILED ({exc})")


if __name__ == "__main__":
    main()
