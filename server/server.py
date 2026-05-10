from flask import Flask, request, jsonify, send_from_directory, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import crawler

RATE_LIMIT = "5/minute"  # requests per minute and IP address

app = Flask(__name__, static_folder='../client', static_url_path='/static')
# limiter = Limiter(app, key_func=lambda: request.remote_addr)
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route('/', methods=['GET'])
def home():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/find_path', methods=['Get', 'POST'])
@limiter.limit(RATE_LIMIT)  # Use the new constant instead of the hardcoded rate limit
def find_path():
    start_title = ""
    target_title = ""
    try:
        start_title, target_title = crawler.generate_puzzle(steps= 2, lang= "en")
        start_url = crawler.make_url(start_title, "en")
        target_url = crawler.make_url(target_title, "en")
 
        path, logs, time, discovered = crawler.find_path(start_url, target_url)
        elapsed_time = logs[-1]
        return jsonify({
            'start_title': start_title,
            'target_title': target_title,
            'start_url': start_url,
            'target_url': target_url,
            'path': path, 
            'logs': logs, 
            'time': elapsed_time, 
            'discovered': discovered
        })
    except crawler.TimeoutErrorWithLogs as e:
        app.logger.error(f"Error occurred: {e}")
        return jsonify({
            'error': str(e), 
            'start_title': start_title,
            'target_title': target_title,
            'logs': e.logs, 
            'time': e.time, 
            'discovered': e.discovered
        }), 408
    except Exception as e:
        app.logger.error(f"Error occurred: {e}")
        return jsonify({'error': 'An error occurred while finding path', 'logs': logs, 'time': time, 'discovered': discovered}), 500


# @app.route('/static/<path:path>')
# def send_static(path):
#     return send_from_directory(app.static_folder, path)

# @app.route('/logs', methods=['GET'])
# def stream_logs():
#     def generate():
#         for log in logs:
#             yield f"data: {log}\n\n"
#     return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)
