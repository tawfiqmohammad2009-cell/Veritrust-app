from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "system": "VeriTrust Security Suite",
        "message": "Python backend is active and listening for native app requests."
    })

@app.route('/log_call', methods=['POST'])
def log_call():
    data = request.get_json() or {}
    phone_number = data.get('phone_number', '').strip()
    
    if not phone_number:
        return jsonify({'status': 'error', 'message': 'No phone number provided'}), 400

    print(f"[!] Intercepted Live Call: {phone_number}")
    return jsonify({'status': 'success', 'message': f'Logged {phone_number}'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
