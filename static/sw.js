// Service Worker for IngredientIQ Push Test
const CACHE_NAME = 'ingredientiq-test-v1';
const urlsToCache = [
  '/test-notifications/mobile/',
  '/static/manifest.json',
  '/static/icon-192x192.png'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});

// Push event - handle background push notifications
self.addEventListener('push', (event) => {
  console.log('Push event received:', event);
  
  let notificationData = {};
  
  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (e) {
      notificationData = {
        title: 'IngredientIQ',
        body: event.data.text() || 'New notification'
      };
    }
  }

  const options = {
    body: notificationData.body || 'New notification from IngredientIQ',
    icon: '/static/icon-192x192.png',
    badge: '/static/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: notificationData.data || {},
    actions: [
      {
        action: 'open',
        title: 'Open App',
        icon: '/static/icon-72x72.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/close-icon.png'
      }
    ],
    requireInteraction: true,
    tag: 'ingredientiq-notification'
  };

  event.waitUntil(
    self.registration.showNotification(
      notificationData.title || 'IngredientIQ',
      options
    )
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();

  if (event.action === 'open' || !event.action) {
    // Open the app
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url.includes('/test-notifications/') && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window if app is not open
        if (clients.openWindow) {
          return clients.openWindow('/test-notifications/mobile/');
        }
      })
    );
  }
});

// Background sync (optional)
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Perform background sync tasks
      console.log('Background sync triggered')
    );
  }
});