# api/index.py

import os
import json
from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL
import uuid
import tempfile # For creating temporary files/directories

app = Flask(__name__)

# --- IMPORTANT CONSIDERATION FOR VERCEL ---
# You would need to integrate with a cloud storage service here (e.g., boto3 for S3, google-cloud-storage)
# and upload the video to it, returning its public URL.
# For simplicity in this example, we'll imagine a placeholder upload function.

def upload_to_cloud_storage(file_path, filename):
    """
    Placeholder function for uploading to cloud storage.
    Replace with actual integration (e.g., AWS S3, Cloudinary).
    """
    print(f"Simulating upload of {file_path} to cloud storage...")
    # Example:
    # import boto3
    # s3 = boto3.client('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    # s3.upload_file(file_path, 'your-bucket-name', filename)
    return f"https://your-storage-service.com/videos/{filename}"

@app.route('/convert', methods=['POST'])
def convert_video():
    data = request.get_json()
    youtube_url = data.get('youtubeUrl')

    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required.'}), 400

    if not youtube_url.startswith('https://www.youtube.com/watch?v='):
        return jsonify({'error': 'Invalid YouTube URL format.'}), 400

    temp_file_path = None
    try:
        # Create a unique filename for the downloaded video
        video_id = youtube_url.split('v=')[1].split('&')[0]
        unique_filename = f"{video_id}-{uuid.uuid4()}.webm"
        
        # Use a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_file_path = os.path.join(tmpdir, unique_filename)

            ydl_opts = {
                'format': 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]',
                'outtmpl': temp_file_path,
                'merge_output_format': 'webm',
                'quiet': True, # Suppress console output
                'no_warnings': True,
                'cachedir': False, # Don't cache
                'noplaylist': True, # Only download single video
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])

            public_webm_url = upload_to_cloud_storage(temp_file_path, unique_filename)

            return jsonify({
                'message': 'Video converted successfully!',
                'webmUrl': public_webm_url
            })

    except Exception as e:
        print(f"Error during conversion: {e}")
        return jsonify({'error': 'Failed to convert video.', 'details': str(e)}), 500
    finally:
        # Clean up the temporary file if it still exists (tempfile context manager handles this mostly)
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                print(f"Error cleaning up file {temp_file_path}: {e}")


@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'ytdlp-webm-converter-api is running!'})
