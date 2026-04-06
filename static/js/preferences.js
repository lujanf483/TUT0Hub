
/**
 * preferences.js - Gestor de preferencias de usuario (tema e idioma)
 */

export function initPreferences() {
    const form = document.querySelector('form[action*="update_preferences"]');

    if (!form) {
        return;
    }

    form.addEventListener('submit', handlePreferencesSubmit);
    console.log('[Preferences] Sistema inicializado');
}

async function handlePreferencesSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const theme = form.querySelector('[name="theme"]')?.value;
    const language = form.querySelector('[name="language"]')?.value;
    const csrfToken = form.querySelector('[name="csrf_token"]')?.value;

    console.log('[Preferences] Enviando preferencias:', { theme, language });

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: new URLSearchParams({
                theme,
                language,
                csrf_token: csrfToken
            })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        applyTheme(theme);
        applyLanguage(language);
        showToast('Preferencias guardadas', 'success');

    } catch (error) {
        console.error('[Preferences] Error:', error.message);
        showToast('Error al guardar preferencias', 'danger');
    }
}

export function applyTheme(theme) {
    if (!theme) return;
    document.body.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    console.log('[Theme] Tema aplicado:', theme);
}

export function applyLanguage(language) {
    if (!language) return;
    document.body.setAttribute('data-language', language);
    document.documentElement.setAttribute('lang', language);

    if (window.translatePage) {
        const count = window.translatePage(language);
        console.log('[Language] Traduccion completada:', count, 'elementos');
    } else {
        console.error('[Language] window.translatePage no esta disponible');
    }
}

export function showToast(message, type = 'info') {
    let flashContainer = document.querySelector('.flash-container');

    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-container';
        document.body.appendChild(flashContainer);
    }

    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `${message}<button onclick="this.parentElement.remove()">x</button>`;
    flashContainer.appendChild(flash);

    setTimeout(() => flash.remove(), 3000);
}