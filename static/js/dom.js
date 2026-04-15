// ============================================================
// dom.js — Módulo de manipulación del DOM
// ============================================================

export function showLoader(container, message = 'Cargando...') {
    container.innerHTML = `
        <div class="loader-container" role="status" aria-live="polite">
            <div class="loader-spinner"></div>
            <p class="loader-text">${message}</p>
        </div>
    `;
}

export function hideLoader(container) {
    const loader = container.querySelector('.loader-container');
    if (loader) loader.remove();
}

export function showError(container, message = 'Ocurrió un error. Intenta de nuevo.') {
    container.innerHTML = `
        <div class="error-message-box" role="alert">
            <span class="error-icon">⚠️</span>
            <p>${message}</p>
            <button class="btn-retry" onclick="location.reload()">Reintentar</button>
        </div>
    `;
}

export function showEmpty(container, message = 'No se encontraron resultados.') {
    container.innerHTML = `
        <div class="empty-state">
            <span class="empty-icon">🔍</span>
            <p>${message}</p>
        </div>
    `;
}

export function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <span class="toast-message">${message}</span>
        <button class="toast-close" aria-label="Cerrar">×</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => dismissToast(toast));
    container.appendChild(toast);

    requestAnimationFrame(() => {
        requestAnimationFrame(() => toast.classList.add('toast-visible'));
    });

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
// Crear tarjeta de video
// IMPORTANTE: El thumbnail usa div + js-open-modal (NO <a href>)
// para que el event delegation del template abra el modal
// en lugar de abrir una pestaña nueva en YouTube.
// -------------------------------------------------------
export function createVideoCard(video, isFavorite = false) {
    const card = document.createElement('div');
    card.className = 'card video-card fade-in-card';
    card.dataset.videoId  = video.id;
    card.dataset.title    = video.title       || '';
    card.dataset.channel  = video.channel     || '';
    card.dataset.description = video.description || '';
    card.dataset.thumbnail   = video.thumbnail   || '';

    card.innerHTML = `
        <div class="video-thumbnail cursor-pointer js-open-modal">
            <img src="${escapeHtml(video.thumbnail)}"
                 alt="${escapeHtml(video.title)}"
                 loading="lazy">
            <div class="video-overlay">
                <span class="play-icon">&#9654;</span>
            </div>
        </div>
        <div class="video-info">
            <div class="video-header">
                <h3 class="video-title cursor-pointer js-open-modal">
                    ${escapeHtml(truncate(video.title, 60))}
                </h3>
                <button class="favorite-btn ${isFavorite ? 'active' : ''}"
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

export function renderVideoGrid(container, videos, favoriteIds = []) {
    container.innerHTML = '';

    if (!videos || videos.length === 0) {
        showEmpty(container, 'No se encontraron videos.');
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'video-grid';

    videos.forEach((video, index) => {
        const card = createVideoCard(video, favoriteIds.includes(video.id));
        card.style.animationDelay = `${index * 60}ms`;
        grid.appendChild(card);
    });

    container.appendChild(grid);
}

export function appendVideosToGrid(videos, favoriteIds = [], animateNew = true) {
    const grid = document.querySelector('.video-grid');
    if (!grid) return;

    if (!videos || videos.length === 0) return;

    const currentCount = grid.querySelectorAll('.video-card').length;

    videos.forEach((video, index) => {
        const card = createVideoCard(video, favoriteIds.includes(video.id));
        card.setAttribute('data-animated', 'false');
        if (animateNew) card.style.animationDelay = `${index * 60}ms`;
        grid.appendChild(card);
    });

    console.log(`[appendVideosToGrid] +${videos.length} videos. Total: ${currentCount + videos.length}`);
}

// -------------------------------------------------------
// Helpers
// -------------------------------------------------------

function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function truncate(str, max) {
    if (!str) return '';
    return str.length > max ? str.slice(0, max) + '...' : str;
}

export function updateFavoriteButton(btn, isActive) {
    btn.classList.toggle('active', isActive);
    btn.textContent = isActive ? '★' : '☆';
    btn.title = isActive ? 'Quitar de favoritos' : 'Agregar a favoritos';
    btn.setAttribute('aria-pressed', String(isActive));
}