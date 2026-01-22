// Custom JavaScript to send user_type to Chainlit backend

window.addEventListener('chainlit-user-type', (event) => {
    console.log('[Chainlit Custom JS] Received user_type event:', event.detail);
    
    // Send to backend via Chainlit's socket connection
    if (window.chainlitSocket) {
        window.chainlitSocket.emit('set_user_type', event.detail);
    }
});

// Also check on page load
window.addEventListener('load', () => {
    const userType = localStorage.getItem('user_type') || 'Client';
    console.log('[Chainlit Custom JS] User type from localStorage:', userType);
});
