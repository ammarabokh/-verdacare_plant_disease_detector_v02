const CACHE_NAME = 'verda-care-v1';
const STATIC_ASSETS = [
    '/',
    '/static/js/main.js',
    '/static/manifest.json',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // API calls: network only
    if (url.pathname.startsWith('/diagnose') ||
        url.pathname.startsWith('/chat') ||
        url.pathname.startsWith('/admin')) {
        return;
    }

    // Static assets: cache first
    if (url.pathname.startsWith('/static/') ||
        url.pathname === '/' ||
        url.pathname.startsWith('/result/')) {
        event.respondWith(
            caches.match(event.request).then(cached => {
                return cached || fetch(event.request).then(response => {
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, response.clone());
                        return response;
                    });
                });
            })
        );
        return;
    }

    // Everything else: network first, cache fallback
    event.respondWith(
        fetch(event.request).then(response => {
            return caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, response.clone());
                return response;
            });
        }).catch(() => caches.match(event.request))
    );
});
