"""Vision spike v2: send N real frames from a video to llama-server and print what the model says.

New in v2:
  --crop auto      find where the motion is (the performers) and crop to it before resizing,
                   so small subjects in a wide shot get far more pixels per image token
  --system-file    load the system prompt from a text file ("MAX_QUIPS" is replaced by --max-quips)
  --dry-run        extract/crop/save the frames and print the crop box, without calling the model

Usage (from the repo root, venv active):
    python backend/scripts/vision_spike.py clip.mp4 --width 640 --crop auto --system-file commentary_prompt_v2.txt
    python backend/scripts/vision_spike.py clip.mp4 --width 640 --crop auto --dry-run

Saves the exact frames the model saw to ./spike_frames/.
"""
import argparse
import base64
import json
import os
import re
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app.services.video_processor import motion_box  # noqa: E402  (single shared implementation)

DEFAULT_SYSTEM = (
    "You are an energetic, funny lion dance sports commentator. You are shown frames from "
    "a lion dance video, each labeled with its timestamp in seconds. Reply with ONLY JSON: "
    '{"what_is_happening": "<2 sentences describing the visible action>", '
    '"commentary": [{"timestamp": <seconds>, "text": "<max 12 words>"}]}'
)


def sample_frames(path, n, width, crop_mode):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"Could not open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    box = None
    if crop_mode == "auto":
        box = motion_box(cap, duration)
    elif crop_mode not in ("none", ""):
        box = tuple(float(v) for v in crop_mode.split(","))
    frames = []
    try:
        for i in range(n):
            t = duration * (i + 0.5) / n
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, frame = cap.read()
            if not ok:
                continue
            h, w = frame.shape[:2]
            if box:
                x0, y0, x1, y1 = box
                frame = frame[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
            fh, fw = frame.shape[:2]
            frame = cv2.resize(frame, (width, max(1, int(fh * width / fw))), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ok:
                frames.append((round(t, 2), frame, base64.b64encode(buf).decode()))
    finally:
        cap.release()
    return duration, box, frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--n", type=int, default=8, help="number of frames to send")
    ap.add_argument("--width", type=int, default=640, help="frame width in px after cropping (aspect preserved)")
    ap.add_argument("--crop", default="auto", help="auto | none | x0,y0,x1,y1 as fractions of the frame")
    ap.add_argument("--system-file", help="text file with the system prompt")
    ap.add_argument("--max-quips", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=500)
    ap.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="qwen-coder", help="llama-server mostly ignores this")
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--think", action="store_true", help="leave the model's thinking mode on")
    ap.add_argument("--dry-run", action="store_true", help="save frames and print the crop box, no model call")
    args = ap.parse_args()

    duration, box, frames = sample_frames(args.video, args.n, args.width, args.crop)
    if not frames:
        raise SystemExit("No frames could be read from the video.")
    shape = frames[0][1].shape
    box_text = tuple(round(v, 2) for v in box) if box else "none (full frame)"
    print(f"Video: {duration:.1f}s | {len(frames)} frames at {shape[1]}x{shape[0]} | crop box: {box_text}")

    os.makedirs("spike_frames", exist_ok=True)
    tag = args.crop.replace(",", "_")
    content = [{"type": "text", "text": "Frames follow, in order."}]
    for t, frame, b64 in frames:
        cv2.imwrite(os.path.join("spike_frames", f"w{args.width}_{tag}_t{t:06.2f}.jpg"), frame)
        content.append({"type": "text", "text": f"Frame at t={t}s:"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    if args.dry_run:
        print("Dry run: frames saved to ./spike_frames/, model not called.")
        return

    system = DEFAULT_SYSTEM
    if args.system_file:
        with open(args.system_file, encoding="utf-8") as fh:
            system = fh.read().replace("MAX_QUIPS", str(args.max_quips))

    from openai import OpenAI

    client = OpenAI(base_url=args.base_url, api_key="local-key", timeout=args.timeout)
    extra = {} if args.think else {"chat_template_kwargs": {"enable_thinking": False}}

    start = time.time()
    resp = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
        temperature=0.8,
        max_tokens=args.max_tokens,
        extra_body=extra,
    )
    elapsed = time.time() - start

    text = resp.choices[0].message.content or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    u = resp.usage
    print(f"\nLatency: {elapsed:.1f}s | prompt_tokens={u.prompt_tokens} completion_tokens={u.completion_tokens}")
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