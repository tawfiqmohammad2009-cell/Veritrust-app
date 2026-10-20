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
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False

app = Flask(__name__)
DB_PATH = "veritrust.db"

# Initialize TFLite deepfake detector safely
try:
    detector = DeepfakeDetector("veritrust_audio.tflite")
    MODEL_LOADED = True
except Exception as e:
    MODEL_LOADED = False

ACTIVE_CHALLENGES = {}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            device_hardware_hash TEXT,
            public_key TEXT,
            trust_score REAL DEFAULT 100.0,
            email TEXT,
            created_at REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            phone_number TEXT,
            verdict TEXT,
            risk_score REAL,
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

GLOBAL_STYLE = """
:root {
    --bg-primary: #07090e;
    --bg-secondary: #0d121f;
    --card-bg: #111827;
    --card-border: #1f2937;
    --accent-blue: #3b82f6;
    --accent-glow: rgba(59, 130, 246, 0.15);
    --accent-green: #10b981;
    --accent-amber: #f59e0b;
    --accent-red: #ef4444;
    --text-primary: #f3f4f6;
    --text-muted: #9ca3af;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: var(--font-sans);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 32px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--card-border);
    position: sticky;
    top: 0;
    z-index: 100;
}
.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: var(--text-primary);
    text-decoration: none;
}
.brand span { color: var(--accent-blue); }
.nav-links { display: flex; gap: 24px; align-items: center; font-size: 14px; }
.nav-links a { color: var(--text-muted); text-decoration: none; transition: color 0.2s; }
.nav-links a:hover { color: var(--text-primary); }
.btn {
    background: var(--accent-blue);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: background 0.2s, box-shadow 0.2s;
}
.btn:hover { background: #2563eb; box-shadow: 0 0 15px var(--accent-glow); }
.btn-outline {
    background: transparent;
    border: 1px solid var(--card-border);
    color: var(--text-primary);
}
.btn-outline:hover { background: var(--card-bg); }
.container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; width: 100%; }
.card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; }
.badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    display: inline-block;
}
.badge-safe { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-warn { background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-danger { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.3); }
input, select, textarea {
    width: 100%;
    background: var(--bg-secondary);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 12px;
    color: white;
    font-size: 14px;
    margin-top: 6px;
    margin-bottom: 16px;
    outline: none;
}
input:focus, select:focus { border-color: var(--accent-blue); box-shadow: 0 0 8px var(--accent-glow); }
footer {
    background: var(--bg-secondary);
    border-top: 1px solid var(--card-border);
    padding: 40px 20px;
    margin-top: auto;
    text-align: center;
    color: var(--text-muted);
    font-size: 13px;
}
"""

