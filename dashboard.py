import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPEhtml>
<html>
<head>
    <title>Terminal Dashboard</title>
    <style>
        body {
            background-color: #050505;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            padding: 30px;
            margin: 0;
        }
        h1 {
            color: #00ff00;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .stat-box {
            display: inline-block;
            margin-right: 20px;
            padding: 15px 25px;
            border: 1px solid #00ff00;
            background-color: #0a0a0a;
            box-shadow: 0 0 10px #00ff0022;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            display: block;
            margin-top: 10px;
            color: #fff;
        }
        .failed-box {
            color: #ff3333;
            border-color: #ff3333;
            box-shadow: 0 0 10px #ff333322;
        }
        #logs {
            background-color: #000;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 15px;
            height: 400px;
            overflow-y: scroll;
            white-space: pre-wrap;
            margin-top: 20px;
            font-size: 0.9em;
            line-height: 1.4;
            box-shadow: inset 0 0 15px #00ff0011;
        }
        .blink {
            animation: blink-animation 1s steps(2, start) infinite;
        }
        @keyframes blink-animation {
            to { visibility: hidden; }
        }
    </style>
</head>
<body>
    <h1>> root@tiktok-downloader:~# ./monitor.sh <span class="blink">_</span></h1>
    
    <div id="stats" style="display: flex;">
        <div class="stat-box">
            TOTAL_QUEUED
            <span class="stat-value" style="color: #00ff00;" id="s-total">0</span>
        </div>
        <div class="stat-box">
            SUCCESS_DOWNLOADED
            <span class="stat-value" style="color: #00ff00;" id="s-done">0</span>
        </div>
        <div class="stat-box failed-box" style="margin-right: 0;">
            FAILED_URLS
            <span class="stat-value" style="color: #ff3333;" id="s-fail">0</span>
        </div>
    </div>

    <h2 style="margin-top: 30px;">> tail -f tiktokdownload.log</h2>
    <div id="logs">Loading system logs...</div>
    
    <script>
        async function update() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                
                document.getElementById('s-total').innerText = data.total;
                document.getElementById('s-done').innerText = data.downloaded;
                document.getElementById('s-fail').innerText = data.failed;
                
                const logsDiv = document.getElementById('logs');
                const isScrolledToBottom = logsDiv.scrollHeight - logsDiv.clientHeight <= logsDiv.scrollTop + 50;
                
                if (data.logs) {
                    logsDiv.textContent = data.logs;
                } else {
                    logsDiv.textContent = "No logs found yet.";
                }
                
                if (isScrolledToBottom) {
                    logsDiv.scrollTop = logsDiv.scrollHeight;
                }
            } catch(e) {
                console.error('Error fetching stats:', e);
            }
        }
        setInterval(update, 2000);
        update();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def stats():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    urls_file = os.path.join(base_dir, "data", "urls.txt")
    log_file = os.path.join(os.path.dirname(base_dir), "tiktokdownload.log")
    failed_file = os.path.join(base_dir, "failed_urls.txt")
    download_dir = os.path.join(base_dir, "data", "downloads")

    total = 0
    if os.path.exists(urls_file):
        with open(urls_file, 'r') as f:
            total = len([l for l in f if l.strip()])
            
    failed = 0
    if os.path.exists(failed_file):
        with open(failed_file, 'r') as f:
            failed = len([l for l in f if l.strip()])
            
    downloaded = 0
    if os.path.exists(download_dir):
        downloaded = len([name for name in os.listdir(download_dir) if name.endswith('.mp4')])
        
    logs = ""
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs_lines = f.readlines()[-50:]
            logs = "".join(logs_lines)
            
    return jsonify({
        'total': total,
        'downloaded': downloaded,
        'failed': failed,
        'logs': logs
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
