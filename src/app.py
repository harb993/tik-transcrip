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
<!DOCTYPEhtml>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PIPELINE_DASHBOARD_v1.0</title>
    <style>
        :root {
            --bg: #030303;
            --main-green: #00ff41;
            --dark-green: #008f11;
            --dim-green: #003b00;
        }
        body { 
            font-family: 'Courier New', Courier, monospace; 
            background-color: var(--bg); 
            color: var(--main-green); 
            margin: 0; 
            padding: 20px; 
            display: flex; 
            height: 100vh; 
            box-sizing: border-box; 
            overflow: hidden;
            text-shadow: 0 0 5px var(--main-green);
        }
        /* CRT Scanline effect */
        body::after {
            content: " ";
            display: block;
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            z-index: 2;
            background-size: 100% 2px, 3px 100%;
            pointer-events: none;
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg); border-left: 1px solid var(--dim-green); }
        ::-webkit-scrollbar-thumb { background: var(--dark-green); }
        ::-webkit-scrollbar-thumb:hover { background: var(--main-green); }

        .terminal-box {
            border: 1px solid var(--main-green);
            background: rgba(0, 20, 0, 0.2);
            box-shadow: inset 0 0 10px var(--dim-green);
            padding: 15px;
            position: relative;
        }
        .terminal-box::before {
            content: " ";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 10px;
            background: linear-gradient(to bottom, rgba(0, 255, 65, 0.2) 0%, transparent 100%);
        }

        .sidebar { width: 300px; display: flex; flex-direction: column; overflow-y: auto; z-index: 3; margin-right: 20px;}
        .main-content { flex: 1; display: flex; flex-direction: column; gap: 20px; z-index: 3;}
        
        .top-row { display: flex; gap: 20px; flex: 1; min-height: 40%;}
        .video-container { flex: 1; text-align: center; display: flex; flex-direction: column;}
        .transcript-container { flex: 1; display: flex; flex-direction: column;}
        
        .log-container { flex: 1; display: flex; flex-direction: column; min-height: 30%; }

        .video-item { 
            padding: 8px; 
            border-bottom: 1px dashed var(--dark-green); 
            cursor: pointer; 
            transition: all 0.2s; 
        }
        .video-item:hover { background: var(--dim-green); }
        .video-item.active { background: var(--main-green); color: var(--bg); text-shadow: none; font-weight: bold;}
        .video-item.active .status-badge { color: var(--bg); border-color: var(--bg); }
        
        video { 
            width: 100%; 
            height: 100%; 
            max-height: 400px;
            background: var(--bg); 
            border: 1px solid var(--main-green);
            filter: grayscale(100%) contrast(1.2) sepia(100%) hue-rotate(80deg) saturate(400%) brightness(0.8);
        }
        
        .transcript-box { 
            flex: 1; 
            overflow-y: auto; 
            white-space: pre-wrap; 
            font-size: 0.9em; 
            line-height: 1.4;
        }
        .log-box {
            flex: 1; 
            overflow-y: auto; 
            white-space: pre-wrap; 
            font-size: 0.85em; 
            line-height: 1.3;
        }

        h2 { margin-top: 0; font-size: 1.2em; border-bottom: 1px solid var(--main-green); padding-bottom: 5px; text-transform: uppercase;}
        
        .status-badge { display: inline-block; padding: 2px 6px; font-size: 0.7em; border: 1px solid var(--main-green); margin-top: 5px; }
        .blink { animation: blinker 1s linear infinite; }
        @keyframes blinker { 50% { opacity: 0; } }
        
        .header-text { margin-bottom: 15px; font-size: 0.9em;}
    </style>
</head>
<body>
    <div class="sidebar terminal-box" id="video-list">
        <h2>>> FILESYSTEM</h2>
        <div class="header-text">SCANNING ./DOWNLOADS...<span class="blink">_</span></div>
        <div id="list-container">LOADING...</div>
    </div>
    
    <div class="main-content">
        <div class="top-row">
            <div class="video-container terminal-box">
                <h2>>> VISUAL_FEED</h2>
                <video id="player" controls controlsList="nodownload"></video>
                <div id="video-info" style="margin-top:10px; font-size:0.8em;">[NO SIGNAL]</div>
            </div>
            
            <div class="transcript-container terminal-box">
                <h2>>> NLP_DECODE_TRANSCRIPT</h2>
                <div id="transcript" class="transcript-box">AWAITING INPUT...</div>
            </div>
        </div>
        
        <div class="log-container terminal-box">
            <h2>>> BACKEND_SYS_LOGS <span style="font-size:0.6em; float:right;">LIVE<span class="blink">_</span></span></h2>
            <div id="logs" class="log-box">INITIALIZING...</div>
        </div>
    </div>

    <script>
        let videos = [];
        
        async function fetchVideos() {
            const res = await fetch('/api/videos');
            videos = await res.json();
            renderList();
        }
        
        function renderList() {
            const container = document.getElementById('list-container');
            if(videos.length === 0) {
               container.innerHTML = "NO FILES FOUND.";
               return;
            }
            container.innerHTML = '';
            
            videos.forEach(v => {
                const div = document.createElement('div');
                div.className = 'video-item';
                div.innerHTML = `
                    > <span>${v.id}.mp4</span><br>
                    <span class="status-badge">[${v.has_transcript ? 'NLP: DONE' : 'NLP: PENDING'}]</span>
                `;
                div.onclick = () => selectVideo(v.id, div);
                container.appendChild(div);
            });
        }
        
        async function selectVideo(id, element) {
            document.querySelectorAll('.video-item').forEach(el => el.classList.remove('active'));
            element.classList.add('active');
            
            const player = document.getElementById('player');
            player.src = `/media/${id}.mp4`;
            document.getElementById('video-info').innerHTML = `PLAYING: <span style="color:white;">${id}.mp4</span>`;
            
            const transBox = document.getElementById('transcript');
            transBox.innerText = "DECODING TRANSCRIPT...";
            
            try {
                const res = await fetch(`/api/transcript/${id}`);
                if (res.ok) {
                    const data = await res.json();
                    transBox.innerText = data.text || "NO TEXT DETECTED.";
                } else {
                    transBox.innerText = "[ERROR] TRANSCRIPT NOT FOUND.";
                }
            } catch (e) {
                transBox.innerText = "[SYS_ERROR] FETCH FAILED.";
            }
        }
        
        // Log streaming
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
                    logBox.innerText = data.logs || "NO LOGS GENERATED YET.";
                    if (isScrolledToBottom) {
                        logBox.scrollTop = logBox.scrollHeight;
                    }
                }
            } catch(e) {}
        }
        
        setInterval(fetchLogs, 1000);
        setInterval(fetchVideos, 5000); // refresh list automatically
        
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
