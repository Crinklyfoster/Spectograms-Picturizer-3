import os
import uuid
import threading
import logging
from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename

from config import get_config
from validators import allowed_extension, validate_duration
from batch_processor import BatchProcessor
from backend.utils import save_uploaded_files, clear_session

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Single shared state object - CRITICAL: all access must use the lock
batch_status = {'data': {}, 'lock': threading.Lock()}

@app.route('/')
def index():
    return render_template('index.html', config=get_config())

@app.route('/upload_files_only', methods=['POST'])
def upload_files_only():
    config = get_config()
    
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    
    if len(files) > config['MAX_FILES_PER_BATCH']:
        return jsonify({
            'error': f'Too many files. Maximum {config["MAX_FILES_PER_BATCH"]} files per batch.'
        }), 400
    
    if not files or (len(files) == 1 and files[0].filename == ''):
        return jsonify({'error': 'No files selected'}), 400
    
    session_id = str(uuid.uuid4())
    upload_path = os.path.join(config['UPLOAD_FOLDER'], session_id)
    os.makedirs(upload_path, exist_ok=True)
    
    file_results = []
    session_files = []
    
    for file in files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        result = {'filename': filename, 'accepted': False}
        
        if not allowed_extension(filename):
            result['reason'] = f'File type not allowed. Allowed: {config["ALLOWED_EXTENSIONS"]}'
            file_results.append(result)
            continue
        
        # Save file temporarily to check duration
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Validate duration server-side
        duration_valid, reason = validate_duration(file_path)
        
        if not duration_valid:
            os.remove(file_path)  # Remove rejected file
            result['reason'] = reason
            result['duration_seconds'] = None
        else:
            # Get actual duration for accepted file
            from validators import get_duration_seconds
            duration = get_duration_seconds(file_path)
            result['accepted'] = True
            result['duration_seconds'] = duration
            session_files.append({
                'original_name': filename,
                'saved_name': filename,
                'duration_seconds': duration
            })
        
        file_results.append(result)
    
    # Store session files info under lock
    if session_files:
        with batch_status['lock']:
            batch_status['data'][session_id] = {
                'files': session_files,
                'upload_time': __import__('time').time()
            }
            logging.debug(f"Session {session_id} created with {len(session_files)} files")
    else:
        # Clean up empty session directory
        import shutil
        shutil.rmtree(upload_path, ignore_errors=True)
    
    return jsonify({
        'session_id': session_id if session_files else None,
        'files': file_results
    })

@app.route('/manage_files')
def manage_files():
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('index'))
    
    with batch_status['lock']:
        session_data = batch_status['data'].get(session_id)
    
    if not session_data:
        return redirect(url_for('index'))
    
    return render_template('manage_files.html', 
                         config=get_config(), 
                         session_id=session_id,
                         files=session_data.get('files', []))

