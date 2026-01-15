// 配置
// 使用 window.API_BASE_URL（在 index.html 中设置）或自动检测
const API_BASE_URL = window.API_BASE_URL || (
    window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'
        : `${window.location.protocol}//${window.location.hostname}:8000`
);

// 全局状态
let currentChatId = null;
let chatHistory = [];
let isProcessing = false;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    loadChatHistory();
});

// 初始化应用
async function initializeApp() {
    // 初始化完成
}

// 设置事件监听器
function setupEventListeners() {
    const input = document.getElementById('questionInput');

    // 自动调整输入框高度
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// 新建对话
function newChat() {
    currentChatId = Date.now().toString();
    document.getElementById('messagesContainer').innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🤖</div>
            <h2>新对话</h2>
            <p>我可以基于知识库内容回答您的问题</p>
        </div>
    `;
    document.getElementById('questionInput').value = '';
    document.getElementById('questionInput').focus();
}

// 示例问题
function askExample(question) {
    document.getElementById('questionInput').value = question;
    sendMessage();
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();

    if (!question || isProcessing) return;

    // 清空输入框
    input.value = '';
    input.style.height = 'auto';

    // 如果是新对话，创建ID
    if (!currentChatId) {
        currentChatId = Date.now().toString();
    }

    // 移除欢迎消息
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // 添加用户消息
    addMessage('user', question);
    saveChatMessage(currentChatId, 'user', question);

    // 添加助手消息占位符
    const assistantMsgId = addMessage('assistant', '', true);

    // 禁用发送按钮
    isProcessing = true;
    updateSendButton(true);

    // 获取设置
    const settings = getSettings();

    try {
        if (settings.streamMode) {
            await sendStreamMessage(question, settings, assistantMsgId);
        } else {
            await sendNormalMessage(question, settings, assistantMsgId);
        }

        // 保存到历史
        saveChatHistory(question);
    } catch (error) {
        console.error('发送消息失败:', error);
        const errorMsg = '抱歉，发生了错误。请稍后重试。';
        updateMessageContent(assistantMsgId, errorMsg);
        saveChatMessage(currentChatId, 'assistant', errorMsg);
    } finally {
        isProcessing = false;
        updateSendButton(false);
    }
}

// 流式消息
async function sendStreamMessage(question, settings, messageId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: question,
            top_k: settings.topK,
            temperature: settings.temperature,
            use_cache: settings.useCache
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    let sources = null;

    // 移除打字指示器
    removeTypingIndicator(messageId);

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);

                if (data === '[DONE]') {
                    continue;
                }

                try {
                    const json = JSON.parse(data);

                    // 处理来源信息
                    if (json.sources) {
                        sources = json.sources;
                    }

                    // 处理内容
                    if (json.content !== undefined) {
                        fullText += json.content;
                        updateMessageContent(messageId, fullText);
                    }
                } catch (e) {
                    console.error('解析JSON失败:', e);
                }
            }
        }
    }

    // 添加来源
    if (sources) {
        addSourcesToMessage(messageId, sources);
    }

    // 保存助手消息
    saveChatMessage(currentChatId, 'assistant', fullText, sources);
}

// 普通消息
async function sendNormalMessage(question, settings, messageId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: question,
            top_k: settings.topK,
            temperature: settings.temperature,
            use_cache: settings.useCache
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // 移除打字指示器
    removeTypingIndicator(messageId);

    // 更新消息内容
    updateMessageContent(messageId, data.answer);

    // 添加来源
    if (data.sources) {
        addSourcesToMessage(messageId, data.sources);
    }

    // 保存助手消息
    saveChatMessage(currentChatId, 'assistant', data.answer, data.sources);
}

// 添加消息
function addMessage(role, content, showTyping = false) {
    const container = document.getElementById('messagesContainer');
    const messageId = `msg-${Date.now()}`;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = messageId;

    const avatar = role === 'user' ? '👤' : '🤖';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${content}</div>
            ${showTyping ? '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>' : ''}
        </div>
    `;

    container.appendChild(messageDiv);
    scrollToBottom();

    return messageId;
}

// 更新消息内容
function updateMessageContent(messageId, content) {
    const message = document.getElementById(messageId);
    if (message) {
        const textDiv = message.querySelector('.message-text');
        textDiv.textContent = content;
        scrollToBottom();
    }
}

// 移除打字指示器
function removeTypingIndicator(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        const indicator = message.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
}

// 添加来源到消息
function addSourcesToMessage(messageId, sources) {
    const message = document.getElementById(messageId);
    if (!message || !sources || sources.length === 0) return;

    const content = message.querySelector('.message-content');

    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'message-sources';
    sourcesDiv.innerHTML = '<h4>📚 参考来源</h4>';

    sources.forEach((source, idx) => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';

        const score = (source.score * 100).toFixed(1);
        const text = source.text.length > 100 ? source.text.substring(0, 100) + '...' : source.text;
        const filename = source.metadata?.filename || '未知文件';

        sourceItem.innerHTML = `
            <div class="source-score">来源 ${idx + 1} · 相似度: ${score}%</div>
            <div class="source-text">${text}</div>
            <div class="source-file">📄 ${filename}</div>
        `;

        sourcesDiv.appendChild(sourceItem);
    });

    content.appendChild(sourcesDiv);
}

