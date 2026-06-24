// Shared JS Utilities
function toggleMode(checkbox) {
    if (checkbox.checked) {
        window.location.href = 'b2b_01_dashboard.html';
    } else {
        window.location.href = 'b2c_02_home.html';
    }
}

function showTyping(historyEl, typingEl, duration, callback) {
    typingEl.style.display = 'flex';
    historyEl.scrollTop = historyEl.scrollHeight;
    setTimeout(() => {
        typingEl.style.display = 'none';
        if(callback) callback();
    }, duration);
}

function appendMessage(historyEl, text, isUser, isHtml = false) {
    const msg = document.createElement('div');
    msg.className = `message ${isUser ? 'msg-user' : 'msg-bot'}`;
    if(isHtml) msg.innerHTML = text;
    else msg.innerText = text;
    historyEl.insertBefore(msg, historyEl.lastElementChild);
    historyEl.scrollTop = historyEl.scrollHeight;
}

async function callBackendApi(message, mode, historyEl, typingEl) {
    showTyping(historyEl, typingEl, 500, null);
    try {
        const response = await fetch('/api/v1/chat/message', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: 'test_session',
                messages: [{role: 'user', content: message}],
                mode: mode
            })
        });
        const data = await response.json();
        typingEl.style.display = 'none';
        appendMessage(historyEl, data.response + (data.rationale ? `<br><small><i>✨ ${data.rationale}</i></small>` : ''), false, true);
    } catch (e) {
        typingEl.style.display = 'none';
        appendMessage(historyEl, "Error connecting to AI.", false);
    }
}
