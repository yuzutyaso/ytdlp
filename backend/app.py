import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import ytpl
import ytsr

app = Flask(__name__)

# CORS設定: 本番環境では特定のオリジンのみを許可することを強く推奨します
# Vercelにデプロイした場合、通常はVercelのドメイン (例: https://your-project-name.vercel.app) を指定します。
# デプロイ後に実際のドメインに合わせて修正してください。
# 例: CORS(app, origins=["https://your-project-name.vercel.app", "http://localhost:3000"])
CORS(app)

# yt-dlpのオプション設定
# quiet=True: コンソール出力を抑制
# skip_download=True: ダウンロードは行わず情報のみ取得
# format: MP4形式で最適なビデオとオーディオを選択
ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
}

@app.route('/api/search', methods=['GET'])
def search_videos():
    """
    指定されたクエリでYouTube動画とプレイリストを検索します。
    GETパラメータ: q (検索クエリ)
    """
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "検索クエリが指定されていません。"}), 400

    try:
        # ytsrで最大10件の検索結果を取得
        results = ytsr.search(query, limit=10)
        formatted_results = []
        for r in results:
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
        # エラー発生時はサーバーサイドのエラーとしてログに記録し、クライアントには汎用メッセージを返します
        print(f"検索エラー: {e}")
        return jsonify({"error": "検索中にエラーが発生しました。"}), 500

@app.route('/api/video_info', methods=['GET'])
def get_video_info():
    """
    指定されたYouTube動画の情報を取得します。
    GETパラメータ: url (動画のURL)
    """
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "動画URLが指定されていません。"}), 400

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 動画の情報をダウンロードせずに抽出
            info = ydl.extract_info(video_url, download=False)
            
            # 必要な情報のみを抽出して整形
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
                # Vercelのサーバーレス環境で動画を直接ストリーミングするのは複雑なため、
                # フロントエンドでYouTubeの埋め込みプレーヤーを使用するためにIDのみを返す
                # "formats": [f['url'] for f in info.get('formats', []) if 'url' in f and f['ext'] == 'mp4' and 'vcodec' in f and f['vcodec'] != 'none'],
            }
            return jsonify(extracted_info)
    except yt_dlp.DownloadError as e:
        # yt-dlp特有のダウンロードエラー (例: 動画が見つからない、非公開など)
        print(f"yt-dlpエラー (動画情報): {e}")
        return jsonify({"error": "動画情報が見つからないか、アクセスできません。"}), 404
    except Exception as e:
        print(f"動画情報取得エラー: {e}")
        return jsonify({"error": "動画情報の取得中にエラーが発生しました。"}), 500

@app.route('/api/playlist_info', methods=['GET'])
def get_playlist_info():
    """
    指定されたYouTubeプレイリストの情報を取得します。
    GETパラメータ: url (プレイリストのURL)
    """
    playlist_url = request.args.get('url')
    if not playlist_url:
        return jsonify({"error": "プレイリストURLが指定されていません。"}), 400

    try:
        playlist = ytpl.parse_playlist(playlist_url)
        
        # プレイリストの基本的な情報と、含まれる動画の情報を抽出
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
        print(f"プレイリスト情報取得エラー: {e}")
        return jsonify({"error": "プレイリスト情報の取得中にエラーが発生しました。"}), 500

if __name__ == '__main__':
    # 開発環境でのみデバッグモードを有効にし、ポート5000で実行します。
    # Vercelにデプロイする際は、Vercelが自動的に環境を設定するため、この部分は無視されます。
    app.run(debug=os.environ.get('FLASK_ENV') == 'development', port=5000)
