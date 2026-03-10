// ============================================================
// animations.js — Animaciones y efectos visuales avanzados
// IntersectionObserver, parallax, hover magnético, mousemove
// ============================================================

// -------------------------------------------------------
// 1. Animaciones con Scroll (IntersectionObserver)
//    Elementos aparecen con fade + translateY escalonado
// -------------------------------------------------------

/**
 * Observa todos los elementos con [data-animate]
 * y les agrega la clase 'animated' cuando entran en viewport
 */
export function initScrollAnimations() {
    const elements = document.querySelectorAll('[data-animate]');
    if (!elements.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    // Dejar de observar una vez animado
                    observer.unobserve(entry.target);
                }
            });
        },
        {
            threshold: 0.12,
            rootMargin: '0px 0px -40px 0px'
        }
    );

    elements.forEach(el => observer.observe(el));
}

/**
 * Activa animaciones escalonadas en grupos de tarjetas
 * Llama esto después de renderizar el grid de videos
 * @param {string} selector - selector CSS del contenedor
 */
export function animateCards(selector = '.video-card') {
    const cards = document.querySelectorAll(selector);

    cards.forEach((card, i) => {
        card.classList.remove('animated');
        card.style.animationDelay = `${i * 60}ms`;

        // Forzar reflow
        void card.offsetWidth;

        requestAnimationFrame(() => {
            card.classList.add('animated');
        });
    });
}

// -------------------------------------------------------
// 2. Mostrar / Ocultar con transición suave
//    No usa display:none directamente
// -------------------------------------------------------

/**
 * Muestra un elemento con transición de opacidad + altura
 * @param {HTMLElement} el
 * @param {number} duration en ms
 */
export function slideDown(el, duration = 300) {
    el.style.overflow = 'hidden';
    el.style.opacity = '0';
    el.style.maxHeight = '0';
    el.style.transition = `opacity ${duration}ms ease, max-height ${duration}ms ease`;

    // Calcular altura real
    const fullHeight = el.scrollHeight + 'px';

    requestAnimationFrame(() => {
        el.style.maxHeight = fullHeight;
        el.style.opacity = '1';
    });

    el.addEventListener('transitionend', () => {
        el.style.maxHeight = '';
        el.style.overflow = '';
        el.style.transition = '';
    }, { once: true });
}

/**
 * Oculta un elemento con transición suave
 * @param {HTMLElement} el
 * @param {number} duration en ms
 */
export function slideUp(el, duration = 300) {
    el.style.maxHeight = el.scrollHeight + 'px';
    el.style.overflow = 'hidden';
    el.style.transition = `opacity ${duration}ms ease, max-height ${duration}ms ease`;

    requestAnimationFrame(() => {
        el.style.maxHeight = '0';
        el.style.opacity = '0';
    });

    el.addEventListener('transitionend', () => {
        el.style.display = 'none';
        el.style.maxHeight = '';
        el.style.overflow = '';
        el.style.transition = '';
        el.style.opacity = '';
    }, { once: true });
}

/**
 * Alterna visibilidad con transición suave
 * @param {HTMLElement} el
 */
export function toggleSlide(el) {
    const isHidden = el.style.display === 'none'
        || getComputedStyle(el).display === 'none'
        || el.style.maxHeight === '0px';

    if (isHidden) {
        el.style.display = '';
        slideDown(el);
    } else {
        slideUp(el);
    }
}

// -------------------------------------------------------
// 3. Eventos del mouse
// -------------------------------------------------------

/**
 * Efecto magnético en botones:
 * El botón se desplaza levemente hacia el cursor
 * @param {string} selector - selector de los botones
 */
export function initMagneticButtons(selector = '.btn-primary, .btn-secondary') {
    const buttons = document.querySelectorAll(selector);

    buttons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            btn.style.transform = `translate(${x * 0.25}px, ${y * 0.25}px) scale(1.05)`;
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'translate(0, 0) scale(1)';
            btn.style.transition = 'transform 0.4s ease';
        });

        btn.addEventListener('mouseenter', () => {
            btn.style.transition = 'transform 0.1s ease';
        });
    });
}

/**
 * Efecto parallax suave con movimiento del mouse
 * @param {string} selector - elementos a mover
 * @param {number} strength - intensidad (0.01 – 0.05 recomendado)
 */
export function initParallax(selector = '.parallax-layer', strength = 0.02) {
    const layers = document.querySelectorAll(selector);
    if (!layers.length) return;

    document.addEventListener('mousemove', throttle((e) => {
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        const offsetX = (e.clientX - centerX) * strength;
        const offsetY = (e.clientY - centerY) * strength;

        layers.forEach(layer => {
            const depth = parseFloat(layer.dataset.depth || '1');
            layer.style.transform = `translate(${offsetX * depth}px, ${offsetY * depth}px)`;
        });
    }, 16)); // ~60fps
}

// -------------------------------------------------------
// 4. Animación de aparición de notificación
// -------------------------------------------------------

/**
 * Pulsa un elemento para indicar actualización de datos
 * @param {HTMLElement} el
 */
export function pulseElement(el) {
    el.classList.remove('pulse-update');
    void el.offsetWidth; // reflow
    el.classList.add('pulse-update');
    el.addEventListener('animationend', () => {
        el.classList.remove('pulse-update');
    }, { once: true });
}

// -------------------------------------------------------
// Helpers internos
// -------------------------------------------------------

function throttle(fn, limit) {
    let inThrottle = false;
    return (...args) => {
        if (!inThrottle) {
            fn(...args);
            inThrottle = true;
            setTimeout(() => (inThrottle = false), limit);
        }
    };
}