// ============================================================
// app.js — Orquestador principal de TUT0hub
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
import { initPreferences } from './preferences.js';
import { translatePage, cacheOriginalTexts } from './i18n.js';

// Exponer al scope global para que preferences.js pueda llamarlas
window.translatePage = translatePage;
window.cacheOriginalTexts = cacheOriginalTexts;

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
// Inicializacion principal
// -------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    console.log('[App] DOMContentLoaded - Inicializando...');

    // 1. Cachear textos originales antes de cualquier traduccion
    if (window.cacheOriginalTexts) {
        window.cacheOriginalTexts();
    }

    // 2. Aplicar idioma guardado
    if (window.translatePage) {
        window.translatePage();
    }

    // 3. Inicializar modulos de UI
    initScrollAnimations();
    initMagneticButtons();
    initFavorites();
    initSearchDebounce();
    initCarousels();
    initPolling();
    initInfiniteScroll();

    // 4. Preferencias (formulario interactivo en perfil)
    initPreferences();

    // 5. Animacion escalonada de tarjetas ya presentes en el DOM
    animateCards('.video-card');

    console.log('[App] Inicializacion completada');
});

// -------------------------------------------------------
// Sistema de favoritos
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

        const wasActive = btn.classList.contains('active');
        updateFavoriteButton(btn, !wasActive);

        const ok = await toggleFavorite(videoId, videoData);

        if (ok) {
            showToast(
                wasActive ? 'Eliminado de favoritos' : 'Agregado a favoritos',
                wasActive ? 'info' : 'success'
            );
            pulseElement(btn);
        } else {
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

    const debouncedHint = debounce((value) => {
        searchInput.style.borderColor = value.length > 1 ? '#ffb700' : '';
    }, 300);

    searchInput.addEventListener('input', (e) => debouncedHint(e.target.value));

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInput.value = '';
            searchInput.style.borderColor = '';
            searchInput.blur();
        }
    });
}

// -------------------------------------------------------
// Carruseles
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
// Polling — actualizacion silenciosa cada 30s
// -------------------------------------------------------

const POLL_INTERVAL_MS = 30_000;
let pollTimer = null;
const seenIds = new Set();

function initPolling() {
    if (!document.querySelector('.video-grid')) return;

    document.querySelectorAll('[data-video-id]').forEach(el => {
        seenIds.add(el.dataset.videoId);
    });

    poll();
}

async function poll() {
    try {
        const response = await fetch('/dashboard', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) throw new Error('Poll failed');

        const html = await response.text();
        const doc = new DOMParser().parseFromString(html, 'text/html');
        let newCount = 0;

        doc.querySelectorAll('[data-video-id]').forEach(card => {
            if (!seenIds.has(card.dataset.videoId)) {
                newCount++;
                seenIds.add(card.dataset.videoId);
            }
        });

        if (newCount > 0) notifyNewContent(newCount);

    } catch {
        console.log('[Polling] Sin actualizaciones');
    } finally {
        pollTimer = setTimeout(poll, POLL_INTERVAL_MS);
    }
}

function notifyNewContent(count) {
    const msg = count === 1
        ? 'Hay 1 video nuevo disponible'
        : `Hay ${count} videos nuevos disponibles`;

    showToast(msg, 'info', 6000);

    const heading = document.querySelector('.dashboard-content h1');
    if (heading) pulseElement(heading);

    const bar = document.createElement('div');
    bar.className = 'refresh-bar';
    bar.innerHTML = `
        <span>${msg}</span>
        <button onclick="location.reload()" class="btn-refresh">Actualizar</button>
        <button onclick="this.parentElement.remove()" class="btn-dismiss">x</button>
    `;
    document.body.prepend(bar);
    setTimeout(() => bar.remove(), 10_000);
}

export function stopPolling() {
    if (pollTimer) {
        clearTimeout(pollTimer);
        pollTimer = null;
    }
}

// -------------------------------------------------------
// Infinite Scroll
// -------------------------------------------------------

function initInfiniteScroll() {
    const grid = document.querySelector('.video-grid');
    if (!grid) return;

    const searchInput = document.querySelector('.header input[name="q"]');
    if (searchInput && searchInput.value) {
        infiniteScrollState.isSearchResults = true;
        infiniteScrollState.searchQuery = searchInput.value;
    }

    const sentinel = document.createElement('div');
    sentinel.className = 'infinite-scroll-sentinel';
    grid.parentElement.appendChild(sentinel);

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting && !infiniteScrollState.isLoading && infiniteScrollState.hasMore) {
                    loadMoreVideosHandler();
                }
            });
        },
        { rootMargin: '200px' }
    );

    observer.observe(sentinel);
    console.log('[Infinite Scroll] Inicializado');
}

async function loadMoreVideosHandler() {
    if (infiniteScrollState.isLoading || !infiniteScrollState.hasMore) return;

    infiniteScrollState.isLoading = true;

    const loadingBar = document.createElement('div');
    loadingBar.className = 'loading-bar';
    loadingBar.innerHTML = '<div class="spinner"></div><p>Cargando mas videos...</p>';
    document.querySelector('.video-grid').parentElement.appendChild(loadingBar);

    try {
        let data;

        if (infiniteScrollState.isSearchResults) {
            data = await loadMoreSearchResults(
                infiniteScrollState.searchQuery,
                infiniteScrollState.nextPageToken
            );
        } else {
            const url = infiniteScrollState.nextPageToken
                ? `/api/videos?per_page=12&page_token=${encodeURIComponent(infiniteScrollState.nextPageToken)}`
                : '/api/videos?per_page=12';

            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            data = await response.json();
        }

        if (data.videos && data.videos.length > 0) {
            appendVideosToGrid(data.videos, data.favorite_ids || []);
            animateCards('[data-animated="false"]');
            document.querySelectorAll('[data-animated="false"]').forEach(el => {
                el.setAttribute('data-animated', 'true');
            });

            infiniteScrollState.nextPageToken = data.nextPageToken || null;
            infiniteScrollState.hasMore = data.has_more || false;

            showToast(`Cargados ${data.videos.length} videos`, 'success', 2000);
        } else {
            infiniteScrollState.hasMore = false;
            showToast('No hay mas videos disponibles', 'info', 3000);
        }
    } catch (err) {
        console.error('[loadMoreVideos] Error:', err);
        showToast('Error al cargar mas videos', 'danger', 3000);
    } finally {
        infiniteScrollState.isLoading = false;
        loadingBar.remove();
    }
}