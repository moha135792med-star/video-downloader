import os
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# قالب صفحة التحميل الجديدة
DOWNLOAD_PAGE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري تجهيز الملف للتحميل...</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; max-width: 450px; width: 100%; }
        .timer { font-size: 48px; color: #3498db; font-weight: bold; margin: 20px 0; }
        .btn { display: none; background-color: #2ecc71; color: white; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 6px; font-size: 18px; }
        .ad-space { background: #eee; border: 1px dashed #ccc; padding: 20px; margin: 20px 0; border-radius: 6px; color: #777; }
    </style>
</head>
<body>
    <div class="card">
        <h2>صفحة التحميل المباشر</h2>
        <div class="ad-space">مساحة إعلانية (Ad Banner)</div>
        <p id="msg">سيبدأ تحضير الملف خلال:</p>
        <div id="countdown" class="timer">5</div>
        <a id="dl-link" href="{{ download_url }}" class="btn">اضغط هنا للتحميل الآن</a>
    </div>

    <script>
        let seconds = 5;
        const timerEl = document.getElementById('countdown');
        const btnEl = document.getElementById('dl-link');
        const msgEl = document.getElementById('msg');

        const interval = setInterval(() => {
            seconds--;
            timerEl.innerText = seconds;
            if (seconds <= 0) {
                clearInterval(interval);
                timerEl.style.display = 'none';
                msgEl.innerText = 'ملفك جاهز للتحميل!';
                btnEl.style.display = 'inline-block';
                // بدء التحميل تلقائياً
                window.location.href = "{{ download_url }}";
            }
        }, 1000);
    </script>
</body>
</html>
"""

@app.route('/download', methods=['POST'])
def get_video_info():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'يرجى تقديم رابط الفيديو'}), 400

    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True, 'noplaylist': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if 'entries' in info:
                info = info['entries'][0]

            return jsonify({'title': info.get('title', 'video'), 'url': video_url})
    except Exception as e:
        return jsonify({'error': 'تعذر معالجة الرابط.'}), 500

@app.route('/download-page', methods=['GET'])
def download_page():
    video_url = request.args.get('url')
    type_type = request.args.get('type')
    download_url = f"http://127.0.0.1:5000/process-download?url={video_url}&type={type_type}"
    return render_template_string(DOWNLOAD_PAGE_HTML, download_url=download_url)

@app.route('/process-download', methods=['GET'])
def process_download():
    video_url = request.args.get('url')
    type_type = request.args.get('type')

    if not video_url:
        return "رابط غير صحيح", 400

    filename_template = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')

    if type_type == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename_template,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        }
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': filename_template,
            'merge_output_format': 'mp4',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            
            if type_type == 'audio':
                file_path = os.path.splitext(file_path)[0] + '.mp3'
            else:
                if not file_path.endswith('.mp4'):
                    file_path = os.path.splitext(file_path)[0] + '.mp4'

            return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"حدث خطأ أثناء التنزيل: {str(e)}", 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)