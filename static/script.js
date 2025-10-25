// Get references to the HTML elements
const fileInput = document.getElementById('fileInput');
const statusElement = document.getElementById('status');
const resultContainer = document.getElementById('result-container');
const resultUrlElement = document.getElementById('resultUrl');
const copyButton = document.getElementById('copyButton');

// The URL of your FastAPI upload service
const UPLOAD_URL = 'http://127.0.0.1:8001/upload-image/';

// Listen for when the user selects a file
fileInput.addEventListener('change', handleFileUpload);

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) {
        return; // No file selected
    }

    // Show uploading status
    statusElement.textContent = 'Uploading, please wait...';
    statusElement.style.color = '#faa61a';
    resultContainer.classList.add('hidden');

    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Use fetch to send the file to your API
        const response = await fetch(UPLOAD_URL, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            // Handle HTTP errors
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed with status ' + response.status);
        }

        // Get the JSON response from the server
        const data = await response.json();
        
        // Display the URL and success message
        statusElement.textContent = 'Upload successful!';
        statusElement.style.color = '#43b581';
        resultUrlElement.textContent = data.file_url;
        resultContainer.classList.remove('hidden');

    } catch (error) {
        // Display an error message
        statusElement.textContent = 'Error: ' + error.message;
        statusElement.style.color = '#f04747';
        console.error('Upload error:', error);
    }
}

// Add click event for the copy button
copyButton.addEventListener('click', () => {
    navigator.clipboard.writeText(resultUrlElement.textContent)
        .then(() => {
            alert('URL copied to clipboard!');
        })
        .catch(err => {
            alert('Failed to copy URL.');
            console.error('Copy error:', err);
        });
});