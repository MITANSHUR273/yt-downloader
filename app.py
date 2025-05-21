from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid
import threading
import time

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/fetch_formats', methods=['POST'])
def fetch_formats():
    url = request.form['url']
    formats = []

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [
                {
                    'format_id': f['format_id'],
                    'format_note': f.get('format_note', ''),
                    'ext': f['ext'],
                    'resolution': f"{f.get('height', '')}p" if f.get('height') else '',
                    'filesize': f.get('filesize')
                }
                for f in info['formats']
                if f.get('vcodec') != 'none'
            ]
    except Exception as e:
        return f"Error fetching formats: {e}"

    return render_template('index.html', formats=formats, url=url)

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    quality = request.form['quality']
    download_type = request.form['type']
    
    unique_id = str(uuid.uuid4())

    if download_type == 'audio':
        file_path = f"downloads/{unique_id}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': file_path,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        file_path = f"downloads/{unique_id}.mp4"
        ydl_opts = {
            'format': f"{quality}+bestaudio/best",
            'outtmpl': file_path,
            'merge_output_format': 'mp4',
            'quiet': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return f"Error downloading: {e}"

    # Delete file after 10 seconds
    def delete_file(path):
        time.sleep(10)
        if os.path.exists(path):
            os.remove(path)

    threading.Thread(target=delete_file, args=(file_path,)).start()

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    app.run(debug=True)
