const CACHE_NAME = 'conductor-cache-v1';
const STATIC_URLS = [
    '/conductor/dashboard/',
    '/static/css/styles.css',
    '/static/js/main.js',
    '/static/js/i18n.js',
    'https://unpkg.com/html5-qrcode'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(STATIC_URLS);
        })
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Intercept POST to /conductor/verify/
    if (event.request.method === 'POST' && url.pathname === '/conductor/verify/') {
        event.respondWith(
            fetch(event.request.clone()).catch(async () => {
                // If offline, queue the request in IndexedDB
                const req = await event.request.clone().json();
                await saveToQueue(req.ticket_uuid);
                
                // Register background sync if available
                if ('sync' in self.registration) {
                    try {
                        await self.registration.sync.register('verify-queue');
                    } catch (err) {
                        console.error('Sync registration failed:', err);
                    }
                }
                
                // Return a mock successful response so the frontend knows it's queued
                return new Response(JSON.stringify({
                    valid: true,
                    message: "Queued for sync",
                    passenger_name: "Offline Scan",
                    from_stop: "Unknown",
                    to_stop: "Unknown"
                }), {
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
        return;
    }

    // Default strategy: Network First, fallback to cache for HTML/API, Cache First for static
    if (url.pathname.startsWith('/static/') || url.hostname === 'unpkg.com') {
        event.respondWith(
            caches.match(event.request).then(response => {
                return response || fetch(event.request);
            })
        );
    } else {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
    }
});

// IndexedDB Helper
function openDB() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open('ConductorSyncDB', 1);
        req.onupgradeneeded = e => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains('verifyQueue')) {
                db.createObjectStore('verifyQueue', { keyPath: 'id', autoIncrement: true });
            }
        };
        req.onsuccess = e => resolve(e.target.result);
        req.onerror = e => reject(e.target.error);
    });
}

async function saveToQueue(ticket_uuid) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('verifyQueue', 'readwrite');
        const store = tx.objectStore('verifyQueue');
        store.put({ ticket_uuid, timestamp: Date.now() });
        tx.oncomplete = () => resolve();
        tx.onerror = e => reject(e.target.error);
    });
}

async function getQueue() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('verifyQueue', 'readonly');
        const store = tx.objectStore('verifyQueue');
        const req = store.getAll();
        req.onsuccess = e => resolve(e.target.result);
        req.onerror = e => reject(e.target.error);
    });
}

async function clearQueueItem(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction('verifyQueue', 'readwrite');
        const store = tx.objectStore('verifyQueue');
        store.delete(id);
        tx.oncomplete = () => resolve();
        tx.onerror = e => reject(e.target.error);
    });
}

self.addEventListener('sync', event => {
    if (event.tag === 'verify-queue') {
        event.waitUntil(processQueue());
    }
});

async function processQueue() {
    const queue = await getQueue();
    for (const item of queue) {
        try {
            const resp = await fetch('/conductor/verify/', {
                method: 'POST',
                body: JSON.stringify({ ticket_uuid: item.ticket_uuid }),
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (resp.ok) {
                // Remove from queue once successfully synced
                await clearQueueItem(item.id);
                
                // Optional: we can also trigger markAsUsed here if needed,
                // but the prompt only mentions the verify endpoint.
                // Assuming verify implies checking. The user manually clicks "Mark as Used"
                // which goes to `/conductor/expire/`. Since the prompt only mentions `/conductor/verify/`,
                // we'll stick strictly to queuing verify requests. 
                // However, offline tickets are marked "Queued for sync". 
                // The conductor might press "Mark as Used", which calls POST /conductor/expire/.
                // The user prompt specifically only requested queuing POST /conductors/verify/.
            }
        } catch (err) {
            console.error('Failed to sync item:', item.ticket_uuid, err);
            // Throwing an error allows the sync event to be retried
            throw err;
        }
    }
}
