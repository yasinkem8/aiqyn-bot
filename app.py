from flask import Flask, jsonify
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "AIQYN Bot is running!", "version": "1.0"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    app.run(host='0.0.0.0', port=8000, debug=False)

# Запускаем Flask в отдельном потоке
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