@app.route('/remove_file', methods=['POST'])
def remove_file():
    data = request.get_json()
    session_id = data.get('session_id')
    saved_name = data.get('saved_name')
    
    if not session_id or not saved_name:
        return jsonify({'error': 'Missing session_id or saved_name'}), 400
    
    config = get_config()
    file_path = os.path.join(config['UPLOAD_FOLDER'], session_id, saved_name)
    
    with batch_status['lock']:
        session_data = batch_status['data'].get(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        # Remove file from filesystem
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from session data
        session_data['files'] = [f for f in session_data['files'] if f['saved_name'] != saved_name]
        logging.debug(f"File {saved_name} removed from session {session_id}")
    
    return jsonify({'removed': True})

@app.route('/process_uploaded_files', methods=['POST'])
def process_uploaded_files():
    data = request.get_json()
    session_id = data.get('session_id')
    selected_types = data.get('selected_types', [])
    
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400
    
    if not selected_types:
        return jsonify({'error': 'No spectrogram types selected'}), 400
    
    config = get_config()
    valid_types = config['AVAILABLE_SPECTROGRAMS']
    
    # Validate selected types
    for spec_type in selected_types:
        if spec_type not in valid_types:
            return jsonify({'error': f'Invalid spectrogram type: {spec_type}'}), 400
    
    with batch_status['lock']:
        session_data = batch_status['data'].get(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        files = session_data.get('files', [])
        if not files:
            return jsonify({'error': 'No files to process'}), 400
        
        # Initialize processing status
        batch_status['data'][session_id].update({
            'status': 'queued',
            'total_files': len(files),
            'processed_count': 0,
            'current_file': None,
            'errors': [],
            'start_time': __import__('time').time(),
            'end_time': None,
            'selected_types': selected_types
        })
        logging.debug(f"Status for {session_id} set to queued")
    
    # Start background processing
    processor = BatchProcessor(session_id, files, selected_types, batch_status, config)
    thread = threading.Thread(target=processor.process, daemon=True)
    thread.start()
    
    return jsonify({'started': True, 'session_id': session_id})

@app.route('/batch_status')
def get_batch_status():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400
    
    with batch_status['lock']:
        session_data = batch_status['data'].get(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        status = session_data.get('status', 'unknown')
        processed = session_data.get('processed_count', 0)
        total = session_data.get('total_files', 0)
        
        progress_percent = (processed / total * 100) if total > 0 else 0
        
        return jsonify({
            'status': status,
            'processed_count': processed,
            'total_files': total,
            'current_file': session_data.get('current_file'),
            'progress_percent': progress_percent,
            'errors': session_data.get('errors', []),
            'end_time': session_data.get('end_time')
        })

@app.route('/results/<session_id>')
def results(session_id):
    with batch_status['lock']:
        session_data = batch_status['data'].get(session_id)
    
    if not session_data:
        return redirect(url_for('index'))
    
    config = get_config()
    results_path = os.path.join(config['RESULTS_FOLDER'], session_id)
    
    # Check for generated spectrograms
    spectrograms = []
    if os.path.exists(results_path):
        for filename in os.listdir(results_path):
            if filename.endswith('.png'):
                spectrograms.append(filename)
    
    # Check for features files
    features_csv_exists = os.path.exists(os.path.join(results_path, 'features.csv'))
    features_json_exists = os.path.exists(os.path.join(results_path, 'features.json'))
    
    return render_template('batch_results.html',
                         config=get_config(),
                         session_id=session_id,
                         spectrograms=spectrograms,
                         features_csv_exists=features_csv_exists,
                         features_json_exists=features_json_exists,
                         session_data=session_data)

@app.route('/download_features/<session_id>')
def download_features(session_id):
    format_type = request.args.get('format', 'csv')
    
    if format_type not in ['csv', 'json']:
        return jsonify({'error': 'Invalid format. Use csv or json'}), 400
    
    config = get_config()
    file_path = os.path.join(config['RESULTS_FOLDER'], session_id, f'features.{format_type}')
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'Features {format_type} file not found'}), 404
    
    return send_file(file_path, as_attachment=True, 
                    download_name=f'features_{session_id}.{format_type}')

@app.route('/download_spectrograms/<session_id>')
def download_spectrograms(session_id):
    config = get_config()
    from backend.utils import create_zip_for_spectrograms
    
    with batch_status['lock']:
        session_data = batch_status['data'].get(session_id)
    
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    zip_path = create_zip_for_spectrograms(session_id, config)
    
    if not zip_path or not os.path.exists(zip_path):
        return jsonify({'error': 'No spectrograms available for download'}), 404
    
    return send_file(zip_path, as_attachment=True, 
                    download_name=f'spectrograms_{session_id}.zip')

@app.route('/delete_session/<session_id>', methods=['POST'])
def delete_session(session_id):
    try:
        clear_session(session_id)
        
        with batch_status['lock']:
            if session_id in batch_status['data']:
                del batch_status['data'][session_id]
                logging.debug(f"Session {session_id} deleted from batch_status")
        
        return jsonify({'deleted': True})
    except Exception as e:
        logging.error(f"Error deleting session {session_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/batch_progress')
def batch_progress():
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('index'))
    
    with batch_status['lock']:
        session_data = batch_status['data'].get(session_id)
    
    if not session_data:
        return redirect(url_for('index'))
    
    return render_template('batch_progress.html', config=get_config(), session_id=session_id)


if __name__ == '__main__':
    # Ensure directories exist
    config = get_config()
    os.makedirs(config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(config['RESULTS_FOLDER'], exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
