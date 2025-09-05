document.addEventListener('DOMContentLoaded', function() {
    const sessionId = document.getElementById('sessionId').value;
    const statusText = document.getElementById('statusText');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const fileCount = document.getElementById('fileCount');
    const currentFileSection = document.getElementById('currentFileSection');
    const currentFileName = document.getElementById('currentFileName');
    const logContainer = document.getElementById('logContainer');
    const errorsSection = document.getElementById('errorsSection');
    const errorsList = document.getElementById('errorsList');
    
    let pollInterval;
    let isCompleted = false;
    
    function addLogEntry(message, type = 'info') {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    
    function updateProgress(data) {
        const { status, processed_count, total_files, current_file, progress_percent, errors, end_time } = data;
        
        // Update status
        statusText.textContent = getStatusText(status);
        
        // Update progress bar
        progressFill.style.width = `${progress_percent}%`;
        progressText.textContent = `${Math.round(progress_percent)}%`;
        fileCount.textContent = `${processed_count} / ${total_files} files`;
        
        // Update current file
        if (current_file) {
            currentFileName.textContent = current_file;
            currentFileSection.style.display = 'block';
        } else {
            currentFileSection.style.display = 'none';
        }
        
        // Update errors
        if (errors && errors.length > 0) {
            errorsSection.style.display = 'block';
            errorsList.innerHTML = '';
            errors.forEach(error => {
                const errorItem = document.createElement('div');
                errorItem.className = 'error-item';
                errorItem.innerHTML = `<strong>${error.file}:</strong> ${error.message}`;
                errorsList.appendChild(errorItem);
            });
        }
        
        // Handle completion
        if (status === 'completed' || status === 'failed') {
            if (!isCompleted) {
                isCompleted = true;
                clearInterval(pollInterval);
                
                if (status === 'completed') {
                    addLogEntry('Processing completed successfully!', 'success');
                    setTimeout(() => {
                        window.location.href = `/results/${sessionId}`;
                    }, 2000);
                } else {
                    addLogEntry('Processing failed. Check errors above.', 'error');
                }
            }
        }
    }
    
    function getStatusText(status) {
        switch (status) {
            case 'queued':
                return 'Queued for processing...';
            case 'running':
                return 'Processing files...';
            case 'completed':
                return 'Processing completed!';
            case 'failed':
                return 'Processing failed!';
            default:
                return 'Unknown status';
        }
    }
    
    function pollBatchStatus() {
        fetch(`/batch_status?session_id=${sessionId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addLogEntry(`Error: ${data.error}`, 'error');
                    clearInterval(pollInterval);
                    return;
                }
                
                updateProgress(data);
                
                // Log progress updates
                if (data.current_file) {
                    addLogEntry(`Processing: ${data.current_file}`);
                }
            })
            .catch(error => {
                console.error('Error polling status:', error);
                addLogEntry(`Polling error: ${error.message}`, 'error');
            });
    }
    
    // Start polling immediately and then every 2 seconds
    addLogEntry('Starting batch processing...');
    pollBatchStatus();
    pollInterval = setInterval(pollBatchStatus, 2000);
    
    // Stop polling when page is unloaded
    window.addEventListener('beforeunload', function() {
        if (pollInterval) {
            clearInterval(pollInterval);
        }
    });
});
