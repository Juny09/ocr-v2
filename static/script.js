// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewArea = document.getElementById('previewArea');
const imagePreview = document.getElementById('imagePreview');
const preprocessToggle = document.getElementById('preprocessToggle');
const langSelect = document.getElementById('langSelect');
const changeBtn = document.getElementById('changeBtn');
const convertBtn = document.getElementById('convertBtn');
const btnText = document.getElementById('btnText');
const spinner = document.getElementById('spinner');
const resultSection = document.getElementById('resultSection');
const resultText = document.getElementById('resultText');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const charCount = document.getElementById('charCount');
const engineInfo = document.getElementById('engineInfo');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');
const statusText = document.querySelector('.status-text');

// API Configuration
const API_BASE_URL = window.location.origin;
const API_ENDPOINT = `${API_BASE_URL}/api/ocr`;

// State
let selectedFile = null;
let extractedText = '';
let cropper = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAPIHealth();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Upload area click
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Buttons
    changeBtn.addEventListener('click', resetUpload);
    convertBtn.addEventListener('click', performOCR);
    copyBtn.addEventListener('click', copyToClipboard);
    downloadBtn.addEventListener('click', downloadText);
}

// Check API Health
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusText.textContent = 'Ready';
            engineInfo.textContent = `Engine: ${data.ocr_engine}`;
            try {
                const engineName = String(data.ocr_engine || '').toLowerCase();
                // PaddleOCR 和 EasyOCR 默认不使用预处理
                if (engineName.startsWith('paddleocr') || engineName.startsWith('easyocr')) {
                    if (preprocessToggle) preprocessToggle.checked = false;
                } else {
                    if (preprocessToggle) preprocessToggle.checked = true;
                }
            } catch (e) {}
        } else {
            statusText.textContent = 'Service Unavailable';
            showToast('OCR service is unavailable', 'error');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        statusText.textContent = 'Offline';
    }
}

// File Handling
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        validateAndPreviewFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const file = event.dataTransfer.files[0];
    if (file) {
        validateAndPreviewFile(file);
    }
}

function validateAndPreviewFile(file) {
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
        showToast('Invalid file type. Please upload PNG, JPG, or JPEG', 'error');
        return;
    }
    
    // Validate file size (5MB)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('File too large. Maximum size is 5MB', 'error');
        return;
    }
    
    selectedFile = file;
    
    // Preview image
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        uploadArea.classList.add('hidden');
        previewArea.classList.remove('hidden');
        
        // Initialize Cropper
        if (cropper) {
            cropper.destroy();
        }
        cropper = new Cropper(imagePreview, {
            viewMode: 1,
            autoCropArea: 1,
            responsive: true,
            background: false,
            zoomable: false,
            scalable: false,
        });
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
    selectedFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    uploadArea.classList.remove('hidden');
    previewArea.classList.add('hidden');
    resultSection.classList.add('hidden');
    resultText.value = '';
}

// OCR Processing
async function performOCR() {
    if (!selectedFile) {
        showToast('Please select an image first', 'error');
        return;
    }
    
    // Show loading state
    convertBtn.disabled = true;
    btnText.classList.add('hidden');
    spinner.classList.remove('hidden');
    statusText.textContent = 'Processing...';
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    const usePreprocess = preprocessToggle ? preprocessToggle.checked : true;
    formData.append('preprocess', usePreprocess ? 'true' : 'false');
    
    // Add language selection if available
    if (langSelect) {
        formData.append('language', langSelect.value);
    }
    
    // Add crop data
    if (cropper) {
        const data = cropper.getData();
        formData.append('crop_x', Math.round(data.x));
        formData.append('crop_y', Math.round(data.y));
        formData.append('crop_width', Math.round(data.width));
        formData.append('crop_height', Math.round(data.height));
    }
    
    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            extractedText = data.text || '';
            resultText.removeAttribute('readonly'); // Make editable
            resultText.value = extractedText;
            charCount.textContent = `${extractedText.length} chars`;
            resultSection.classList.remove('hidden');

            // Listen for changes to update state
            resultText.oninput = () => {
                extractedText = resultText.value;
                charCount.textContent = `${extractedText.length} chars`;
            };

            // 若成功但文本为空，给出更明确的提示
            if (extractedText.length === 0) {
                showToast('未检测到文本，请尝试更清晰的图片或切换识别引擎', 'error');
                statusText.textContent = 'No Text';
            } else {
                showToast('Text extracted successfully!', 'success');
                statusText.textContent = 'Complete';
            }
        } else {
            const errorMsg = data.error || data.detail || 'OCR processing failed';
            showToast(errorMsg, 'error');
            statusText.textContent = 'Failed';
        }
    } catch (error) {
        console.error('OCR request failed:', error);
        showToast('Network error. Please try again.', 'error');
        statusText.textContent = 'Error';
    } finally {
        // Reset button state
        convertBtn.disabled = false;
        btnText.classList.remove('hidden');
        spinner.classList.add('hidden');
    }
}

// Copy to Clipboard
async function copyToClipboard() {
    if (!extractedText) {
        showToast('No text to copy', 'error');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(extractedText);
        showToast('Text copied to clipboard!', 'success');
    } catch (error) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = extractedText;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Text copied to clipboard!', 'success');
    }
}

// Download Text
function downloadText() {
    if (!extractedText) {
        showToast('No text to download', 'error');
        return;
    }
    
    const blob = new Blob([extractedText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extracted-text-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Text file downloaded!', 'success');
}

// Toast Notification
function showToast(message, type = 'info') {
    toastMessage.textContent = message;
    toast.classList.remove('hidden');
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}
