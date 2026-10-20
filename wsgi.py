import time
import hashlib
import secrets
from flask import Flask, request, jsonify, render_template_string
import ecdsa
from ecdsa import VerifyingKey, BadSignatureError
import sqlite3

from features import extract_log_mel_spectrogram
from inference import DeepfakeDetector

app = Flask(__name__)
DB_PATH = "veritrust.db"

# Initialize TFLite deepfake detector safely
try:
    detector = DeepfakeDetector("veritrust_audio.tflite")
    MODEL_LOADED = True
except Exception as e:
    print(f"[Warning] TFLite model not loaded: {e}. Running in simulation/fallback mode.")
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
            trust_score REAL DEFAULT 100.0
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on module load for Gunicorn
init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Veritrust Mobile HUD</title>
        <style>
            :root {
                --bg-color: #0b0f19;
                --card-bg: #111827;
                --accent-green: #10b981;
                --accent-red: #ef4444;
                --accent-blue: #3b82f6;
                --text-color: #f3f4f6;
                --text-muted: #9ca3af;
            }
            body {
                background-color: var(--bg-color);
                color: var(--text-color);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 16px;
            }
            .hud-container { max-width: 480px; margin: 0 auto; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
            .title { font-size: 22px; font-weight: 700; color: var(--accent-blue); letter-spacing: 1px; }
            .card { background: var(--card-bg); border-radius: 16px; padding: 20px; margin-bottom: 16px; border: 1px solid #1f2937; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
            .shield-toggle { display: flex; justify-content: space-between; align-items: center; }
            .switch { position: relative; display: inline-block; width: 50px; height: 26px; }
            .switch input { opacity: 0; width: 0; height: 0; }
            .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #374151; transition: .4s; border-radius: 34px; }
            .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }
            input:checked + .slider { background-color: var(--accent-green); }
            input:checked + .slider:before { transform: translateX(24px); }
            .overlay-hud { background: rgba(17, 24, 39, 0.95); border: 2px solid var(--accent-blue); border-radius: 12px; padding: 16px; text-align: center; backdrop-filter: blur(8px); }
            .hud-status { font-size: 18px; font-weight: 800; margin-top: 8px; }
            .status-safe { color: var(--accent-green); }
            .status-warn { color: var(--accent-red); }
            .score-bar-bg { background: #374151; height: 10px; border-radius: 5px; margin-top: 12px; overflow: hidden; }
            .score-bar-fill { background: var(--accent-green); height: 100%; width: 100%; transition: width 0.5s ease; }
            .log-list { list-style: none; padding: 0; margin: 0; font-size: 14px; }
            .log-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #1f2937; }
            .log-item:last-child { border-bottom: none; }
        </style>
    </head>
    <body>
        <div class="hud-container">
            <div class="header">
                <div class="title">VERITRUST</div>
                <span style="font-size: 12px; color: var(--accent-green);">● SYSTEM ONLINE</span>
            </div>
            <div class="card overlay-hud" id="hud-banner">
                <div style="font-size: 12px; color: var(--text-muted); letter-spacing: 1.5px;">IN-CALL FORENSIC HUD</div>
                <div class="hud-status status-safe" id="hud-status-text">VERIFIED HUMAN</div>
                <div class="score-bar-bg">
                    <div class="score-bar-fill" id="trust-bar" style="width: 100%;"></div>
                </div>
                <div style="font-size: 12px; margin-top: 8px; color: var(--text-muted);" id="hud-score-label">Trust Score: 100.0%</div>
            </div>
            <div class="card shield-toggle">
                <div>
                    <div style="font-weight: 600;">Active Identity Shield</div>
                    <div style="font-size: 12px; color: var(--text-muted);">Real-time aarch64 deepfake guard</div>
                </div>
                <label class="switch">
                    <input type="checkbox" checked>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="card">
                <div style="font-weight: 600; margin-bottom: 12px;">Call Safety History</div>
                <ul class="log-list">
                    <li class="log-item">
                        <span>Incoming Call (+233 24 *** 8901)</span>
                        <span style="color: var(--accent-green); font-weight: 600;">PASSED</span>
                    </li>
                    <li class="log-item">
                        <span>Voice Memo Analysis</span>
                        <span style="color: var(--accent-green); font-weight: 600;">PASSED</span>
                    </li>
                    <li class="log-item">
                        <span>Unknown Caller (+233 55 *** 1234)</span>
                        <span style="color: var(--accent-red); font-weight: 600;">SPOOF DETECTED</span>
                    </li>
                </ul>
            </div>
            <div class="card">
                <div style="font-weight: 600; margin-bottom: 12px;">Settings & Security</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px;">
                    <span style="color: var(--text-muted);">Key Management:</span>
                    <span style="color: var(--accent-blue); font-family: monospace;">secp256k1 [Active]</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px;">
                    <span style="color: var(--text-muted);">Emergency Alerts:</span>
                    <span style="color: var(--accent-green);">ENABLED</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 14px;">
                    <span style="color: var(--text-muted);">Node License:</span>
                    <span style="color: var(--text-color); font-weight: 600;">Veritrust Native Node</span>
                </div>
            </div>
        </div>
        <script>
            async function pollTrustScore() {
                try {
                    const response = await fetch('/api/v1/score/user_alpha_01');
                    const data = await response.json();
                    if (data.status === 'success') {
                        const score = data.trust_score;
                        document.getElementById('trust-bar').style.width = score + '%';
                        document.getElementById('hud-score-label').innerText = 'Trust Score: ' + score.toFixed(1) + '%';
                        const statusText = document.getElementById('hud-status-text');
                        if (score < 50.0) {
                            statusText.innerText = 'WARNING: DEEPFAKE DETECTED';
                            statusText.className = 'hud-status status-warn';
                            document.getElementById('trust-bar').style.backgroundColor = '#ef4444';
                        } else {
                            statusText.innerText = 'VERIFIED HUMAN';
                            statusText.className = 'hud-status status-safe';
                            document.getElementById('trust-bar').style.backgroundColor = '#10b981';
                        }
                    }
                } catch (e) {
                    console.log('Syncing...');
                }
            }
            setInterval(pollTrustScore, 2000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

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
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, device_hardware_hash, public_key, trust_score)
            VALUES (?, ?, ?, 100.0)
        ''', (user_id, device_hardware_hash, public_key))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "User registered successfully", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/handshake/initiate', methods=['POST'])
def initiate_hardware_handshake():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT device_hardware_hash FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"status": "error", "message": "User not found"}), 404
    challenge_nonce = secrets.token_hex(16)
    ACTIVE_CHALLENGES[user_id] = {
        "nonce": challenge_nonce,
        "expires_at": time.time() + 300
    }
    return jsonify({
        "status": "success",
        "user_id": user_id,
        "challenge_nonce": challenge_nonce,
        "message": "Hardware handshake initiated successfully."
    }), 200

@app.route('/api/v1/handshake/verify', methods=['POST'])
def verify_hardware_handshake():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    device_hardware_hash = data.get('device_hardware_hash')
    if not all([user_id, device_hardware_hash]):
        return jsonify({"status": "error", "message": "Missing user_id or hardware hash"}), 400
    if user_id not in ACTIVE_CHALLENGES:
        return jsonify({"status": "error", "message": "No active handshake session found. Initiate first."}), 400
    session = ACTIVE_CHALLENGES[user_id]
    if time.time() > session["expires_at"]:
        del ACTIVE_CHALLENGES[user_id]
        return jsonify({"status": "error", "message": "Handshake session expired."}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT device_hardware_hash, trust_score FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"status": "error", "message": "User not found"}), 404
    if device_hardware_hash != row['device_hardware_hash']:
        return jsonify({"status": "failed", "hardware_status": "MISMATCH", "message": "Device hardware hash verification failed."}), 403
    del ACTIVE_CHALLENGES[user_id]
    return jsonify({"status": "success", "hardware_status": "VERIFIED", "user_id": user_id, "trust_score": row['trust_score']}), 200

@app.route('/api/v1/handshake/dual-verify', methods=['POST'])
def dual_verify_handshake():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    token = data.get('token')
    signature_hex = data.get('signature')
    if not all([user_id, token, signature_hex]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    try:
        nonce, timestamp_str = token.split(":")
        timestamp = int(timestamp_str)
    except (ValueError, AttributeError):
        return jsonify({"status": "error", "message": "Invalid token format."}), 400
    if abs(int(time.time()) - timestamp) > 300:
        return jsonify({"status": "error", "message": "Token expired"}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT public_key, trust_score FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"status": "error", "message": "User not found"}), 404
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(row['public_key']), curve=ecdsa.SECP256k1)
        is_valid = vk.verify_digest(bytes.fromhex(signature_hex), hashlib.sha256(token.encode('utf-8')).digest())
    except Exception as e:
        return jsonify({"status": "failed", "cryptographic_status": "INVALID", "message": str(e)}), 403
    if is_valid:
        return jsonify({"status": "success", "cryptographic_status": "VERIFIED", "user_id": user_id, "trust_score": row['trust_score']}), 200
    return jsonify({"status": "failed", "cryptographic_status": "REJECTED"}), 403

@app.route('/api/v1/verify-audio', methods=['POST'])
def verify_audio():
    if request.content_type == 'application/octet-stream' or (request.data and not request.is_json):
        audio_bytes = request.data
        if not audio_bytes:
            return jsonify({"status": "error", "message": "Empty audio payload"}), 400
        user_id = request.headers.get('X-User-ID', 'user_alpha_01')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trust_score FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        current_score = row['trust_score'] if row else 100.0
        if not row:
            cursor.execute("INSERT OR IGNORE INTO users (user_id, trust_score) VALUES (?, ?)", (user_id, 100.0))
            conn.commit()

        if MODEL_LOADED:
            features = extract_log_mel_spectrogram(audio_bytes)
            spoof_score = detector.predict(features)
            verdict = "SPOOF" if spoof_score > 0.65 else "BONAFIDE"
        else:
            spoof_score = 0.1234
            verdict = "BONAFIDE"

        new_score = max(0.0, current_score - 15.0) if verdict == "SPOOF" else min(100.0, current_score + 2.0)
        cursor.execute("UPDATE users SET trust_score = ? WHERE user_id = ?", (new_score, user_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "user_id": user_id, "verdict": verdict, "spoof_score": round(spoof_score, 4), "updated_trust_score": new_score}), 200
    else:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'user_alpha_01')
        verdict = data.get('verdict', 'BONAFIDE').upper()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trust_score FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        current_score = row['trust_score'] if row else 100.0
        if not row:
            cursor.execute("INSERT OR IGNORE INTO users (user_id, trust_score) VALUES (?, ?)", (user_id, 100.0))
            conn.commit()

        new_score = max(0.0, current_score - 15.0) if verdict == "SPOOF" else min(100.0, current_score + 2.0)
        cursor.execute("UPDATE users SET trust_score = ? WHERE user_id = ?", (new_score, user_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "user_id": user_id, "verdict": verdict, "updated_trust_score": new_score}), 200

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
