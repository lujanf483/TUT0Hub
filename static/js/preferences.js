/**
 * preferences.js - Gestor de preferencias de usuario (tema e idioma)
 * ⭐ Usa i18n.translatePage para traducir toda la app
 */

/**
 * Inicializar el sistema de preferencias
 */
export function initPreferences() {
    console.log('[Preferences] 🔍 Buscando formulario de preferencias...');
    const form = document.querySelector('form[action*="update_preferences"]');
    
    if (!form) {
        console.warn('[Preferences] ⚠️ Formulario NO encontrado');
        return;
    }
    
    console.log('[Preferences] ✅ Formulario encontrado:', form.action);
    form.addEventListener('submit', handlePreferencesSubmit);
    console.log('[Preferences] Sistema inicializado ✓');
}

/**
 * Manejar envío del formulario de preferencias
 * ⭐ AQUÍ ES DONDE OCURRE LA MAGIA: Cambia idioma y tema
 */
async function handlePreferencesSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const theme = form.querySelector('[name="theme"]')?.value;
    const language = form.querySelector('[name="language"]')?.value;
    const csrfToken = form.querySelector('[name="csrf_token"]')?.value;
    
    console.log('[Preferences] 🚀 ENVIANDO PREFERENCIAS:', { theme, language });
    
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
        
        console.log('[Preferences] ✅ Servidor respondió OK');
        
        // ⭐ APLICAR CAMBIOS INMEDIATAMENTE
        applyTheme(theme);
        applyLanguage(language);
        
        showToast('✓ Preferencias guardadas', 'success');
        
    } catch (error) {
        console.error('[Preferences] ❌ Error:', error.message);
        showToast('✗ Error al guardar preferencias', 'danger');
    }
}

/**
 * Aplicar tema dinámicamente (CSS variables)
 */
function applyTheme(theme) {
    if (!theme) return;
    
    document.body.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    
    try {
        localStorage.setItem('theme', theme);
    } catch (e) {
        console.warn('No se pudo guardar tema en localStorage');
    }
    
    console.log('[Theme] ✅ Tema aplicado:', theme);
}

/**
 * Aplicar idioma dinámicamente
 * ⭐ USA LA FUNCIÓN DE i18n.js PARA TRADUCIR TODO
 */
function applyLanguage(language) {
    if (!language) return;
    
    // Establecer atributos del documento
    document.body.setAttribute('data-language', language);
    document.documentElement.setAttribute('lang', language);
    
    try {
        localStorage.setItem('language', language);
    } catch (e) {
        console.warn('No se pudo guardar idioma en localStorage');
    }
    
    console.log('[Language] 🌐 Aplicando idioma:', language);
    
    // ⭐ AQUÍ LLAMAMOS LA FUNCIÓN GLOBAL DE i18n.js
    if (window.translatePage) {
        console.log('[Language] ⭐ Llamando window.translatePage...');
        const count = window.translatePage(language);
        console.log('[Language] ✅ Traducción completada:', count, 'elementos');
    } else {
        console.error('[Language] ❌ window.translatePage no está disponible!');
    }
}

/**
 * Mostrar notificación
 */
function showToast(message, type = 'info') {
    let flashContainer = document.querySelector('.flash-container');
    
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-container';
        document.body.appendChild(flashContainer);
    }
    
    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `${message}<button onclick="this.parentElement.remove()">×</button>`;
    flashContainer.appendChild(flash);
    
    setTimeout(() => flash.remove?.(), 3000);
}

export { applyTheme, applyLanguage };

// Exportar funciones
export { applyTheme, applyLanguage, showToast, translateAllElements };
