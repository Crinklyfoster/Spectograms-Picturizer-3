import os
import time
import logging
import signal
from contextlib import contextmanager
from backend.spectrograms import generate_spectrograms
from backend.features import extract_all_features
from backend.utils import get_upload_path

@contextmanager
def timeout_handler(seconds):
    """Context manager to timeout long-running operations."""
    def timeout_signal(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler and a alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_signal)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the old signal handler
        signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)

class BatchProcessor:
    """
    Sequential batch processor for audio files.
    Processes files one-by-one in a single background thread.
    Updates shared batch_status under lock.
    """
    
    def __init__(self, session_id, file_list, selected_types, batch_status_ref, config):
        self.session_id = session_id
        self.file_list = file_list
        self.selected_types = selected_types
        self.batch_status = batch_status_ref
        self.config = config
        self.results_dir = os.path.join(config['RESULTS_FOLDER'], session_id)
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def process(self):
        """Main processing method - runs in background thread."""
        try:
            # Set status to running
            with self.batch_status['lock']:
                self.batch_status['data'][self.session_id]['status'] = 'running'
                logging.debug(f"Status for {self.session_id} set to running")
            
            all_features = []
            
            # Process each file sequentially
            for i, file_info in enumerate(self.file_list):
                file_name = file_info['saved_name']
                original_name = file_info['original_name']
                
                logging.info(f"Starting processing file {i+1}/{len(self.file_list)}: {file_name}")
                
                # Update current file
                with self.batch_status['lock']:
                    self.batch_status['data'][self.session_id]['current_file'] = file_name
                    logging.debug(f"Current file for {self.session_id}: {file_name}")
                
                file_path = get_upload_path(self.session_id, file_name, self.config)
                
                # Check if file exists
                if not os.path.exists(file_path):
                    error_msg = f"File not found: {file_path}"
                    logging.error(error_msg)
                    
                    with self.batch_status['lock']:
                        self.batch_status['data'][self.session_id]['errors'].append({
                            'file': file_name,
                            'message': error_msg
                        })
                    continue
                
                try:
                    logging.info(f"Generating spectrograms for {file_name}")
                    
                    # Generate spectrograms with timeout protection
                    try:
                        with timeout_handler(300):  # 5 minute timeout per file
                            spectrogram_results = generate_spectrograms(
                                file_path, self.selected_types, self.results_dir, 
                                os.path.splitext(original_name)[0]
                            )
                    except TimeoutError as e:
                        raise Exception(f"Processing timeout: {str(e)}")
                    
                    logging.info(f"Generated {len(spectrogram_results)} spectrograms for {file_name}")
                    
                    # Extract features with timeout protection
                    logging.info(f"Extracting features for {file_name}")
                    try:
                        with timeout_handler(120):  # 2 minute timeout for features
                            features = extract_all_features(file_path)
                    except TimeoutError as e:
                        raise Exception(f"Feature extraction timeout: {str(e)}")
                    
                    if features:
                        features['filename'] = original_name
                        features['session_id'] = self.session_id
                        all_features.append(features)
                        logging.info(f"Extracted features for {file_name}")
                    else:
                        logging.warning(f"No features extracted for {file_name}")
                    
                    logging.info(f"Completed processing {file_name} successfully")
                    
                except Exception as e:
                    error_msg = f"Error processing {file_name}: {str(e)}"
                    logging.error(error_msg, exc_info=True)
                    
                    # Add error to batch status
                    with self.batch_status['lock']:
                        self.batch_status['data'][self.session_id]['errors'].append({
                            'file': file_name,
                            'message': str(e)
                        })
                
                # CRITICAL: Update progress after each file (regardless of success/failure)
                with self.batch_status['lock']:
                    self.batch_status['data'][self.session_id]['processed_count'] = i + 1
                    logging.debug(f"Updated processed count for {self.session_id}: {i + 1}/{len(self.file_list)}")
            
            # Save aggregated features
            try:
                logging.info(f"Saving {len(all_features)} feature sets")
                self._save_features(all_features)
            except Exception as e:
                logging.error(f"Error saving features: {e}")
                with self.batch_status['lock']:
                    self.batch_status['data'][self.session_id]['errors'].append({
                        'file': 'FEATURE_SAVE',
                        'message': f"Error saving features: {str(e)}"
                    })
            
            # Mark as completed
            with self.batch_status['lock']:
                self.batch_status['data'][self.session_id].update({
                    'status': 'completed',
                    'current_file': None,
                    'end_time': time.time()
                })
                logging.debug(f"Status for {self.session_id} set to completed")
                logging.info(f"Batch processing completed for {self.session_id}")
                
        except Exception as e:
            logging.error(f"Batch processing failed for {self.session_id}: {e}", exc_info=True)
            
            # Mark as failed
            with self.batch_status['lock']:
                self.batch_status['data'][self.session_id].update({
                    'status': 'failed',
                    'current_file': None,
                    'end_time': time.time()
                })
                self.batch_status['data'][self.session_id]['errors'].append({
                    'file': 'BATCH_PROCESSOR',
                    'message': f"Batch processing failed: {str(e)}"
                })
                logging.debug(f"Status for {self.session_id} set to failed")
    
    def _save_features(self, features_list):
        """Save extracted features to CSV and JSON files."""
        if not features_list:
            return
        
        import pandas as pd
        import json
        
        try:
            # Convert to DataFrame and save as CSV
            df = pd.DataFrame(features_list)
            csv_path = os.path.join(self.results_dir, 'features.csv')
            df.to_csv(csv_path, index=False)
            
            # Save as JSON
            json_path = os.path.join(self.results_dir, 'features.json')
            with open(json_path, 'w') as f:
                json.dump(features_list, f, indent=2)
            
            logging.info(f"Features saved for {self.session_id}: {len(features_list)} files")
            
        except Exception as e:
            logging.error(f"Error saving features for {self.session_id}: {e}")
