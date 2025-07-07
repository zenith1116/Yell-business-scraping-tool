from flask import Flask, render_template, request, jsonify, send_file, url_for
from flask_cors import CORS
import threading
from scraper import run_scraper, scraping_status
import os

app = Flask(__name__, static_folder='static')
CORS(app)

scraping_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    global scraping_thread
    if not scraping_status["is_running"]:
        query = request.json.get('query', '')
        num_websites = int(request.json.get('num_websites', 10))
        scraping_status["log"] = []  # Reset log
        scraping_thread = threading.Thread(target=run_scraper, args=(scraping_status, query, num_websites))
        scraping_thread.start()
        return jsonify({"status": "Scraping started"}), 202
    else:
        return jsonify({"status": "Scraping already in progress"}), 400

@app.route('/stop_scraping', methods=['POST'])
def stop_scraping():
    global scraping_thread
    if scraping_status["is_running"]:
        scraping_status["stop_requested"] = True
        if scraping_thread:
            scraping_thread.join()
        return jsonify({"status": "Scraping stopped"}), 200
    else:
        return jsonify({"status": "No scraping in progress"}), 400

@app.route('/scraping_status')
def get_scraping_status():
    return jsonify(scraping_status)

@app.route('/download_csv')
def download_csv():
    if os.path.exists('emails.csv'):
        return send_file('emails.csv', as_attachment=True)
    else:
        return jsonify({"error": "CSV file not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)