// 获取设置
function getSettings() {
    return {
        topK: parseInt(document.getElementById('topK').value),
        temperature: parseFloat(document.getElementById('temperature').value),
        useCache: document.getElementById('useCache').checked,
        streamMode: document.getElementById('streamMode').checked
    };
}

// 更新发送按钮状态
function updateSendButton(disabled) {
    const btn = document.getElementById('sendBtn');
    btn.disabled = disabled;
    btn.innerHTML = disabled ? '<span class="send-icon">⏳</span>' : '<span class="send-icon">➤</span>';
}

// 滚动到底部
function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    container.scrollTop = container.scrollHeight;
}

// 切换设置面板
function toggleSettings() {
    const panel = document.getElementById('settingsPanel');
    panel.classList.toggle('open');
}

// 更新设置值显示
function updateTopKValue(value) {
    document.getElementById('topKValue').textContent = value;
}

function updateTemperatureValue(value) {
    document.getElementById('temperatureValue').textContent = value;
}

// 保存对话历史
function saveChatHistory(question) {
    // 如果已经存在该对话记录，则不重复添加
    const existing = chatHistory.find(h => h.id === currentChatId);
    if (existing) {
        return;
    }

    const title = question.length > 30 ? question.substring(0, 30) + '...' : question;

    chatHistory.unshift({
        id: currentChatId,
        title: title,
        timestamp: Date.now()
    });

    // 只保留最近20条
    if (chatHistory.length > 20) {
        chatHistory = chatHistory.slice(0, 20);
    }

    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    renderChatHistory();
}

// 加载对话历史
function loadChatHistory() {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
        chatHistory = JSON.parse(saved);
        renderChatHistory();
    }
}

// 渲染对话历史
function renderChatHistory() {
    const list = document.getElementById('historyList');
    list.innerHTML = '';

    chatHistory.forEach(chat => {
        const item = document.createElement('div');
        item.className = 'history-item';
        if (chat.id === currentChatId) {
            item.classList.add('active');
        }

        // 点击整个条目加载对话
        item.onclick = (e) => {
            // 如果点击的是删除按钮，不触发加载
            if (e.target.closest('.delete-chat-btn')) return;
            loadChat(chat.id);
        };

        item.innerHTML = `
            <span class="history-item-title">${chat.title}</span>
            <button class="delete-chat-btn" onclick="deleteChat('${chat.id}', event)" title="删除">✕</button>
        `;

        list.appendChild(item);
    });
}

// 删除单个对话
function deleteChat(chatId, event) {
    if (event) {
        event.stopPropagation();
    }

    if (!confirm('确定要删除这个对话吗？')) {
        return;
    }

    // 从历史记录数组中移除
    chatHistory = chatHistory.filter(c => c.id !== chatId);
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));

    // 移除消息存储
    localStorage.removeItem(`chat_msgs_${chatId}`);

    // 如果删除的是当前对话，重置界面
    if (currentChatId === chatId) {
        newChat();
    }

    renderChatHistory();
}

// 清除所有历史
function clearAllHistory() {
    if (chatHistory.length === 0) return;

    if (!confirm('确定要清除所有对话历史吗？此操作不可恢复。')) {
        return;
    }

    // 清除所有消息记录
    chatHistory.forEach(chat => {
        localStorage.removeItem(`chat_msgs_${chat.id}`);
    });

    // 清空历史记录
    chatHistory = [];
    localStorage.setItem('chatHistory', JSON.stringify([]));

    // 重置界面
    newChat();
    renderChatHistory();
}

// 加载对话
function loadChat(chatId) {
    currentChatId = chatId;
    renderChatHistory();

    // 清空当前消息
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';

    // 加载该对话的消息记录
    const messages = getChatMessages(chatId);

    if (messages.length > 0) {
        messages.forEach(msg => {
            const msgId = addMessage(msg.role, msg.content, false);
            if (msg.sources) {
                addSourcesToMessage(msgId, msg.sources);
            }
        });
    } else {
        // 如果没有消息（不应该发生，但在某些边缘情况下可能），显示欢迎消息
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🤖</div>
                <h2>新对话</h2>
                <p>我可以基于知识库内容回答您的问题</p>
            </div>
        `;
    }
}

// 保存单条消息到本地存储
function saveChatMessage(chatId, role, content, sources = null) {
    if (!chatId) return;

    const messages = getChatMessages(chatId);
    messages.push({
        role,
        content,
        sources,
        timestamp: Date.now()
    });

    localStorage.setItem(`chat_msgs_${chatId}`, JSON.stringify(messages));
}

// 获取对话消息记录
function getChatMessages(chatId) {
    const saved = localStorage.getItem(`chat_msgs_${chatId}`);
    return saved ? JSON.parse(saved) : [];
}

// 显示通知
function showNotification(message, type = 'info') {
    // 简单的通知实现
    console.log(`[${type}] ${message}`);
    // 可以扩展为更好的UI通知
}
