function copyToClipboard(text) {
    document.addEventListener('DOMContentLoaded', function() {
        const copyButton = document.getElementById('copy');
        copyButton.addEventListener('click', function() {
            // Create a temporary textarea element to perform clipboard operations
            const tempTextarea = document.createElement('textarea');
            tempTextarea.value = text;
            document.body.appendChild(tempTextarea);
            // Copy the selected text to clipboard
            tempTextarea.select();
            document.execCommand('copy');
            // Clean up - remove the temporary textarea
            document.body.removeChild(tempTextarea);
        });
    });
}