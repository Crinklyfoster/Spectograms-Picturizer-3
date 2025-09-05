document.addEventListener('DOMContentLoaded', function() {
    const sessionId = document.getElementById('sessionId').value;
    const processBtn = document.getElementById('processBtn');
    const deleteBatchBtn = document.getElementById('deleteBatchBtn');
    const selectAllBtn = document.getElementById('selectAll');
    const selectNoneBtn = document.getElementById('selectNone');
    const selectRecommendedBtn = document.getElementById('selectRecommended');
    const selectionCount = document.getElementById('selectionCount');
    const spectrogramCheckboxes = document.querySelectorAll('input[name="spectrograms"]');
    const removeFileButtons = document.querySelectorAll('.remove-file');
    
    // Initialize
    updateSelectionCount();
    updateProcessButton();
    
    // Event listeners
    spectrogramCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectionCount();
            updateProcessButton();
        });
    });
    
    selectAllBtn.addEventListener('click', function() {
        spectrogramCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        updateSelectionCount();
        updateProcessButton();
    });
    
    selectNoneBtn.addEventListener('click', function() {
        spectrogramCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        updateSelectionCount();
        updateProcessButton();
    });
    
    selectRecommendedBtn.addEventListener('click', function() {
        const recommendedTypes = ['mel', 'wavelet', 'spectral_kurtosis'];
        spectrogramCheckboxes.forEach(checkbox => {
            checkbox.checked = recommendedTypes.includes(checkbox.value);
        });
        updateSelectionCount();
        updateProcessButton();
    });
    
    removeFileButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filename = this.getAttribute('data-filename');
            removeFile(filename);
        });
    });
    
    processBtn.addEventListener('click', function() {
        if (!processBtn.disabled) {
            startProcessing();
        }
    });
    
    deleteBatchBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to delete this batch? This cannot be undone.')) {
            deleteBatch();
        }
    });
    
    function updateSelectionCount() {
        const selected = Array.from(spectrogramCheckboxes).filter(cb => cb.checked);
        selectionCount.textContent = `${selected.length} of ${spectrogramCheckboxes.length} selected`;
    }
    
    function updateProcessButton() {
        const hasFiles = document.querySelectorAll('.file-item').length > 0;
        const hasSelectedSpectrograms = Array.from(spectrogramCheckboxes).some(cb => cb.checked);
        
        processBtn.disabled = !hasFiles || !hasSelectedSpectrograms;
    }
    
    function removeFile(filename) {
        fetch('/remove_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                saved_name: filename
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.removed) {
                // Remove file item from DOM
                const fileItem = document.querySelector(`[data-filename="${filename}"]`);
                if (fileItem) {
                    fileItem.remove();
                }
                updateProcessButton();
                
                // Check if no files left
                const remainingFiles = document.querySelectorAll('.file-item');
                if (remainingFiles.length === 0) {
                    alert('No files remaining. Redirecting to upload page.');
                    window.location.href = '/';
                }
            } else {
                alert('Error removing file: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error removing file:', error);
            alert('Error removing file: ' + error.message);
        });
    }
    
    function startProcessing() {
        const selectedTypes = Array.from(spectrogramCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        if (selectedTypes.length === 0) {
            alert('Please select at least one spectrogram type.');
            return;
        }
        
        processBtn.disabled = true;
        processBtn.textContent = 'Starting...';
        
        fetch('/process_uploaded_files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                selected_types: selectedTypes
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.started) {
                // Redirect to progress page
                window.location.href = `/batch_progress?session_id=${sessionId}`;
            } else {
                alert('Error starting processing: ' + (data.error || 'Unknown error'));
                processBtn.disabled = false;
                processBtn.textContent = 'Process Files';
            }
        })
        .catch(error => {
            console.error('Error starting processing:', error);
            alert('Error starting processing: ' + error.message);
            processBtn.disabled = false;
            processBtn.textContent = 'Process Files';
        });
    }
    
    function deleteBatch() {
        fetch(`/delete_session/${sessionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.deleted) {
                alert('Batch deleted successfully');
                window.location.href = '/';
            } else {
                alert('Error deleting batch: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error deleting batch:', error);
            alert('Error deleting batch: ' + error.message);
        });
    }
});