@app.route('/')
def landing():
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>VERITRUST — Global Cybersecurity Intelligence Platform</title>
        <style>{{GLOBAL_STYLE}}</style>
    </head>
    <body>
        <nav class="navbar">
            <a href="/" class="brand">🛡️ VERI<span>TRUST</span></a>
            <div class="nav-links">
                <a href="#features">Features</a>
                <a href="/pricing">Pricing</a>
                <a href="/developers">Developers</a>
                <a href="/auth/signin" class="btn btn-outline" style="padding: 6px 14px;">Sign In</a>
                <a href="/dashboard" class="btn" style="padding: 6px 14px;">Launch Platform</a>
            </div>
        </nav>
        <div class="container" style="text-align: center; padding: 80px 20px;">
            <div style="display: inline-block; padding: 6px 16px; background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.3); border-radius: 20px; color: var(--accent-blue); font-size: 13px; font-weight: 600; margin-bottom: 20px;">
                ENTERPRISE THREAT INTELLIGENCE & DEEPFAKE DEFENSE
            </div>
            <h1 style="font-size: 48px; font-weight: 800; max-width: 800px; margin: 0 auto 20px; line-height: 1.2;">
                Trust Every Connection. Investigate Every Threat.
            </h1>
            <p style="color: var(--text-muted); font-size: 18px; max-width: 650px; margin: 0 auto 40px;">
                Advanced phone-number reputation intelligence, caller-ID spoofing investigation, voice deepfake analysis, and device cryptographic integrity verification.
            </p>
            <div style="display: flex; gap: 16px; justify-content: center; margin-bottom: 60px;">
                <a href="/dashboard/numbers" class="btn" style="font-size: 16px; padding: 14px 28px;">Scan a Number</a>
                <a href="/dashboard" class="btn btn-outline" style="font-size: 16px; padding: 14px 28px;">Explore Platform</a>
            </div>
        </div>
        <footer>
            <p>&copy; 2026 Veritrust Cyber Intelligence Inc. All rights reserved.</p>
        </footer>
    </body>
    </html>
    """)

@app.route('/dashboard')
def dashboard():
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>VERITRUST — Security Dashboard</title>
        <style>{{GLOBAL_STYLE}}
            .layout {{ display: flex; min-height: calc(100vh - 70px); }}
            .sidebar {{ width: 260px; background: var(--bg-secondary); border-right: 1px solid var(--card-border); padding: 24px; }}
            .sidebar a {{ display: block; color: var(--text-muted); text-decoration: none; padding: 12px 16px; border-radius: 8px; margin-bottom: 6px; font-weight: 500; }}
            .sidebar a:hover, .sidebar a.active {{ background: rgba(59,130,246,0.1); color: var(--accent-blue); }}
            .main-content {{ flex: 1; padding: 32px; overflow-y: auto; }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <a href="/" class="brand">🛡️ VERI<span>TRUST</span></a>
            <div class="nav-links">
                <span style="color: var(--text-muted); font-size: 13px;">Node: user_alpha_01</span>
                <a href="/" class="btn btn-outline" style="padding: 6px 12px;">Sign Out</a>
            </div>
        </nav>
        <div class="layout">
            <div class="sidebar">
                <a href="/dashboard" class="active">Overview</a>
                <a href="/dashboard/numbers">Number Intelligence</a>
                <a href="/dashboard/voice">Voice Verification</a>
                <a href="/dashboard/devices">Device Security</a>
            </div>
            <div class="main-content">
                <h1 style="font-size: 24px; margin-bottom: 8px;">Security Operations Overview</h1>
                <p style="color: var(--text-muted); margin-bottom: 24px;">Real-time telemetry and forensic intelligence status.</p>
                <div class="grid-3" style="margin-bottom: 24px;">
                    <div class="card" style="margin: 0;">
                        <div style="color: var(--text-muted); font-size: 12px;">TRUST SCORE INDEX</div>
                        <div id="metric-score" style="font-size: 32px; font-weight: 800; color: var(--accent-green); margin-top: 8px;">100.0%</div>
                    </div>
                </div>
                <div class="card">
                    <h3 style="margin-bottom: 16px;">Quick Actions</h3>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                        <a href="/dashboard/numbers" class="btn">🔍 Scan Phone Number</a>
                        <a href="/dashboard/voice" class="btn btn-outline">🎙️ Analyze Audio Memo</a>
                    </div>
                </div>
            </div>
        </div>
        <script>
            async function pollScore() {{
                try {{
                    const res = await fetch('/api/v1/score/user_alpha_01');
                    const data = await res.json();
                    if(data.status === 'success') {{
                        document.getElementById('metric-score').innerText = data.trust_score.toFixed(1) + '%';
                    }}
                }} catch(e) {{}}
            }}
            setInterval(pollScore, 3000);
        </script>
    </body>
    </html>
    """)

