from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
import json
import uuid

app = FastAPI()

VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)


@app.get("/")
def read_root():
    return {"message": "Hello, Ultron!"}

class VideoRequest(BaseModel):
    url: str
    mode: str = "download"  # or "direct"

@app.post("/fetch")
def fetch_video(req: VideoRequest):
    if req.mode == "direct":
        try:
            output = subprocess.check_output([
                "yt-dlp", "-f", "best[ext=mp4]", "-j", req.url
            ])
            video_info = json.loads(output)
            return {"direct_url": video_info["url"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Direct link fetch failed: {str(e)}")
    elif req.mode == "download":
        video_id = str(uuid.uuid4())[:8]
        output_template = f"{VIDEO_DIR}/{video_id}.%(ext)s"
        try:
            subprocess.run([
                "yt-dlp", "-f", "best[ext=mp4]", "-o", output_template, req.url
            ], check=True)

            for file in os.listdir(VIDEO_DIR):
                if file.startswith(video_id):
                    return {"download_url": f"/videos/{file}"}
            raise HTTPException(status_code=404, detail="File not found after download.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

# Static route to serve downloaded files
from fastapi.staticfiles import StaticFiles
app.mount("/videos", StaticFiles(directory=VIDEO_DIR), name="videos")
