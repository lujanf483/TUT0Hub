
import Cache from './cache.js';

// Controladores activos para cancelación
const _controllers = new Map();

// -------------------------------------------------------
// Utilidades de control de tiempo
// -------------------------------------------------------

/**
 * Debounce: retrasa la ejecución hasta que el usuario deje de escribir
 * @param {Function} fn
 * @param {number} delay en ms
 * @returns {Function}
 */
export function debounce(fn, delay = 400) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}

/**
 * Throttle: ejecuta como máximo una vez por intervalo
 * @param {Function} fn
 * @param {number} limit en ms
 * @returns {Function}
 */
export function throttle(fn, limit = 300) {
    let inThrottle = false;
    return (...args) => {
        if (!inThrottle) {
            fn(...args);
            inThrottle = true;
            setTimeout(() => (inThrottle = false), limit);
        }
    };
}

// -------------------------------------------------------
// Petición base con AbortController y caché
// -------------------------------------------------------

/**
 * Fetch con caché, cancelación y manejo de errores
 * @param {string} url
 * @param {object} options
 * @param {string} cacheKey - clave para el caché (null para no cachear)
 * @returns {Promise<object>}
 */
async function fetchWithCache(url, options = {}, cacheKey = null) {
    // Revisar caché primero
    if (cacheKey) {
        const cached = Cache.get(cacheKey);
        if (cached) {
            console.log(`[Cache HIT] ${cacheKey}`);
            return cached;
        }
    }

    // Cancelar petición anterior con misma clave si existe
    if (cacheKey && _controllers.has(cacheKey)) {
        _controllers.get(cacheKey).abort();
    }

    // Crear nuevo controlador
    const controller = new AbortController();
    if (cacheKey) _controllers.set(cacheKey, controller);

    try {
        console.time(`[API] ${url}`);
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        console.timeEnd(`[API] ${url}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Guardar en caché
        if (cacheKey) {
            Cache.set(cacheKey, data);
            _controllers.delete(cacheKey);
        }

        return data;

    } catch (err) {
        if (err.name === 'AbortError') {
            console.log(`[Cancelado] ${url}`);
            return null;
        }
        console.error(`[Error API] ${url}:`, err.message);
        throw err;
    }
}

// -------------------------------------------------------
// Cancelar una petición en curso
// -------------------------------------------------------
export function cancelRequest(key) {
    if (_controllers.has(key)) {
        _controllers.get(key).abort();
        _controllers.delete(key);
    }
}

// -------------------------------------------------------
// Búsqueda de videos con debounce (uso interno)
// -------------------------------------------------------

/**
 * Busca videos en el backend Flask
 * @param {string} query
 * @returns {Promise<Array>}
 */
export async function searchVideos(query) {
    if (!query || query.trim().length < 2) return [];

    const cacheKey = `search:${query.trim().toLowerCase()}`;
    const url = `/search/?q=${encodeURIComponent(query.trim())}`;

    // Esta ruta devuelve HTML, así que usamos el endpoint JSON si existiera.
    // Para el proyecto actual hacemos fetch del HTML y retornamos desde caché
    try {
        const cached = Cache.get(cacheKey);
        if (cached) return cached;

        // Marcar como en progreso (simulación: retornamos señal para que el DOM maneje)
        return { query, fromCache: false };
    } catch (err) {
        console.error('[searchVideos]', err);
        return [];
    }
}

// -------------------------------------------------------
// Promise.all — carga múltiple simultánea
// -------------------------------------------------------

/**
 * Carga múltiples URLs en paralelo
 * Maneja errores parciales: si una falla, las demás continúan
 * @param {Array<{url: string, key: string}>} requests
 * @returns {Promise<Array<{key, data, error}>>}
 */
export async function fetchMultiple(requests) {
    const promises = requests.map(async ({ url, key }) => {
        try {
            const data = await fetchWithCache(url, {}, key);
            return { key, data, error: null };
        } catch (err) {
            console.warn(`[fetchMultiple] Falló ${key}:`, err.message);
            return { key, data: null, error: err.message };
        }
    });

    // Promise.all: lanza todas en paralelo
    // Al usar try/catch en cada una, un fallo no cancela las demás
    const results = await Promise.all(promises);

    const failed = results.filter(r => r.error);
    if (failed.length > 0) {
        console.warn(`[fetchMultiple] ${failed.length} petición(es) fallaron:`,
            failed.map(f => f.key));
    }

    return results;
}

// -------------------------------------------------------
// Toggle favorito con CSRF
// -------------------------------------------------------

/**
 * Agrega o quita un video de favoritos
 * @param {string} videoId
 * @param {object} videoData
 * @returns {Promise<boolean>}
 */
export async function toggleFavorite(videoId, videoData) {
    const csrfToken = document.querySelector('[name="csrf_token"]')?.value
        || document.cookie.match(/csrf_token=([^;]+)/)?.[1]
        || '';

    try {
        const response = await fetch(`/toggle-favorite/${videoId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(videoData)
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        // Invalidar caché relacionado con favoritos
        Cache.remove('favorites');

        return true;
    } catch (err) {
        console.error('[toggleFavorite]', err);
        return false;
    }
}

// -------------------------------------------------------
// Infinite Scroll — Carga más videos
// -------------------------------------------------------

/**
 * Carga más videos del dashboard (trending)
 * @param {number} page número de página (comienza en 1)
 * @param {number} perPage videos por página (12, 24, o 50)
 * @returns {Promise<object>}
 */
export async function loadMoreVideos(page = 1, perPage = 12) {
    const url = `/api/videos?per_page=${perPage}`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        console.log(`[loadMoreVideos] Página:`, data.videos.length, 'videos');
        
        return data;
    } catch (err) {
        console.error('[loadMoreVideos]', err);
        return { videos: [], has_more: false, nextPageToken: null };
    }
}

/**
 * Carga más resultados de búsqueda
 * @param {string} query término de búsqueda
 * @param {number} page número de página
 * @param {number} perPage videos por página
 * @returns {Promise<object>}
 */
export async function loadMoreSearchResults(query, pageToken = null, perPage = 12) {
    if (!query || query.length < 2) {
        return { videos: [], has_more: false, nextPageToken: null };
    }
    
    let url = `/search/api/search?q=${encodeURIComponent(query)}&per_page=${perPage}`;
    if (pageToken) {
        url += `&page_token=${encodeURIComponent(pageToken)}`;
    }
    
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        console.log(`[loadMoreSearchResults] "${query}":`, data.videos.length, 'videos');
        
        return data;
    } catch (err) {
        console.error('[loadMoreSearchResults]', err);
        return { videos: [], has_more: false, nextPageToken: null };
    }
}