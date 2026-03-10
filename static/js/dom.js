// ============================================================
// dom.js — Módulo de manipulación del DOM
// Renderizado dinámico, loaders, errores, estado
// ============================================================

// -------------------------------------------------------
// Loader / Indicador de carga
// -------------------------------------------------------

/**
 * Muestra un spinner de carga dentro de un contenedor
 * @param {HTMLElement} container
 * @param {string} message
 */
export function showLoader(container, message = 'Cargando...') {
    container.innerHTML = `
        <div class="loader-container" role="status" aria-live="polite">
            <div class="loader-spinner"></div>
            <p class="loader-text">${message}</p>
        </div>
    `;
}

/**
 * Elimina el loader de un contenedor
 * @param {HTMLElement} container
 */
export function hideLoader(container) {
    const loader = container.querySelector('.loader-container');
    if (loader) loader.remove();
}

// -------------------------------------------------------
// Mensajes de error / vacío
// -------------------------------------------------------

/**
 * Muestra un mensaje de error visual
 * @param {HTMLElement} container
 * @param {string} message
 */
export function showError(container, message = 'Ocurrió un error. Intenta de nuevo.') {
    container.innerHTML = `
        <div class="error-message-box" role="alert">
            <span class="error-icon">⚠️</span>
            <p>${message}</p>
            <button class="btn-retry" onclick="location.reload()">Reintentar</button>
        </div>
    `;
}

/**
 * Muestra mensaje cuando no hay resultados
 * @param {HTMLElement} container
 * @param {string} message
 */
export function showEmpty(container, message = 'No se encontraron resultados.') {
    container.innerHTML = `
        <div class="empty-state">
            <span class="empty-icon">🔍</span>
            <p>${message}</p>
        </div>
    `;
}

// -------------------------------------------------------
// Notificación toast (sin recargar página)
// -------------------------------------------------------

/**
 * Muestra una notificación tipo toast
 * @param {string} message
 * @param {'success'|'danger'|'info'|'warning'} type
 * @param {number} duration en ms
 */
export function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container')
        || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <span class="toast-message">${message}</span>
        <button class="toast-close" aria-label="Cerrar">×</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
        dismissToast(toast);
    });

    container.appendChild(toast);

    // Forzar reflow para activar la transición de entrada
    requestAnimationFrame(() => {
        requestAnimationFrame(() => toast.classList.add('toast-visible'));
    });

    // Auto-dismiss
    setTimeout(() => dismissToast(toast), duration);
}

function dismissToast(toast) {
    toast.classList.remove('toast-visible');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
}

function createToastContainer() {
    const div = document.createElement('div');
    div.id = 'toast-container';
    div.setAttribute('aria-live', 'polite');
    document.body.appendChild(div);
    return div;
}

// -------------------------------------------------------
// Renderizar tarjeta de video
// -------------------------------------------------------

/**
 * Crea el HTML de una tarjeta de video
 * @param {object} video - { id, title, thumbnail, channel, description }
 * @param {boolean} isFavorite
 * @returns {HTMLElement}
 */
export function createVideoCard(video, isFavorite = false) {
    const card = document.createElement('div');
    card.className = 'card video-card fade-in-card';
    card.dataset.videoId = video.id;

    card.innerHTML = `
        <a href="https://youtube.com/watch?v=${video.id}" 
           target="_blank" 
           rel="noopener noreferrer"
           class="video-thumbnail">
            <img src="${escapeHtml(video.thumbnail)}" 
                 alt="${escapeHtml(video.title)}" 
                 loading="lazy">
            <div class="video-overlay">
                <span class="play-icon">▶</span>
            </div>
        </a>
        <div class="video-info">
            <div class="video-header">
                <h3 class="video-title">${escapeHtml(truncate(video.title, 60))}</h3>
                <button class="favorite-btn ${isFavorite ? 'active' : ''}"
                        data-video-id="${video.id}"
                        data-title="${escapeHtml(video.title)}"
                        data-channel="${escapeHtml(video.channel || '')}"
                        data-description="${escapeHtml(video.description || '')}"
                        data-thumbnail="${escapeHtml(video.thumbnail || '')}"
                        title="${isFavorite ? 'Quitar de favoritos' : 'Agregar a favoritos'}"
                        aria-pressed="${isFavorite}">
                    ${isFavorite ? '★' : '☆'}
                </button>
            </div>
            <p class="video-channel">${escapeHtml(video.channel || '')}</p>
            <p class="video-description">${escapeHtml(truncate(video.description || '', 100))}</p>
        </div>
    `;

    return card;
}

// -------------------------------------------------------
// Renderizar grid de videos
// -------------------------------------------------------

/**
 * Renderiza una lista de videos en un contenedor con animación escalonada
 * @param {HTMLElement} container
 * @param {Array} videos
 * @param {Array<string>} favoriteIds
 */
export function renderVideoGrid(container, videos, favoriteIds = []) {
    container.innerHTML = '';

    if (!videos || videos.length === 0) {
        showEmpty(container, 'No se encontraron videos.');
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'video-grid';

    videos.forEach((video, index) => {
        const isFavorite = favoriteIds.includes(video.id);
        const card = createVideoCard(video, isFavorite);
        // Animación escalonada
        card.style.animationDelay = `${index * 60}ms`;
        grid.appendChild(card);
    });

    container.appendChild(grid);
}

/**
 * Añade más videos al grid existente (para infinite scroll)
 * @param {Array} videos
 * @param {Array<string>} favoriteIds
 * @param {boolean} animateNew - animar los nuevos videos
 */
export function appendVideosToGrid(videos, favoriteIds = [], animateNew = true) {
    const grid = document.querySelector('.video-grid');
    if (!grid) {
        console.warn('[appendVideosToGrid] No hay .video-grid en el DOM');
        return;
    }

    if (!videos || videos.length === 0) {
        console.log('[appendVideosToGrid] Sin nuevos videos para agregar');
        return;
    }

    const currentCount = grid.querySelectorAll('.video-card').length;

    videos.forEach((video, index) => {
        const isFavorite = favoriteIds.includes(video.id);
        const card = createVideoCard(video, isFavorite);
        card.setAttribute('data-animated', 'false'); // Marcar para animar
        
        if (animateNew) {
            card.style.animationDelay = `${(index) * 60}ms`;
        }
        
        grid.appendChild(card);
    });

    console.log(`[appendVideosToGrid] Agregados ${videos.length} videos. Total: ${currentCount + videos.length}`);
}

// -------------------------------------------------------
// Helpers
// -------------------------------------------------------

/**
 * Escapa caracteres HTML para prevenir XSS
 */
function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Trunca un texto a N caracteres
 */
function truncate(str, max) {
    if (!str) return '';
    return str.length > max ? str.slice(0, max) + '...' : str;
}

/**
 * Actualiza visualmente un botón de favorito sin recargar
 * @param {HTMLButtonElement} btn
 * @param {boolean} isActive
 */
export function updateFavoriteButton(btn, isActive) {
    btn.classList.toggle('active', isActive);
    btn.textContent = isActive ? '★' : '☆';
    btn.title = isActive ? 'Quitar de favoritos' : 'Agregar a favoritos';
    btn.setAttribute('aria-pressed', String(isActive));
}