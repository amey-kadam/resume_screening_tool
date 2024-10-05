// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Redirect to the chatbot page
                window.location.href = '/chatbot';
            } else {
                const result = await response.json();
                alert(result.error || 'An error occurred during upload.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during upload.');
        }
    });
});