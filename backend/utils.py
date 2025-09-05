import os
import shutil
import zipfile
import csv
import logging
from config import get_config

def save_uploaded_files(files, session_id):
    """Save uploaded files to session directory."""
    config = get_config()
    upload_dir = os.path.join(config['UPLOAD_FOLDER'], session_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    saved_files = []
    for file in files:
        if file.filename:
            filename = file.filename
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            saved_files.append({
                'original_name': filename,
                'saved_name': filename,
                'path': file_path
            })
    
    return saved_files

def get_upload_path(session_id, filename, config):
    """Get the full path to an uploaded file."""
    return os.path.join(config['UPLOAD_FOLDER'], session_id, filename)

def create_zip_for_spectrograms(session_id, config):
    """
    Create ZIP file containing generated spectrograms and manifest.
    
    Returns:
        str: Path to created ZIP file or None if no spectrograms found
    """
    results_dir = os.path.join(config['RESULTS_FOLDER'], session_id)
    
    if not os.path.exists(results_dir):
        return None
    
    # Find all PNG files (spectrograms)
    png_files = [f for f in os.listdir(results_dir) if f.endswith('.png')]
    
    if not png_files:
        return None
    
    zip_path = os.path.join(results_dir, f'spectrograms_{session_id}.zip')
    manifest_rows = []
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add spectrogram images
            for png_file in png_files:
                file_path = os.path.join(results_dir, png_file)
                
                # Parse filename: original_basename__spec_type.png
                if '__' in png_file:
                    parts = png_file.rsplit('__', 1)
                    if len(parts) == 2:
                        original_basename = parts[0]
                        spec_type_ext = parts[1]  # spec_type.png
                        spec_type = spec_type_ext.replace('.png', '')
                        
                        # Archive path format: {session_id}/{original_basename}__{spec_type}.png
                        archive_path = f"{session_id}/{png_file}"
                        
                        zipf.write(file_path, archive_path)
                        
                        manifest_rows.append({
                            'file': original_basename,
                            'spectrogram_type': spec_type,
                            'archive_path': archive_path,
                            'status': 'success',
                            'error': ''
                        })
            
            # Create and add manifest.csv
            manifest_path = os.path.join(results_dir, 'manifest.csv')
            with open(manifest_path, 'w', newline='', encoding='utf-8') as csvfile:
                if manifest_rows:
                    fieldnames = ['file', 'spectrogram_type', 'archive_path', 'status', 'error']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(manifest_rows)
            
            # Add manifest to ZIP
            zipf.write(manifest_path, 'manifest.csv')
        
        logging.info(f"Created ZIP file: {zip_path} with {len(png_files)} spectrograms")
        return zip_path
        
    except Exception as e:
        logging.error(f"Error creating ZIP file for {session_id}: {e}")
        return None

def clear_session(session_id):
    """Remove all files and directories for a session."""
    config = get_config()
    
    # Clear upload directory
    upload_dir = os.path.join(config['UPLOAD_FOLDER'], session_id)
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
        logging.info(f"Cleared upload directory: {upload_dir}")
    
    # Clear results directory
    results_dir = os.path.join(config['RESULTS_FOLDER'], session_id)
    if os.path.exists(results_dir):
        shutil.rmtree(results_dir)
        logging.info(f"Cleared results directory: {results_dir}")
