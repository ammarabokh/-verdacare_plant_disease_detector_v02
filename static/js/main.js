// Dark Mode
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved dark mode preference
    if (localStorage.getItem('darkMode') === 'true' || 
        (!localStorage.getItem('darkMode') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
});

function toggleDarkMode() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('darkMode', document.documentElement.classList.contains('dark'));
}

// Language Menu
function toggleLanguageMenu() {
    const menu = document.getElementById('language-menu');
    menu.classList.toggle('hidden');
}

// Close language menu when clicking outside
document.addEventListener('click', function(event) {
    const menu = document.getElementById('language-menu');
    const button = event.target.closest('button');
    if (menu && !menu.classList.contains('hidden') && !button?.onclick?.toString().includes('toggleLanguageMenu')) {
        menu.classList.add('hidden');
    }
});

// Mobile Menu
function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('hidden');
}

// Chat Widget Toggle
function toggleChat() {
    const chatWindow = document.getElementById('chat-window');
    chatWindow.classList.toggle('hidden');
    if (!chatWindow.classList.contains('hidden')) {
        document.getElementById('chat-input').focus();
    }
}

// Clear Chat
function clearChat() {
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.innerHTML = `
        <div class="flex gap-3">
            <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-robot text-white text-sm"></i>
            </div>
            <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 max-w-[80%]">
                <p class="text-gray-700 dark:text-gray-300 text-sm">
                    ${document.documentElement.lang === 'ar' 
                        ? 'مرحباً! أنا مساعدك الزراعي. اسألني عن أمراض النباتات، العلاجات، أو نصائح الزراعة.'
                        : "Hello! I am your agricultural assistant. Ask me about plant diseases, treatments, or farming tips."
                    }
                </p>
            </div>
        </div>
    `;

    // Clear on server
    fetch('/chat/clear', { method: 'POST' });
}

// Send Chat Message
function sendMessage(event) {
    event.preventDefault();

    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    const typingId = addTypingIndicator();

    // Send to server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        removeTypingIndicator(typingId);
        addMessage(data.response, 'assistant');
    })
    .catch(error => {
        removeTypingIndicator(typingId);
        addMessage(
            document.documentElement.lang === 'ar' 
                ? 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.'
                : 'Sorry, an error occurred. Please try again.',
            'assistant'
        );
    });
}

function addMessage(text, role) {
    const messagesDiv = document.getElementById('chat-messages');
    const isRTL = document.documentElement.dir === 'rtl';

    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex gap-3 animate-fade-in';

    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="flex-1"></div>
            <div class="bg-primary text-white rounded-lg p-3 max-w-[80%] ${isRTL ? 'rounded-tr-none' : 'rounded-tl-none'}">
                <p class="text-sm">${escapeHtml(text)}</p>
            </div>
            <div class="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-user text-white text-sm"></i>
            </div>
        `;
    } else {
        const assistantHtml = renderMarkdownSafe(text);
        messageDiv.innerHTML = `
            <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-robot text-white text-sm"></i>
            </div>
            <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 max-w-[80%]">
                <div class="text-gray-700 dark:text-gray-300 text-sm leading-7">${assistantHtml}</div>
            </div>
        `;
    }

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addTypingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');
    const id = 'typing-' + Date.now();

    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'flex gap-3';
    typingDiv.innerHTML = `
        <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
            <i class="fas fa-robot text-white text-sm"></i>
        </div>
        <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
            <div class="flex gap-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
        </div>
    `;

    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    return id;
}

function removeTypingIndicator(id) {
    const typingDiv = document.getElementById(id);
    if (typingDiv) {
        typingDiv.remove();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderMarkdownSafe(text) {
    const escaped = escapeHtml(text || '');
    const lines = escaped.split('\n');
    const html = [];
    let inList = false;

    for (const rawLine of lines) {
        const line = rawLine.trim();
        const listMatch = line.match(/^([-*]|\d+\.)\s+(.+)$/);

        if (listMatch) {
            if (!inList) {
                html.push('<ul class="list-disc list-inside space-y-1 my-2">');
                inList = true;
            }
            html.push(`<li>${formatInlineMarkdown(listMatch[2])}</li>`);
            continue;
        }

        if (inList) {
            html.push('</ul>');
            inList = false;
        }

        if (!line) {
            html.push('<br>');
        } else {
            html.push(`<p class="mb-2">${formatInlineMarkdown(line)}</p>`);
        }
    }

    if (inList) {
        html.push('</ul>');
    }

    return html.join('');
}

function formatInlineMarkdown(line) {
    return line
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.+?)__/g, '<strong>$1</strong>');
}

// Handle Enter key in chat
if (document.getElementById('chat-input')) {
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('chat-form').dispatchEvent(new Event('submit'));
        }
    });
}
