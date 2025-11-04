// Firebase Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Firebase configuration (replace with your actual config)
const firebaseConfig = {
    apiKey: "AIzaSyA0NIBtI0M1RNvN1_6U9lUQ499wBQgVzIM",
    authDomain: "ai-ingredients-3a169.firebaseapp.com",
    projectId: "ai-ingredients-3a169",
    storageBucket: "ai-ingredients-3a169.firebasestorage.app",
    messagingSenderId: "396842128462",
    appId: "1:396842128462:web:c07f515fa39ec9b7491f1f",
    measurementId: "G-S52J89R49S"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get messaging instance
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('Received background message:', payload);

    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/icon-192x192.png',
        badge: '/static/badge-72x72.png',
        vibrate: [200, 100, 200],
        tag: 'ingredientiq-notification',
        data: payload.data
    };

    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    
    event.notification.close();

    if (event.action === 'open' || !event.action) {
        // Open the app
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then((clientList) => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url.includes('/foodapp/test-notifications/') && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window if app is not open
                if (clients.openWindow) {
                    return clients.openWindow('/foodapp/test-notifications/mobile/');
                }
            })
        );
    }
}); 