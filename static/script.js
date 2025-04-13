document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('messages');
    const questionInput = document.getElementById('question-input');
    const sendButton = document.getElementById('send-button');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle.querySelector('i');
    const refreshBtn = document.getElementById('refresh-btn');
    const refreshDataBtn = document.getElementById('refresh-data-btn');
    
    // Theme Toggle
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        themeIcon.className = newTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        
        // Save theme preference
        localStorage.setItem('theme', newTheme);
    });
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        themeIcon.className = savedTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }
    
    function addUserMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'user-message');
        messageDiv.textContent = content;
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.classList.add('timestamp');
        timestamp.textContent = getCurrentTime();
        messageDiv.appendChild(timestamp);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function addBotMessage(content) {
        // Create the bot message container
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'bot-message');
        messagesContainer.appendChild(messageDiv);
        
        // Split the message by line breaks
        const lines = content.split('\n');
        let lineIndex = 0;
        
        // Function to type each line with dynamic sizing
        function typeLine() {
            if (lineIndex < lines.length) {
                const line = lines[lineIndex];
                
                // Skip empty lines but still process them
                if (line.trim() === '') {
                    // Add an empty paragraph for spacing
                    const emptyLine = document.createElement('p');
                    emptyLine.innerHTML = '&nbsp;';
                    messageDiv.appendChild(emptyLine);
                    lineIndex++;
                    setTimeout(typeLine, 50); // Small delay between lines
                    return;
                }
                
                // Create container for this line
                const lineElement = document.createElement('div');
                lineElement.classList.add('typing-line');
                messageDiv.appendChild(lineElement);
                
                // Type the current line character by character
                let charIndex = 0;
                const typeInterval = setInterval(() => {
                    if (charIndex < line.length) {
                        lineElement.textContent += line.charAt(charIndex);
                        charIndex++;
                        
                        // Adjust message div height and scroll
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    } else {
                        clearInterval(typeInterval);
                        lineElement.classList.remove('typing-line');
                        
                        // Move to next line
                        lineIndex++;
                        setTimeout(typeLine, 100); // Delay before starting next line
                    }
                }, 15); // Speed of typing
            } else {
                // Add timestamp after all typing is done
                const timestamp = document.createElement('div');
                timestamp.classList.add('timestamp');
                timestamp.textContent = getCurrentTime();
                messageDiv.appendChild(timestamp);
            }
        }
        
        // Start typing the first line
        typeLine();
        
        // Ensure visibility
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    function showThinking() {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.classList.add('thinking');
        thinkingDiv.id = 'thinking-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.classList.add('dot');
            thinkingDiv.appendChild(dot);
        }
        
        messagesContainer.appendChild(thinkingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function hideThinking() {
        const thinkingDiv = document.getElementById('thinking-indicator');
        if (thinkingDiv) {
            thinkingDiv.remove();
        }
    }
    
    function askQuestion() {
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Add user message
        addUserMessage(question);
        questionInput.value = '';
        
        // Disable input while processing
        questionInput.disabled = true;
        sendButton.disabled = true;
        
        // Show thinking animation
        showThinking();
        
        // Send request to server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        })
        .then(response => response.json())
        .then(data => {
            // Hide thinking animation
            hideThinking();
            
            // Add bot response with line-by-line typing
            addBotMessage(data.answer);
            
            // Re-enable input
            questionInput.disabled = false;
            sendButton.disabled = false;
            questionInput.focus();
        })
        .catch(error => {
            hideThinking();
            addBotMessage('Sorry, I encountered an error while processing your question.');
            console.error('Error:', error);
            
            // Re-enable input
            questionInput.disabled = false;
            sendButton.disabled = false;
        });
    }
    
    // Refresh conversation
    refreshBtn.addEventListener('click', function() {
        // Remove all messages except the welcome message
        while (messagesContainer.children.length > 1) {
            messagesContainer.removeChild(messagesContainer.lastChild);
        }
        
        // Scroll to top
        messagesContainer.scrollTop = 0;
    });
    
    // Refresh data
    refreshDataBtn.addEventListener('click', function() {
        // Show a refreshing message
        addBotMessage('Refreshing player statistics and data...');
        
        // Send a refresh request to the server
        fetch('/refresh-data', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            addBotMessage('Statistics database updated successfully with the latest player data!');
        })
        .catch(error => {
            addBotMessage('Unable to refresh data. Please try again later.');
            console.error('Error refreshing data:', error);
        });
    });
    
    // Event listeners
    sendButton.addEventListener('click', askQuestion);
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            askQuestion();
        }
    });
    
    // Focus input on load
    questionInput.focus();
});