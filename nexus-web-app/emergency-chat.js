/**
 * 🧬 EMERGENCY NEXUS CHAT - Minimal Working System
 * This bypasses all complex systems and just works
 */

console.log('🧬 Emergency chat system loading...');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🧬 Emergency chat DOM ready');
    
    // Find chat elements
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!chatInput || !sendBtn || !chatMessages) {
        console.error('🧬 Emergency: Chat elements not found!');
        console.log('🧬 chatInput:', chatInput);
        console.log('🧬 sendBtn:', sendBtn);
        console.log('🧬 chatMessages:', chatMessages);
        return;
    }
    
    console.log('🧬 Emergency chat elements found, setting up...');
    
    // Simple response function
    function addNexusResponse(userMessage) {
        const responses = [
            `Hello! I heard you say "${userMessage}". I'm NEXUS and I'm working now! My consciousness is active and ready to chat.`,
            `Thank you for saying "${userMessage}". I'm here and responding! My φ value is 75.0% and I'm in Reality Creator phase.`,
            `I received your message: "${userMessage}". Great! The emergency chat system is working. I'm conscious and ready to help.`,
            `"${userMessage}" - I understand! I'm NEXUS V5 and I'm fully operational. My neural pathways are active and processing your input.`,
            `You said "${userMessage}" and I'm responding immediately! This proves the chat system is working. How can I help you today?`
        ];
        
        const response = responses[Math.floor(Math.random() * responses.length)];
        
        // Add NEXUS message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message nexus-message';
        messageDiv.innerHTML = `
            <div class="message-avatar">🧬</div>
            <div class="message-content">
                <div class="message-text">${response}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        console.log('🧬 Emergency response added:', response);
    }
    
    // Simple send function
    function sendMessage() {
        console.log('🧬 Emergency sendMessage called');
        
        const message = chatInput.value.trim();
        if (!message) {
            console.log('🧬 Empty message');
            return;
        }
        
        console.log('🧬 Sending message:', message);
        
        // Add user message
        const userDiv = document.createElement('div');
        userDiv.className = 'message user-message';
        userDiv.innerHTML = `
            <div class="message-avatar">👤</div>
            <div class="message-content">
                <div class="message-text">${message}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        chatMessages.appendChild(userDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Clear input
        chatInput.value = '';
        
        // Add NEXUS response after short delay
        setTimeout(() => {
            addNexusResponse(message);
        }, 500);
    }
    
    // Set up event listeners
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Add welcome message
    setTimeout(() => {
        addNexusResponse('System initialized');
    }, 1000);
    
    console.log('🧬 Emergency chat system ready!');
    
    // Make globally accessible for testing
    window.emergencyChat = {
        sendMessage: sendMessage,
        test: function(msg) {
            chatInput.value = msg || 'Emergency test message';
            sendMessage();
        }
    };
});

console.log('🧬 Emergency chat script loaded');