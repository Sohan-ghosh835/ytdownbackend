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
async def download_video(data: DownloadRequest):
    url = data.url
    fmt = data.format
    quality = data.quality
    filename = f"{uuid.uuid4()}"
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    if fmt == "mp3":
        ydl_opts = {
            'format': f'bestaudio[abr<={quality}]',
            'outtmpl': f'{output_dir}/{filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'quiet': True,
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': f'{output_dir}/{filename}.%(ext)s',
            'quiet': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    file_ext = 'mp3' if fmt == 'mp3' else 'mp4'
    download_path = f"{output_dir}/{filename}.{file_ext}"
    return {"download_url": f"/file/{filename}.{file_ext}"}

@app.get("/file/{filename}")
def serve_file(filename: str):
    filepath = f"downloads/{filename}"
    if not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(filepath, media_type='application/octet-stream', filename=filename)
