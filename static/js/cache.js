// ============================================================
// cache.js — Caché manual en memoria
// Evita llamadas repetidas a la API
// ============================================================

const Cache = (() => {
    const _store = new Map();
    const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutos

    /**
     * Guarda un valor en caché con TTL
     * @param {string} key
     * @param {*} value
     * @param {number} ttl - tiempo de vida en ms
     */
    function set(key, value, ttl = DEFAULT_TTL) {
        _store.set(key, {
            value,
            expiresAt: Date.now() + ttl
        });
    }

    /**
     * Obtiene un valor del caché (null si expiró o no existe)
     * @param {string} key
     * @returns {*|null}
     */
    function get(key) {
        const entry = _store.get(key);
        if (!entry) return null;

        if (Date.now() > entry.expiresAt) {
            _store.delete(key);
            return null;
        }

        return entry.value;
    }

    /**
     * Elimina una entrada del caché
     * @param {string} key
     */
    function remove(key) {
        _store.delete(key);
    }

    /**
     * Limpia entradas expiradas
     */
    function cleanup() {
        const now = Date.now();
        for (const [key, entry] of _store.entries()) {
            if (now > entry.expiresAt) {
                _store.delete(key);
            }
        }
    }

    /**
     * Vacía todo el caché
     */
    function clear() {
        _store.clear();
    }

    /**
     * Verifica si una clave existe y es válida
     * @param {string} key
     * @returns {boolean}
     */
    function has(key) {
        return get(key) !== null;
    }

    // Limpiar expiradas cada 2 minutos
    setInterval(cleanup, 2 * 60 * 1000);

    return { set, get, remove, clear, has };
})();

export default Cache;