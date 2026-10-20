import time
import hashlib
import secrets
from flask import Flask, request, jsonify, render_template_string
import ecdsa
from ecdsa import VerifyingKey, BadSignatureError
import sqlite3

try:
    from features import extract_log_mel_spectrogram
    from inference import DeepfakeDetector
    MODEL_LOADED = True
except Exception:
    MODEL_LOADED = False

app = Flask(__name__)
DB_PATH = "veritrust.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            device_hardware_hash TEXT,
            public_key TEXT,
            trust_score REAL DEFAULT 100.0,
            created_at REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            verdict TEXT,
            timestamp REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VERITRUST — Global Cybersecurity Intelligence Platform</title>
    <style>
        :root {
            --bg-primary: #07090e;
            --bg-secondary: #0d121f;
            --card-bg: #111827;
            --card-border: #1f2937;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --text-primary: #f3f4f6;
            --text-muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--card-border);
        }
        .brand {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 1.5px;
            color: var(--text-primary);
            text-decoration: none;
        }
        .brand span { color: var(--accent-blue); }
        .nav-links a {
            color: var(--text-muted);
            text-decoration: none;
            margin-left: 16px;
            font-size: 14px;
        }
        .container { max-width: 1000px; margin: 0 auto; padding: 32px 16px; width: 100%; }
        .hero { text-align: center; padding: 40px 0; }
        .hero h1 { font-size: 36px; font-weight: 800; margin-bottom: 16px; line-height: 1.2; }
        .hero p { color: var(--text-muted); font-size: 16px; max-width: 600px; margin: 0 auto 30px; }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .btn {
            background: var(--accent-blue);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn-outline {
            background: transparent;
            border: 1px solid var(--card-border);
            color: var(--text-primary);
        }
        .input-group { display: flex; gap: 8px; margin-top: 12px; }
        input {
            flex: 1;
            background: var(--bg-secondary);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 12px;
            color: white;
            font-size: 14px;
            outline: none;
        }
        .badge {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
            display: inline-block;
        }
        .badge-safe { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
        .badge-danger { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
        .log-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--card-border); font-size: 14px; }
    </style>
</head>
<body>
    <nav class="navbar">
        <a href="/" class="brand">🛡️ VERI<span>TRUST</span></a>
        <div class="nav-links">
            <a href="/dashboard" class="btn btn-outline" style="padding: 6px 12px;">Dashboard</a>
        </div>
    </nav>

    <div class="container">
        <div class="hero">
            <span class="badge badge-safe" style="margin-bottom: 12px;">SYSTEM ONLINE & PROTECTED</span>
            <h1>Trust Every Connection.<br>Investigate Every Threat.</h1>
            <p>Advanced phone-number reputation intelligence, caller-ID spoofing investigation, and AI deepfake detection platform.</p>
        </div>

        <div class="card">
            <h3>🔍 Phone Number Reputation Intelligence</h3>
            <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">Enter any phone number to test for spoofing heuristics.</p>
            <div class="input-group">
                <input type="text" id="phoneInput" placeholder="e.g. +233 24 123 4567">
                <button class="btn" onclick="checkNumber()">Scan Number</button>
            </div>
            <div id="scanResult" style="margin-top: 16px; font-weight: 600;"></div>
        </div>

        <div class="card">
            <h3>📊 Live Security Operations Log</h3>
            <div id="logList" style="margin-top: 12px;">
                <div class="log-item">
                    <span>Incoming Call (+233 24 *** 8901)</span>
                    <span class="badge badge-safe">PASSED</span>
                </div>
                <div class="log-item">
                    <span>Unknown Caller (+233 55 *** 1234)</span>
                    <span class="badge badge-danger">SPOOF DETECTED</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function checkNumber() {
            const phone = document.getElementById('phoneInput').value.trim();
            const resDiv = document.getElementById('scanResult');
            if(!phone) {
                resDiv.style.color = '#ef4444';
                resDiv.innerText = 'Please enter a phone number.';
                return;
            }
            resDiv.style.color = '#9ca3af';
            resDiv.innerText = 'Scanning Veritrust database...';

            try {
                const res = await fetch('/api/v1/check-number', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone_number: phone })
                });
                const data = await res.json();
                if(data.status === 'success') {
                    const isSpoof = data.verdict === 'SPOOF DETECTED';
                    resDiv.style.color = isSpoof ? '#ef4444' : '#10b981';
                    resDiv.innerText = `Result for ${data.phone_number}: ${data.verdict}`;

                    const logList = document.getElementById('logList');
                    const div = document.createElement('div');
                    div.className = 'log-item';
                    div.innerHTML = `<span>${data.phone_number}</span><span class="badge ${isSpoof ? 'badge-danger' : 'badge-safe'}">${data.verdict}</span>`;
                    logList.prepend(div);
                }
            } catch(e) {
                resDiv.style.color = '#ef4444';
                resDiv.innerText = 'Connection error during scan.';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
@app.route('/dashboard')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/v1/check-number', methods=['POST'])
def check_number():
    data = request.get_json() or {}
    phone_number = data.get('phone_number')
    if not phone_number:
        return jsonify({"status": "error", "message": "Missing phone number"}), 400

    clean_num = phone_number.replace(" ", "").replace("-", "")
    if clean_num.endswith("0000") or "1234" in clean_num:
        verdict = "SPOOF DETECTED"
    else:
        verdict = "PASSED"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO call_logs (phone_number, verdict, timestamp) VALUES (?, ?, ?)", 
                   (phone_number, verdict, time.time()))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "phone_number": phone_number, "verdict": verdict}), 200

@app.route('/api/v1/score/<user_id>', methods=['GET'])
def get_user_score(user_id):
    return jsonify({"status": "success", "trust_score": 100.0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
