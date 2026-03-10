// ============================================================
// app.js — Orquestador principal de TUT0hub
// Inicializa módulos, maneja favoritos, polling, buscador
// ============================================================

import { debounce, toggleFavorite, loadMoreVideos, loadMoreSearchResults } from './api.js';
import {
    showLoader,
    hideLoader,
    showError,
    showToast,
    updateFavoriteButton,
    appendVideosToGrid
} from './dom.js';
import {
    initScrollAnimations,
    animateCards,
    initMagneticButtons,
    initParallax,
    pulseElement
} from './animations.js';
import { Carousel } from './carousel.js';

// -------------------------------------------------------
// Estado de infinite scroll
// -------------------------------------------------------
const infiniteScrollState = {
    isLoading: false,
    nextPageToken: null,
    hasMore: true,
    isSearchResults: false,
    searchQuery: ''
};

// -------------------------------------------------------
// Inicialización principal
// -------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    initMagneticButtons();
    initFavorites();
    initSearchDebounce();
    initCarousels();
    initPolling();
    initInfiniteScroll();

    // Animación escalonada de tarjetas ya presentes en el DOM
    animateCards('.video-card');

    console.log('[TUT0hub] App inicializada ✅');
});

// -------------------------------------------------------
// Sistema de favoritos (sin recargar página)
// -------------------------------------------------------

function initFavorites() {
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.favorite-btn');
        if (!btn) return;

        e.preventDefault();
        e.stopPropagation();

        const videoId = btn.dataset.videoId;
        const videoData = {
            title: btn.dataset.title,
            channel: btn.dataset.channel,
            description: btn.dataset.description,
            thumbnail: btn.dataset.thumbnail
        };

        // Estado optimista: actualizar UI inmediatamente
        const wasActive = btn.classList.contains('active');
        updateFavoriteButton(btn, !wasActive);

        const ok = await toggleFavorite(videoId, videoData);

        if (ok) {
            showToast(
                wasActive ? '⭐ Eliminado de favoritos' : '★ Agregado a favoritos',
                wasActive ? 'info' : 'success'
            );
            pulseElement(btn);
        } else {
            // Revertir si falló
            updateFavoriteButton(btn, wasActive);
            showToast('Error al actualizar favoritos', 'danger');
        }
    });
}

// -------------------------------------------------------
// Buscador con Debounce
// -------------------------------------------------------

function initSearchDebounce() {
    const searchInput = document.querySelector('.header input[name="q"]');
    if (!searchInput) return;

    // Muestra indicador visual mientras el usuario escribe
    const debouncedHint = debounce((value) => {
        if (value.length > 1) {
            searchInput.style.borderColor = '#ffb700';
        } else {
            searchInput.style.borderColor = '';
        }
    }, 300);

    searchInput.addEventListener('input', (e) => {
        debouncedHint(e.target.value);
    });

    // Cancelar petición previa al escribir (AbortController está en api.js)
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInput.value = '';
            searchInput.style.borderColor = '';
            searchInput.blur();
        }
    });
}

// -------------------------------------------------------
// Carruseles (si existen en la página)
// -------------------------------------------------------

function initCarousels() {
    document.querySelectorAll('.carousel').forEach(el => {
        new Carousel(el, {
            autoplay: true,
            autoplayDelay: 5000,
            loop: true
        });
    });
}

// -------------------------------------------------------
// Polling inteligente — Reto final
// Simula actualización en tiempo real sin WebSocket
// -------------------------------------------------------

const POLL_INTERVAL_MS = 30_000; // 30 segundos
let pollTimer = null;
let lastKnownCount = null;
const seenIds = new Set();

/**
 * Inicia el polling solo en el dashboard
 */
function initPolling() {
    // Solo activar en el dashboard principal
    if (!document.querySelector('.video-grid')) return;

    // Registrar IDs actuales para prevenir duplicados
    document.querySelectorAll('[data-video-id]').forEach(el => {
        seenIds.add(el.dataset.videoId);
    });
    lastKnownCount = seenIds.size;

    poll();
}

async function poll() {
    try {
        // Hacemos una petición silenciosa al endpoint de trending
        // para verificar si hay contenido nuevo
        const response = await fetch('/dashboard', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });

        if (!response.ok) throw new Error('Poll failed');

        // Parsear respuesta (el backend devuelve HTML)
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        const newCards = doc.querySelectorAll('[data-video-id]');
        let newCount = 0;

        newCards.forEach(card => {
            if (!seenIds.has(card.dataset.videoId)) {
                newCount++;
                seenIds.add(card.dataset.videoId);
            }
        });

        if (newCount > 0) {
            notifyNewContent(newCount);
        }

    } catch (err) {
        // Silencioso: el polling no debe interrumpir la UX
        console.log('[Polling] Sin actualizaciones');
    } finally {
        // Programar próxima verificación con control de frecuencia
        pollTimer = setTimeout(poll, POLL_INTERVAL_MS);
    }
}

