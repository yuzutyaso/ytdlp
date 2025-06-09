# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS # CORS対応のため
import yt_dlp
import ytpl
import ytsr

app = Flask(__name__)
CORS(app) # 全てのオリジンからのリクエストを許可 (開発用。本番では制限推奨)

# yt-dlpのオプション設定 (必要な場合)
ydl_opts = {
    'quiet': True,
    'skip_download': True, # ダウンロードはしない
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]', # MP4形式を優先
}

@app.route('/api/search', methods=['GET'])
def search_videos():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "検索クエリが指定されていません"}), 400
    try:
        results = ytsr.search(query, limit=10) # 10件まで取得
        formatted_results = []
        for r in results:
            # 検索結果のタイプに応じて情報を整形
            if r['type'] == 'video':
                formatted_results.append({
                    "type": "video",
                    "title": r['title'],
                    "id": r['id'],
                    "url": r['url'],
                    "thumbnail": r['thumbnail'],
                    "duration": r['duration'],
                    "views": r['views'],
                    "author": r['author']['name'] if 'author' in r else 'Unknown',
                })
            elif r['type'] == 'playlist':
                 formatted_results.append({
                    "type": "playlist",
                    "title": r['title'],
                    "id": r['id'],
                    "url": r['url'],
                    "thumbnail": r['thumbnail'],
                    "video_count": r['video_count'],
                    "author": r['author']['name'] if 'author' in r else 'Unknown',
                })
        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/video_info', methods=['GET'])
def get_video_info():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "動画URLが指定されていません"}), 400
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # 必要な情報のみ抽出
            extracted_info = {
                "id": info.get('id'),
                "title": info.get('title'),
                "description": info.get('description'),
                "uploader": info.get('uploader'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "view_count": info.get('view_count'),
                "upload_date": info.get('upload_date'),
                "webpage_url": info.get('webpage_url'),
                "formats": [f['url'] for f in info.get('formats', []) if 'url' in f and f['ext'] == 'mp4' and 'vcodec' in f and f['vcodec'] != 'none'], # MP4動画URLのみ
            }
            return jsonify(extracted_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlist_info', methods=['GET'])
def get_playlist_info():
    playlist_url = request.args.get('url')
    if not playlist_url:
        return jsonify({"error": "プレイリストURLが指定されていません"}), 400
    try:
        playlist = ytpl.parse_playlist(playlist_url)
        # プレイリストの基本的な情報と、各動画の情報を抽出
        extracted_playlist = {
            "id": playlist.id,
            "title": playlist.title,
            "description": playlist.description,
            "url": playlist.url,
            "video_count": playlist.video_count,
            "videos": []
        }
        for video in playlist.videos:
            extracted_playlist["videos"].append({
                "id": video.id,
                "title": video.title,
                "url": video.url,
                "thumbnail_url": video.thumbnail_url,
                "duration": video.duration,
                "author": video.author
            })
        return jsonify(extracted_playlist)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) # 開発用サーバーをポート5000で起動
