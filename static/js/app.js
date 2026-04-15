// ============================================================
// app.js — Orquestador principal de TUT0hub
// ============================================================

import { debounce, loadMoreVideos, loadMoreSearchResults } from './api.js';
import {
    showToast,
    appendVideosToGrid
} from './dom.js';
import {
    initScrollAnimations,
    animateCards,
    initMagneticButtons,
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
    // NOTA: initFavorites() fue eliminado intencionalmente.
    // Los favoritos y el modal se manejan con event delegation
    // directamente en cada template (dashboard.html, search.html,
    // advanced_search.html). Tener dos listeners en document causaba
    // que el toggle se activara y cancelara al mismo tiempo.
    initSearchDebounce();
    initCarousels();
    // NOTA: initPolling() fue eliminado intencionalmente.
    // El polling llamaba a /dashboard cada 30s lo cual consumia
    // quota de la YouTube API innecesariamente en produccion.
    initInfiniteScroll();

    // 4. Preferencias (formulario interactivo en perfil)
    initPreferences();

    // 5. Animacion escalonada de tarjetas ya presentes en el DOM
    animateCards('.video-card');

    console.log('[App] Inicializacion completada');
});

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
// Infinite Scroll
// -------------------------------------------------------

function initInfiniteScroll() {
    const grid = document.querySelector('.video-grid');
    if (!grid) return;

    // Detectar si estamos en una página de búsqueda
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