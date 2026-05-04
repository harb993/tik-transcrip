import os
import json
from flask import Flask, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOWNLOADS_DIR = os.path.join(DATA_DIR, "downloads")
TRANSCRIPTS_DIR = os.path.join(DOWNLOADS_DIR, "transcripts")
LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "tiktokdownload.log")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Categorization Pipeline</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --panel-bg: rgba(255, 255, 255, 0.03);
            --panel-border: rgba(255, 255, 255, 0.08);
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.5);
            --success: #10b981;
            --pending: #f59e0b;
        }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg-color); 
            background-image: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.15), transparent 50%);
            color: var(--text-main); 
            margin: 0; 
            padding: 24px; 
            display: flex; 
            height: 100vh; 
            box-sizing: border-box; 
            overflow: hidden;
        }

        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }

        .glass-panel {
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .sidebar { width: 320px; margin-right: 24px; overflow-y: hidden; z-index: 10; }
        .main-content { flex: 1; display: flex; flex-direction: column; gap: 24px; z-index: 10; min-width: 0; }
        
        .top-row { display: flex; gap: 24px; flex: 1; min-height: 50%; }
        .video-container { flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center;}
        .transcript-container { flex: 1; display: flex; flex-direction: column;}
        .log-container { flex: 1; display: flex; flex-direction: column; min-height: 25%; }

        h2 { 
            margin-top: 0; 
            font-size: 0.9em; 
            font-weight: 600; 
            letter-spacing: 0.05em; 
            text-transform: uppercase; 
            color: var(--text-muted);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .live-dot {
            height: 8px; width: 8px;
            background-color: var(--success);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px var(--success);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        #list-container { flex: 1; overflow-y: auto; padding-right: 8px; }

        .video-item { 
            padding: 12px 16px; 
            border-radius: 10px;
            background: rgba(255,255,255,0.02);
            margin-bottom: 8px;
            cursor: pointer; 
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid transparent;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .video-item:hover { 
            background: rgba(255,255,255,0.06); 
            transform: translateY(-1px);
        }
        .video-item.active { 
            background: rgba(59, 130, 246, 0.1); 
            border-color: rgba(59, 130, 246, 0.3);
            box-shadow: inset 0 0 20px rgba(59, 130, 246, 0.05);
        }
        
        .vid-name { font-weight: 500; font-size: 0.9em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
        
        .status-badge { 
            align-self: flex-start;
            padding: 4px 8px; 
            font-size: 0.7em; 
            font-weight: 600;
            border-radius: 20px; 
            background: rgba(255,255,255,0.1);
            color: var(--text-muted);
        }
        .status-badge.done { background: rgba(16, 185, 129, 0.15); color: var(--success); }
        .status-badge.pending { background: rgba(245, 158, 11, 0.15); color: var(--pending); }
        
        video { 
            width: 100%; 
            height: 100%; 
            max-height: 100%;
            border-radius: 10px;
            background: #000; 
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            outline: none;
        }
        
        .transcript-box { 
            flex: 1; 
            overflow-y: auto; 
            white-space: pre-wrap; 
            font-size: 0.95em; 
            line-height: 1.6;
            color: var(--text-main);
            padding: 16px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }
        
        .log-box {
            flex: 1; 
            overflow-y: auto; 
            white-space: pre-wrap; 
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85em; 
            line-height: 1.5;
            color: var(--text-muted);
            padding: 16px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="sidebar glass-panel">
        <h2>Video Queue <span class="live-dot"></span></h2>
        <div id="list-container">Loading...</div>
    </div>
    
    <div class="main-content">
        <div class="top-row">
            <div class="video-container glass-panel" style="padding: 10px;">
                <video id="player" controls controlsList="nodownload"></video>
            </div>
            
            <div class="transcript-container glass-panel">
                <h2>AI Transcript</h2>
                <div id="transcript" class="transcript-box">Select a video to view its transcript.</div>
            </div>
        </div>
        
        <div class="log-container glass-panel">
            <h2>System Logs</h2>
            <div id="logs" class="log-box">Initializing...</div>
        </div>
    </div>

    <script>
        let videos = [];
        let currentActiveId = null;
        
        async function fetchVideos() {
            try {
                const res = await fetch('/api/videos');
                videos = await res.json();
                renderList();
            } catch(e) {
                console.error("Failed to fetch videos", e);
            }
        }
        
        function renderList() {
            const container = document.getElementById('list-container');
            if(videos.length === 0) {
               container.innerHTML = "<div style='color: var(--text-muted); font-size: 0.9em;'>No videos found in downloads folder.</div>";
               return;
            }
            container.innerHTML = '';
            
            videos.forEach(v => {
                const div = document.createElement('div');
                div.className = `video-item ${v.id === currentActiveId ? 'active' : ''}`;
                div.innerHTML = `
                    <div class="vid-name">${v.id}.mp4</div>
                    <div class="status-badge ${v.has_transcript ? 'done' : 'pending'}">${v.has_transcript ? 'Transcript Ready' : 'Processing...'}</div>
                `;
                div.onclick = () => selectVideo(v.id, div);
                container.appendChild(div);
            });
        }
        
        async function selectVideo(id, element) {
            currentActiveId = id;
            document.querySelectorAll('.video-item').forEach(el => el.classList.remove('active'));
            element.classList.add('active');
            
            const player = document.getElementById('player');
            if (!player.src.includes(id)) {
                player.src = `/media/${id}.mp4`;
                player.play().catch(e => console.log("Autoplay prevented"));
            }
            
            const transBox = document.getElementById('transcript');
            transBox.innerHTML = '<span style="color: var(--text-muted)">Loading transcript...</span>';
            
            try {
                const res = await fetch(`/api/transcript/${id}`);
                if (res.ok) {
                    const data = await res.json();
                    transBox.innerText = data.text || "No speech detected in this video.";
                } else {
                    transBox.innerHTML = '<span style="color: var(--text-muted)">Transcript not found or still processing.</span>';
                }
            } catch (e) {
                transBox.innerText = "Error loading transcript.";
            }
        }
        
        const logBox = document.getElementById('logs');
        let isScrolledToBottom = true;
        
        logBox.addEventListener('scroll', () => {
            isScrolledToBottom = Math.abs(logBox.scrollHeight - logBox.clientHeight - logBox.scrollTop) < 5;
        });

        async function fetchLogs() {
            try {
                const res = await fetch('/api/logs');
                const data = await res.json();
                if(data.logs !== logBox.innerText) {
                    logBox.innerText = data.logs || "No logs available.";
                    if (isScrolledToBottom) {
                        logBox.scrollTop = logBox.scrollHeight;
                    }
                }
            } catch(e) {}
        }
        
        setInterval(fetchLogs, 1000);
        setInterval(fetchVideos, 5000);
        
        fetchVideos();
        fetchLogs();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/videos')
def list_videos():
    videos = []
    if os.path.exists(DOWNLOADS_DIR):
        for f in os.listdir(DOWNLOADS_DIR):
            if f.endswith('.mp4'):
                vid = f.replace('.mp4', '')
                has_transcript = os.path.exists(os.path.join(TRANSCRIPTS_DIR, f"{vid}.json"))
                videos.append({'id': vid, 'has_transcript': has_transcript})
    return jsonify(videos)

@app.route('/media/<filename>')
def serve_media(filename):
    return send_from_directory(DOWNLOADS_DIR, filename)

@app.route('/api/transcript/<vid>')
def get_transcript(vid):
    t_path = os.path.join(TRANSCRIPTS_DIR, f"{vid}.json")
    if os.path.exists(t_path):
        with open(t_path, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/logs')
def get_logs():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                # Get last 150 lines
                lines = f.readlines()
                return jsonify({'logs': "".join(lines[-150:])})
        except:
            return jsonify({'logs': '[SYS_ERROR] UNABLE TO READ LOGS'})
    return jsonify({'logs': 'NO LOG FILE LOCATED.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)
