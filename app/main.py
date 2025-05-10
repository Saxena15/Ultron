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
#
# from fastapi import File, UploadFile
#
# @app.post("/upload-cookies")
# async def upload_cookies(file: UploadFile = File(...)):
#     if file.filename != "cookies.txt":
#         raise HTTPException(status_code=400, detail="Only 'cookies.txt' is allowed")
#
#     contents = await file.read()
#     with open("cookies.txt", "wb") as f:
#         f.write(contents)
#
#     return {"message": "Cookies uploaded successfully"}


# Static route to serve downloaded files
from fastapi.staticfiles import StaticFiles
app.mount("/videos", StaticFiles(directory=VIDEO_DIR), name="videos")

class M3U8Request(BaseModel):
    m3u8_url: str


@app.post("/convert-m3u8")
def convert_m3u8(req: M3U8Request):
    video_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")

    try:
        result = subprocess.run([
            "ffmpeg",
            "-i", req.m3u8_url,
            "-c", "copy",
            output_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Conversion failed or file not created.")

        return {"download_url": f"/videos/{video_id}.mp4"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"ffmpeg error: {e.stderr}")