/**
 * Notificación visual cuando llegan nuevos datos
 * @param {number} count
 */
function notifyNewContent(count) {
    // Toast de notificación
    const msg = count === 1
        ? '🔔 Hay 1 video nuevo disponible'
        : `🔔 Hay ${count} videos nuevos disponibles`;

    showToast(msg, 'info', 6000);

    // Pulsar el título de la sección
    const heading = document.querySelector('.dashboard-content h1');
    if (heading) pulseElement(heading);

    // Botón para recargar si el usuario quiere ver el contenido nuevo
    const refreshBar = document.createElement('div');
    refreshBar.className = 'refresh-bar';
    refreshBar.innerHTML = `
        <span>${msg}</span>
        <button onclick="location.reload()" class="btn-refresh">
            Actualizar
        </button>
        <button onclick="this.parentElement.remove()" class="btn-dismiss">×</button>
    `;
    document.body.prepend(refreshBar);

    // Auto-ocultar la barra después de 10s
    setTimeout(() => refreshBar.remove(), 10_000);
}

/**
 * Detiene el polling (ej: al cambiar de página)
 */
export function stopPolling() {
    if (pollTimer) {
        clearTimeout(pollTimer);
        pollTimer = null;
    }
}

// -------------------------------------------------------
// Infinite Scroll — Carga automática de más videos
// -------------------------------------------------------

/**
 * Inicializa el sistema de infinite scroll
 * Detecta cuando el usuario está cerca del final de la página
 */
function initInfiniteScroll() {
    // Solo si hay un grid de videos
    const grid = document.querySelector('.video-grid');
    if (!grid) return;

    // Detectar si estamos en búsqueda
    const searchInput = document.querySelector('.header input[name="q"]');
    if (searchInput && searchInput.value) {
        infiniteScrollState.isSearchResults = true;
        infiniteScrollState.searchQuery = searchInput.value;
    }

    // Crear elemento centinela al final del grid
    const sentinel = document.createElement('div');
    sentinel.className = 'infinite-scroll-sentinel';
    sentinel.style.height = '100px';
    grid.parentElement.appendChild(sentinel);

    // IntersectionObserver: se dispara cuando el centinela entra en viewport
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting && !infiniteScrollState.isLoading && infiniteScrollState.hasMore) {
                    loadMoreVideosHandler();
                }
            });
        },
        {
            rootMargin: '200px' // Empezar a cargar 200px antes de llegar al final
        }
    );

    observer.observe(sentinel);
    console.log('[Infinite Scroll] Inicializado ✅');
}

/**
 * Carga el siguiente lote de videos
 */
async function loadMoreVideosHandler() {
    if (infiniteScrollState.isLoading || !infiniteScrollState.hasMore) return;

    infiniteScrollState.isLoading = true;

    const loadingBar = document.createElement('div');
    loadingBar.className = 'loading-bar';
    loadingBar.innerHTML = '<div class="spinner"></div><p>Cargando más videos...</p>';
    document.querySelector('.video-grid').parentElement.appendChild(loadingBar);

    try {
        let data;

        if (infiniteScrollState.isSearchResults) {
            // Cargar resultados de búsqueda
            data = await loadMoreSearchResults(
                infiniteScrollState.searchQuery,
                infiniteScrollState.nextPageToken
            );
        } else {
            // Cargar videos del dashboard (trending)
            const url = infiniteScrollState.nextPageToken 
                ? `/api/videos?per_page=12&page_token=${encodeURIComponent(infiniteScrollState.nextPageToken)}`
                : '/api/videos?per_page=12';
            
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            data = await response.json();
        }

        if (data.videos && data.videos.length > 0) {
            // Agregar videos al grid
            appendVideosToGrid(data.videos, data.favorite_ids || []);

            // Reinicializar las animaciones para los nuevos videos
            animateCards('[data-animated="false"]');
            
            // Marcar como animados
            document.querySelectorAll('[data-animated="false"]').forEach(el => {
                el.setAttribute('data-animated', 'true');
            });

            // Actualizar estado
            infiniteScrollState.nextPageToken = data.nextPageToken || null;
            infiniteScrollState.hasMore = data.has_more || false;

            showToast(`✅ Cargados ${data.videos.length} videos`, 'success', 2000);
            console.log('[loadMoreVideos] Token siguiente:', infiniteScrollState.nextPageToken, '- Más disponibles:', infiniteScrollState.hasMore);
        } else {
            infiniteScrollState.hasMore = false;
            showToast('📺 No hay más videos disponibles', 'info', 3000);
        }
    } catch (err) {
        console.error('[loadMoreVideos] Error:', err);
        showToast('❌ Error al cargar más videos', 'danger', 3000);
    } finally {
        infiniteScrollState.isLoading = false;
        loadingBar.remove();
    }
}