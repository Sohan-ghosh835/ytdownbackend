from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    format: str
    quality: str

@app.post("/download")
async def download_video(data: DownloadRequest, request: Request):
    url = data.url
    fmt = data.format
    quality = data.quality
    filename = str(uuid.uuid4())
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    common_opts = {
        'outtmpl': f'{output_dir}/{filename}.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'retries': 3,
        'sleep_interval_requests': 1,
        'max_sleep_interval': 3,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
    }

    if fmt == "mp3":
        ydl_opts = {
            **common_opts,
            'format': f'bestaudio[abr<={quality}]',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }]
        }
        ext = 'mp3'
    else:
        ydl_opts = {
            **common_opts,
            'format': f'bestvideo[height<={quality}]+bestaudio/best',
            'merge_output_format': 'mp4',
        }
        ext = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Download failed: {str(e)}"})

    file_path = f"{output_dir}/{filename}.{ext}"
    base_url = str(request.base_url).rstrip("/")
    return {"download_url": f"{base_url}/file/{filename}.{ext}"}

@app.get("/file/{filename}")
def serve_file(filename: str):
    filepath = os.path.join("downloads", filename)
    if not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "video/mp4"
    return FileResponse(filepath, media_type=media_type, filename=filename)
