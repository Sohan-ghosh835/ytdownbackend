import yt_dlp
from pytube import YouTube
import tkinter as tk
from tkinter import filedialog, messagebox

def get_best_qualities(link):
    best_video_res = None
    best_audio_abr = None
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(link, download=False)
            formats = info.get('formats', [])
            video_resolutions = [f.get('height', 0) for f in formats if f.get('vcodec') != 'none']
            audio_bitrates = [f.get('abr', 0) for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            if video_resolutions:
                best_video_res = max(video_resolutions)
            if audio_bitrates:
                best_audio_abr = max(audio_bitrates)
    except Exception:
        pass
    return str(best_video_res), str(int(best_audio_abr)) if best_audio_abr else None

def try_download_ytdlp(video_url, save_dir, fmt, quality):
    if fmt == "mp3":
        options = {
            'format': f'bestaudio[abr<={quality}]',
            'outtmpl': f'{save_dir}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'quiet': True,
        }
    else:
        options = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': f'{save_dir}/%(title)s.%(ext)s',
            'quiet': True,
        }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video_url])
        return True
    except Exception:
        return False

def fallback_download_pytube(link, destination_folder, quality):
    try:
        yt_obj = YouTube(link)
        mp4_streams = yt_obj.streams.filter(progressive=True, file_extension='mp4', res=quality)
        best_stream = mp4_streams.first()
        if best_stream:
            best_stream.download(output_path=destination_folder)
            return True
        return False
    except Exception:
        return False

def pick_output_folder():
    return filedialog.askdirectory()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    video_link = input("Enter the YouTube video URL: ").strip()
    best_video, best_audio = get_best_qualities(video_link)
    format_choice = input(f"Choose format (mp4/mp3): ").strip().lower()
    if format_choice == "mp4":
        print(f"Highest available resolution: {best_video}p")
        quality_choice = input("Select resolution (e.g., 1080, 720, 480): ").strip()
    elif format_choice == "mp3":
        print(f"Highest available audio bitrate: {best_audio}kbps")
        quality_choice = input("Select audio bitrate (e.g., 160, 128, 70): ").strip()
    else:
        print("Invalid format")
        exit()
    print("choosing output folder . . .")
    output_path = pick_output_folder()
    if not output_path:
        messagebox.showerror("Error", "No folder selected.")
        exit()
    print("downloading . . .")
    if try_download_ytdlp(video_link, output_path, format_choice, quality_choice):
        print("Success: Downloaded")
    elif format_choice == "mp4" and fallback_download_pytube(video_link, output_path, quality_choice + "p"):
        print("Success: Downloaded (fallback)")
    else:
        print("Download failed! Please check the video URL or your internet connection.")
