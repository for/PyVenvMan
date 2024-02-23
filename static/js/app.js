function displayFlashMessage(category, message) {
    const flashContainer = document.querySelector('.flash-messages');
    const flashMessage = `<div class="alert alert-${category}" role="alert">${message}</div>`;
    flashContainer.insertAdjacentHTML('afterbegin', flashMessage);

    // Automatically dismiss the newly added flash message after a delay
    setTimeout(() => {
        const alert = flashContainer.querySelector('.alert');
        if (alert) {
            alert.remove(); // This removes the element completely
        }
    }, 5000); // Adjust the timeout as needed
}

// Automatically dismiss all existing flash messages after 5 seconds
document.querySelectorAll('.flash-messages .alert').forEach(alert => {
    setTimeout(() => {
        alert.remove(); // This ensures each alert is removed completely
    }, 5000); // Adjust the timeout as needed
});

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.run-venv').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();  // Prevent form submission
            const venvName = this.getAttribute('data-venv-name');
            const commandInput = document.querySelector(`.command-input[data-venv-name="${venvName}"]`);
            const command = commandInput.value;

            if (!command) {
                displayFlashMessage('danger', 'Please enter a command.');
                return;
            }

            fetch(`/run/${venvName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command }),
            })
            .then(response => response.json())
            .then(data => {
                const outputTextArea = document.getElementById('command-output');
                if(data.success) {
                    outputTextArea.value = `Output: ${data.output}`;
                } else {
                    outputTextArea.value = `Error: ${data.output}`;
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
        });
    });

    // Automatically dismiss all existing flash messages after 5 seconds
    document.querySelectorAll('.container .alert').forEach(alert => {
        setTimeout(() => {
            alert.style.display = 'none'; // Or use alert.remove() if you want to completely remove the element
        }, 5000); // Adjust the timeout as needed
    });
});

function updateCommandHistory() {
    fetch('/command-history')
        .then(response => response.json())
        .then(data => {
            const historyContainer = document.getElementById('command-history');
            historyContainer.innerHTML = ''; // Clear existing history
            data.forEach(log => {
                const entry = document.createElement('div');
                entry.classList.add('command-history-entry');
                entry.innerHTML = `<strong>${log.timestamp} [${log.venv_name}] (${log.log_type})</strong>: ${log.log_message} - Output: ${log.command_output}`;
                historyContainer.appendChild(entry);
            });
        })
        .catch(error => console.error('Error fetching command history:', error));
}

document.addEventListener('DOMContentLoaded', updateCommandHistory);