
export class Carousel {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!this.container) {
            console.warn('[Carousel] Contenedor no encontrado');
            return;
        }

        this.options = {
            autoplay: true,
            autoplayDelay: 4000,
            transitionDuration: 400,
            loop: true,
            ...options
        };

        this.currentIndex = 0;
        this.isDragging = false;
        this.startX = 0;
        this.autoplayTimer = null;
        this.isAnimating = false;

        this._init();
    }

    _init() {
        this.track = this.container.querySelector('.carousel-track');
        this.slides = Array.from(this.container.querySelectorAll('.carousel-slide'));

        if (!this.track || this.slides.length === 0) {
            console.warn('[Carousel] No se encontraron slides');
            return;
        }

        this.total = this.slides.length;
        this._buildControls();
        this._buildIndicators();
        this._goTo(0, false);
        this._bindEvents();

        if (this.options.autoplay) {
            this._startAutoplay();
        }
    }

    _buildControls() {
        const prev = document.createElement('button');
        prev.className = 'carousel-btn carousel-prev';
        prev.innerHTML = '&#8249;';
        prev.setAttribute('aria-label', 'Anterior');

        const next = document.createElement('button');
        next.className = 'carousel-btn carousel-next';
        next.innerHTML = '&#8250;';
        next.setAttribute('aria-label', 'Siguiente');

        this.container.appendChild(prev);
        this.container.appendChild(next);

        prev.addEventListener('click', () => {
            this._stopAutoplay();
            this.prev();
            if (this.options.autoplay) this._startAutoplay();
        });

        next.addEventListener('click', () => {
            this._stopAutoplay();
            this.next();
            if (this.options.autoplay) this._startAutoplay();
        });
    }

    _buildIndicators() {
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'carousel-indicators';

        this.dots = this.slides.map((_, i) => {
            const dot = document.createElement('button');
            dot.className = 'carousel-dot';
            dot.setAttribute('aria-label', `Ir a slide ${i + 1}`);
            dot.addEventListener('click', () => {
                this._stopAutoplay();
                this._goTo(i);
                if (this.options.autoplay) this._startAutoplay();
            });
            dotsContainer.appendChild(dot);
            return dot;
        });

        this.container.appendChild(dotsContainer);
    }

    next() {
        if (this.isAnimating) return;
        const nextIndex = this.options.loop
            ? (this.currentIndex + 1) % this.total
            : Math.min(this.currentIndex + 1, this.total - 1);
        this._goTo(nextIndex);
    }

    prev() {
        if (this.isAnimating) return;
        const prevIndex = this.options.loop
            ? (this.currentIndex - 1 + this.total) % this.total
            : Math.max(this.currentIndex - 1, 0);
        this._goTo(prevIndex);
    }

    _goTo(index, animate = true) {
        if (index < 0 || index >= this.total) return;
        this.isAnimating = animate;

        const offset = -index * 100;
        this.track.style.transition = animate
            ? `transform ${this.options.transitionDuration}ms ease`
            : 'none';
        this.track.style.transform = `translateX(${offset}%)`;

        this.currentIndex = index;
        this._updateIndicators();

        if (animate) {
            setTimeout(() => { this.isAnimating = false; }, this.options.transitionDuration);
        }
    }

    _updateIndicators() {
        this.dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === this.currentIndex);
            dot.setAttribute('aria-current', i === this.currentIndex ? 'true' : 'false');
        });
    }

    _startAutoplay() {
        this._stopAutoplay();
        this.autoplayTimer = setInterval(() => this.next(), this.options.autoplayDelay);
    }

    _stopAutoplay() {
        if (this.autoplayTimer) {
            clearInterval(this.autoplayTimer);
            this.autoplayTimer = null;
        }
    }

    _bindEvents() {
        this.container.addEventListener('touchstart', (e) => {
            this.startX = e.touches[0].clientX;
            this.isDragging = true;
            this._stopAutoplay();
        }, { passive: true });

        this.container.addEventListener('touchmove', (e) => {
            if (!this.isDragging) return;
            const diff = this.startX - e.touches[0].clientX;
            if (Math.abs(diff) > 50) {
                this.isDragging = false;
                diff > 0 ? this.next() : this.prev();
                if (this.options.autoplay) this._startAutoplay();
            }
        }, { passive: true });

        this.container.addEventListener('touchend', () => {
            this.isDragging = false;
            if (this.options.autoplay) this._startAutoplay();
        });

        this.container.addEventListener('mousedown', (e) => {
            this.startX = e.clientX;
            this.isDragging = true;
            this._stopAutoplay();
        });

        document.addEventListener('mouseup', (e) => {
            if (!this.isDragging) return;
            this.isDragging = false;
            const diff = this.startX - e.clientX;
            if (Math.abs(diff) > 60) {
                diff > 0 ? this.next() : this.prev();
            }
            if (this.options.autoplay) this._startAutoplay();
        });

        this.container.addEventListener('mouseenter', () => this._stopAutoplay());
        this.container.addEventListener('mouseleave', () => {
            if (this.options.autoplay) this._startAutoplay();
        });

        this.container.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight') this.next();
            if (e.key === 'ArrowLeft') this.prev();
        });
    }

    destroy() {
        this._stopAutoplay();
        this.container.querySelectorAll('.carousel-btn, .carousel-indicators')
            .forEach(el => el.remove());
    }
}