@app.route('/dashboard/numbers')
def numbers_page():
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>VERITRUST — Number Intelligence</title>
        <style>{{GLOBAL_STYLE}}</style>
    </head>
    <body>
        <nav class="navbar">
            <a href="/" class="brand">🛡️ VERI<span>TRUST</span></a>
            <div class="nav-links"><a href="/dashboard" class="btn btn-outline" style="padding: 6px 12px;">Dashboard</a></div>
        </nav>
        <div class="container">
            <h1>Phone Number Intelligence</h1>
            <div class="card" style="margin-top: 20px;">
                <label style="font-weight: 600;">Enter Phone Number</label>
                <div style="display: flex; gap: 12px; margin-top: 6px;">
                    <input type="text" id="phoneInput" placeholder="e.g. +233 24 123 4567" style="margin: 0;">
                    <button class="btn" onclick="scanNumber()">Scan</button>
                </div>
                <div id="scanResult" style="margin-top: 20px;"></div>
            </div>
        </div>
        <script>
            async function scanNumber() {{
                const phone = document.getElementById('phoneInput').value.trim();
                const resDiv = document.getElementById('scanResult');
                if(!phone) return;
                resDiv.innerHTML = 'Scanning...';
                try {{
                    const response = await fetch('/api/v1/check-number', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ phone_number: phone }})
                    }});
                    const data = await response.json();
                    if(data.status === 'success') {{
                        resDiv.innerHTML = `<strong>${{data.phone_number}}</strong>: ${{data.verdict}}`;
                    }}
                }} catch(e) {{
                    resDiv.innerHTML = 'Scan failed.';
                }}
            }}
        </script>
    </body>
    </html>
    """)

@app.route('/dashboard/voice')
def voice_page():
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>VERITRUST — Voice Verification</title><style>{{GLOBAL_STYLE}}</style></head>
    <body>
        <nav class="navbar"><a href="/" class="brand">🛡️ VERI<span>TRUST</span></a><div class="nav-links"><a href="/dashboard" class="btn btn-outline" style="padding: 6px 12px;">Dashboard</a></div></nav>
        <div class="container"><h1>Voice Analysis Workspace</h1><p style="color: var(--text-muted); margin-top: 10px;">Deepfake detection workspace.</p></div>
    </body>
    </html>
    """)

@app.route('/pricing')
def pricing():
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>VERITRUST — Pricing</title><style>{{GLOBAL_STYLE}}</style></head>
    <body>
        <nav class="navbar"><a href="/" class="brand">🛡️ VERI<span>TRUST</span></a><div class="nav-links"><a href="/" class="btn btn-outline" style="padding: 6px 12px;">Home</a></div></nav>
        <div class="container" style="text-align: center;"><h1>Pricing Plans</h1></div>
    </body>
    </html>
    """)

@app.route('/developers')
def developers():
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>VERITRUST — Developers</title><style>{{GLOBAL_STYLE}}</style></head>
    <body>
        <nav class="navbar"><a href="/" class="brand">🛡️ VERI<span>TRUST</span></a><div class="nav-links"><a href="/dashboard" class="btn btn-outline" style="padding: 6px 12px;">Dashboard</a></div></nav>
        <div class="container"><h1>Developer API Documentation</h1></div>
    </body>
    </html>
    """)

@app.route('/auth/signin')
def signin():
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>VERITRUST — Sign In</title><style>{{GLOBAL_STYLE}}</style></head>
    <body>
        <div class="container" style="max-width: 400px; margin-top: 80px;">
            <div class="card">
                <h2>Sign In</h2>
                <input type="email" placeholder="Email">
                <input type="password" placeholder="Password">
                <a href="/dashboard" class="btn" style="width: 100%; justify-content: center; margin-top: 10px;">Sign In</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route('/api/v1/register', methods=['POST'])
def register_user():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    device_hardware_hash = data.get('device_hardware_hash')
    public_key = data.get('public_key')
    if not all([user_id, device_hardware_hash, public_key]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO users (user_id, device_hardware_hash, public_key, trust_score, created_at) VALUES (?, ?, ?, 100.0, ?)', (user_id, device_hardware_hash, public_key, time.time()))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "User registered successfully", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/check-number', methods=['POST'])
def check_number():
    data = request.get_json() or {}
    phone_number = data.get('phone_number')
    if not phone_number:
        return jsonify({"status": "error", "message": "Missing phone number"}), 400
    clean_num = phone_number.replace(" ", "").replace("-", "")
    verdict = "SPOOF DETECTED" if (clean_num.endswith("0000") or "1234" in clean_num) else "PASSED"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO call_logs (phone_number, verdict, timestamp) VALUES (?, ?, ?)", (phone_number, verdict, time.time()))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "phone_number": phone_number, "verdict": verdict}), 200

@app.route('/api/v1/score/<user_id>', methods=['GET'])
def get_user_score(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT trust_score FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"status": "success", "trust_score": 100.0})
    return jsonify({"status": "success", "trust_score": row['trust_score']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
