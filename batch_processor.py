import os
import time
import logging
from backend.spectrograms import generate_spectrograms
from backend.features import extract_all_features
from backend.utils import get_upload_path

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
                
                # Update current file
                with self.batch_status['lock']:
                    self.batch_status['data'][self.session_id]['current_file'] = file_name
                
                file_path = get_upload_path(self.session_id, file_name, self.config)
                
                try:
                    # Generate spectrograms
                    spectrogram_results = generate_spectrograms(
                        file_path, self.selected_types, self.results_dir, 
                        os.path.splitext(original_name)[0]
                    )
                    
                    # Extract features
                    features = extract_all_features(file_path)
                    if features:
                        features['filename'] = original_name
                        features['session_id'] = self.session_id
                        all_features.append(features)
                    
                    logging.info(f"Processed {file_name} successfully")
                    
                except Exception as e:
                    error_msg = f"Error processing {file_name}: {str(e)}"
                    logging.error(error_msg)
                    
                    # Add error to batch status
                    with self.batch_status['lock']:
                        self.batch_status['data'][self.session_id]['errors'].append({
                            'file': file_name,
                            'message': str(e)
                        })
                
                # Update progress
                with self.batch_status['lock']:
                    self.batch_status['data'][self.session_id]['processed_count'] = i + 1
                    logging.debug(f"Processed count for {self.session_id}: {i + 1}")
            
            # Save aggregated features
            self._save_features(all_features)
            
            # Mark as completed
            with self.batch_status['lock']:
                self.batch_status['data'][self.session_id].update({
                    'status': 'completed',
                    'current_file': None,
                    'end_time': time.time()
                })
                logging.debug(f"Status for {self.session_id} set to completed")
                
        except Exception as e:
            logging.error(f"Batch processing failed for {self.session_id}: {e}")
            
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
