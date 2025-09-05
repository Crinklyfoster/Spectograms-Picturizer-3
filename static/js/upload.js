document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const selectedFiles = document.getElementById('selectedFiles');
    const filesList = document.getElementById('filesList');
    const uploadControls = document.getElementById('uploadControls');
    const uploadBtn = document.getElementById('uploadBtn');
    const clearBtn = document.getElementById('clearBtn');
    const uploadResults = document.getElementById('uploadResults');
    const resultsContent = document.getElementById('resultsContent');
    const nextStepBtn = document.getElementById('nextStepBtn');
    const manageLink = document.getElementById('manageLink');
    
    let currentFiles = [];

    // Drag and drop handlers
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    clearBtn.addEventListener('click', function() {
        currentFiles = [];
        updateFilesList();
    });

    uploadBtn.addEventListener('click', function() {
        if (currentFiles.length > 0) {
            uploadFiles();
        }
    });

    function handleFiles(files) {
        // Add new files to current selection
        Array.from(files).forEach(file => {
            if (isAudioFile(file)) {
                // Check if file already exists
                const existingFile = currentFiles.find(f => f.name === file.name && f.size === file.size);
                if (!existingFile) {
                    currentFiles.push(file);
                }
            }
        });
        
        updateFilesList();
    }

    function isAudioFile(file) {
        const audioExtensions = ['.wav', '.mp3', '.flac', '.aac', '.m4a', '.ogg'];
        const fileName = file.name.toLowerCase();
        return audioExtensions.some(ext => fileName.endsWith(ext));
    }

    function updateFilesList() {
        if (currentFiles.length === 0) {
            selectedFiles.style.display = 'none';
            uploadControls.style.display = 'none';
            uploadResults.style.display = 'none';
            return;
        }

        selectedFiles.style.display = 'block';
        uploadControls.style.display = 'flex';

        filesList.innerHTML = '';
        currentFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-info">
                    <span class="filename">${file.name}</span>
                    <span class="file-size">${formatFileSize(file.size)}</span>
                </div>
                <button class="btn btn-danger btn-sm" onclick="removeFile(${index})">Remove</button>
            `;
            filesList.appendChild(fileItem);
        });

        // Update upload button
        uploadBtn.textContent = `Upload ${currentFiles.length} File${currentFiles.length !== 1 ? 's' : ''}`;
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Global function for remove buttons
    window.removeFile = function(index) {
        currentFiles.splice(index, 1);
        updateFilesList();
    };

    function uploadFiles() {
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';
        
        const formData = new FormData();
        currentFiles.forEach(file => {
            formData.append('files[]', file);
        });

        fetch('/upload_files_only', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            displayUploadResults(data);
        })
        .catch(error => {
            console.error('Upload error:', error);
            alert('Upload failed: ' + error.message);
        })
        .finally(() => {
            uploadBtn.disabled = false;
            uploadBtn.textContent = `Upload ${currentFiles.length} File${currentFiles.length !== 1 ? 's' : ''}`;
        });
    }

    function displayUploadResults(data) {
        uploadResults.style.display = 'block';
        
        let resultsHTML = '<div class="upload-summary">';
        
        if (data.error) {
            resultsHTML += `<div class="error-item">${data.error}</div>`;
        } else {
            const acceptedFiles = data.files.filter(f => f.accepted);
            const rejectedFiles = data.files.filter(f => !f.accepted);
            
            resultsHTML += `
                <div class="summary-stats">
                    <div class="stat-item success">
                        <h3>${acceptedFiles.length}</h3>
                        <span>Accepted</span>
                    </div>
                    <div class="stat-item danger">
                        <h3>${rejectedFiles.length}</h3>
                        <span>Rejected</span>
                    </div>
                </div>
            `;
            
            if (acceptedFiles.length > 0) {
                resultsHTML += '<h4>Accepted Files:</h4><div class="file-results">';
                acceptedFiles.forEach(file => {
                    resultsHTML += `
                        <div class="result-item success">
                            <span class="filename">${file.filename}</span>
                            <span class="duration">${file.duration_seconds?.toFixed(1) || '?'}s</span>
                        </div>
                    `;
                });
                resultsHTML += '</div>';
            }
            
            if (rejectedFiles.length > 0) {
                resultsHTML += '<h4>Rejected Files:</h4><div class="file-results">';
                rejectedFiles.forEach(file => {
                    resultsHTML += `
                        <div class="result-item error">
                            <span class="filename">${file.filename}</span>
                            <span class="reason">${file.reason}</span>
                        </div>
                    `;
                });
                resultsHTML += '</div>';
            }
            
            if (data.session_id && acceptedFiles.length > 0) {
                manageLink.href = `/manage_files?session_id=${data.session_id}`;
                nextStepBtn.style.display = 'block';
            }
        }
        
        resultsHTML += '</div>';
        resultsContent.innerHTML = resultsHTML;
    }
});
