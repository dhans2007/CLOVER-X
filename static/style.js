document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const statusText = document.getElementById('status-text');
    const spinner = document.querySelector('.spinner');
    
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    // Drag and Drop Logic
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        // Validate file type
        const validTypes = ['.pdf', '.docx', '.txt'];
        const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        
        if (!validTypes.includes(ext)) {
            showStatus('Error: Invalid file type. Use PDF, DOCX, or TXT.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        showStatus('Processing document...', 'processing');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showStatus(data.message, 'success');
                // Update drop zone to show the uploaded file name
                const dropText = dropZone.querySelector('p');
                if (dropText) {
                    dropText.innerHTML = `<strong>Uploaded:</strong><br>${file.name}`;
                }
                enableChat();
            } else {
                showStatus(data.error || 'Upload failed', 'error');
            }
        } catch (err) {
            showStatus('Network error occurred.', 'error');
        }
    }

    function showStatus(message, state) {
        uploadStatus.classList.remove('hidden');
        uploadStatus.className = 'status-indicator';
        statusText.textContent = message;
        
        if (state === 'processing') {
            spinner.style.display = 'block';
        } else {
            spinner.style.display = 'none';
            uploadStatus.classList.add(state);
        }
    }

    function enableChat() {
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }

    // Chat Logic
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        appendMessage('user', text);
        chatInput.value = '';
        
        const typingId = showTypingIndicator();
        scrollToBottom();

        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: text })
            });

            const data = await response.json();
            removeTypingIndicator(typingId);

            if (response.ok) {
                appendMessage('assistant', data.answer, data.sources);
            } else {
                appendMessage('assistant', `Error: ${data.error}`);
            }
        } catch (err) {
            removeTypingIndicator(typingId);
            appendMessage('assistant', 'Error: Could not connect to the server.');
        }
        
        scrollToBottom();
    }

    function appendMessage(role, text, sources = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}-msg`;
        
        // Avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'avatar';
        avatarDiv.textContent = role === 'user' ? 'U' : 'AI';
        msgDiv.appendChild(avatarDiv);
        
        // Wrapper for content and sources
        const wrapperDiv = document.createElement('div');
        wrapperDiv.className = 'msg-wrapper';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'msg-content';
        
        // Use marked.js for assistant messages, plain text for user
        if (role === 'assistant' && typeof marked !== 'undefined') {
            contentDiv.innerHTML = marked.parse(text);
        } else {
            contentDiv.textContent = text;
        }
        
        wrapperDiv.appendChild(contentDiv);

        if (sources && sources.length > 0) {
            const sourceContainer = document.createElement('div');
            sourceContainer.className = 'source-container';
            
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'source-toggle';
            toggleBtn.innerHTML = `<span>View Source (${sources.length} chunks)</span> <span style="font-size:10px">▼</span>`;
            
            const sourceContent = document.createElement('div');
            sourceContent.className = 'source-content';
            
            sources.forEach((source, index) => {
                const p = document.createElement('p');
                p.style.marginBottom = '10px';
                p.textContent = `[Snippet ${index + 1}]: ${source}`;
                sourceContent.appendChild(p);
            });

            toggleBtn.addEventListener('click', () => {
                sourceContent.classList.toggle('open');
                const isOpen = sourceContent.classList.contains('open');
                toggleBtn.innerHTML = `<span>View Source (${sources.length} chunks)</span> <span style="font-size:10px">${isOpen ? '▲' : '▼'}</span>`;
            });

            sourceContainer.appendChild(toggleBtn);
            sourceContainer.appendChild(sourceContent);
            wrapperDiv.appendChild(sourceContainer);
        }

        msgDiv.appendChild(wrapperDiv);
        chatMessages.appendChild(msgDiv);
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicator = document.createElement('div');
        indicator.id = id;
        indicator.className = 'typing-indicator message assistant-msg';
        // Add dummy avatar for typing indicator layout consistency
        indicator.style.background = 'transparent';
        indicator.style.padding = '0';
        indicator.style.gap = '12px';
        
        indicator.innerHTML = `
            <div class="avatar">AI</div>
            <div class="msg-wrapper">
                <div class="msg-content" style="display:flex; gap:4px; align-items:center; height:100%; padding: 1.2rem;">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(indicator);
        return id;
    }

    function removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
