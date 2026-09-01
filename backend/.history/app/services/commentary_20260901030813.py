import os
import requests
from typing import List, Dict
from app.schemas.events import CommentaryQuip, CommentaryResponse

async def generate_video_commentary(video_id: str) -> CommentaryResponse:
    frame_dir = os.path.join("backend", "uploads", "frames", video_id)
    frame_files = sorted(os.listdir(frame_dir))

    system_prompt = """
    You are a sarcastic, chaotic, high-energy sports commentator. 
    Provide commentary in the format of a JSON array of { timestamp: float, text: string }.
    """

    commentary_quips = []

    for frame_file in frame_files:
        frame_path = os.path.join(frame_dir, frame_file)
        with open(frame_path, "rb") as frame_image:
            files = {"file": frame_image}
            data = {
                "prompt": system_prompt,
                "max_tokens": 150
            }
            response = requests.post("http://127.0.0.1:8080/v1/chat/completions", files=files, data=data)

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    # Extract the frame count from the filename
                    frame_count = int(frame_file.split("_")[1].split(".")[0])
                    # Calculate the timestamp based on the frame count and sample interval
                    timestamp = frame_count * 2  # Assuming 2 seconds per frame
                    text = response_data.get("text", "")
                    commentary_quips.append(CommentaryQuip(timestamp=timestamp, text=text))
                except Exception as e:
                    print(f"Error processing frame {frame_file}: {e}")
            else:
                print(f"Error sending frame {frame_file} to the endpoint: {response.status_code} - {response.text}")

    return CommentaryResponse(quips=commentary_quips)
