// MailMorph - Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const oldDomainInput = document.getElementById('old_domain');
    const newDomainInput = document.getElementById('new_domain');

    // Drag and drop functionality
    if (dropZone && fileInput) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        // Handle dropped files
        dropZone.addEventListener('drop', handleDrop, false);

        // Handle file input change
        fileInput.addEventListener('change', function(e) {
            handleFiles(e.target.files);
        });

        // Click to browse functionality
        dropZone.addEventListener('click', function(e) {
            if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {
                fileInput.click();
            }
        });
    }

    // Form validation
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            showLoadingState();
        });
    }

    // Real-time domain validation
    if (oldDomainInput) {
        oldDomainInput.addEventListener('input', function() {
            validateDomain(this, 'oldDomainFeedback');
        });
    }

    if (newDomainInput) {
        newDomainInput.addEventListener('input', function() {
            validateDomain(this, 'newDomainFeedback');
        });
    }

    // Utility functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('drag-over');
    }

    function unhighlight(e) {
        dropZone.classList.remove('drag-over');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            
            // Validate file type
            const allowedTypes = ['text/csv', 'text/plain', 'application/vnd.ms-excel'];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            if (!allowedTypes.includes(file.type) && !['csv', 'txt'].includes(fileExtension)) {
                showAlert('Invalid file type. Please select a CSV or TXT file.', 'danger');
                return;
            }

            // Validate file size (16MB)
            const maxSize = 16 * 1024 * 1024;
            if (file.size > maxSize) {
                showAlert('File is too large. Maximum size is 16MB.', 'danger');
                return;
            }

            // Update file input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;

            // Show file preview
            showFilePreview(file);
        }
    }

    function showFilePreview(file) {
        const dropZoneContent = dropZone.querySelector('.drop-zone-content');
        const filePreview = dropZone.querySelector('.drop-zone-preview');
        
        if (dropZoneContent && filePreview && fileName) {
            dropZoneContent.style.display = 'none';
            filePreview.classList.remove('d-none');
            fileName.textContent = file.name;
            
            // Add file size info
            const fileSize = formatFileSize(file.size);
            fileName.textContent += ` (${fileSize})`;
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function validateDomain(input, feedbackId) {
        const domain = input.value.trim();
        const feedbackElement = document.getElementById(feedbackId);
        
        if (!domain) {
            input.classList.remove('is-valid', 'is-invalid');
            if (feedbackElement) feedbackElement.textContent = '';
            return true;
        }

        const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/;
        const isValid = domainRegex.test(domain) && domain.length <= 253;

        if (isValid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            if (feedbackElement) feedbackElement.textContent = '';
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            if (feedbackElement) feedbackElement.textContent = 'Please enter a valid domain (e.g., example.com)';
        }

        return isValid;
    }

    function validateForm() {
        let isValid = true;

        // Validate file
        if (!fileInput.files || fileInput.files.length === 0) {
            showAlert('Please select a file to upload.', 'danger');
            isValid = false;
        }

        // Validate domains
        const oldDomainValid = validateDomain(oldDomainInput, 'oldDomainFeedback');
        const newDomainValid = validateDomain(newDomainInput, 'newDomainFeedback');

        if (!oldDomainValid || !newDomainValid) {
            isValid = false;
        }

        // Check if domains are different
        const oldDomain = oldDomainInput.value.trim().toLowerCase();
        const newDomain = newDomainInput.value.trim().toLowerCase();
        
        if (oldDomain && newDomain && oldDomain === newDomain) {
            showAlert('Old and new domains must be different.', 'danger');
            isValid = false;
        }

        return isValid;
    }

    function showLoadingState() {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Processing...';
            submitBtn.classList.add('loading');
        }
    }

    function showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'danger' ? 'danger' : 'info'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i class="bi bi-${type === 'danger' ? 'exclamation-triangle' : 'info-circle'}-fill me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert alert at the top of main content
        const main = document.querySelector('main');
        if (main) {
            main.insertBefore(alertDiv, main.firstChild);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Clear file function (global)
    window.clearFile = function() {
        if (fileInput) {
            fileInput.value = '';
        }
        
        const dropZoneContent = dropZone.querySelector('.drop-zone-content');
        const filePreview = dropZone.querySelector('.drop-zone-preview');
        
        if (dropZoneContent && filePreview) {
            dropZoneContent.style.display = 'block';
            filePreview.classList.add('d-none');
        }
    };

    // API call for domain validation (optional enhancement)
    function validateDomainsAPI(oldDomain, newDomain) {
        return fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                old_domain: oldDomain,
                new_domain: newDomain
            })
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Validation API error:', error);
            return { old_domain_valid: true, new_domain_valid: true, domains_different: true };
        });
    }

    // Enhanced form validation with API call (optional)
    async function validateFormEnhanced() {
        const basicValidation = validateForm();
        if (!basicValidation) return false;

        const oldDomain = oldDomainInput.value.trim();
        const newDomain = newDomainInput.value.trim();

        try {
            const validation = await validateDomainsAPI(oldDomain, newDomain);
            
            if (!validation.old_domain_valid) {
                showAlert('Invalid old domain format.', 'danger');
                return false;
            }
            
            if (!validation.new_domain_valid) {
                showAlert('Invalid new domain format.', 'danger');
                return false;
            }
            
            if (!validation.domains_different) {
                showAlert('Old and new domains must be different.', 'danger');
                return false;
            }
            
            return true;
        } catch (error) {
            console.error('Enhanced validation error:', error);
            return basicValidation; // Fall back to basic validation
        }
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + O to open file dialog
        if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
            e.preventDefault();
            if (fileInput) {
                fileInput.click();
            }
        }
        
        // Enter to submit form when form fields are focused
        if (e.key === 'Enter' && (e.target === oldDomainInput || e.target === newDomainInput)) {
            e.preventDefault();
            if (uploadForm && validateForm()) {
                uploadForm.submit();
            }
        }
    });

    // Auto-focus first input on page load
    if (oldDomainInput) {
        oldDomainInput.focus();
    }

    console.log('MailMorph JavaScript initialized successfully');
});