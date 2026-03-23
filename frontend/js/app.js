/** 
 * SOFZENIX HACKFEST — Global Interactions
 * Handles: Scroll Animations, Sticky Navbar, Mobile Menu
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Scroll-Triggered Animations (Reveal on Scroll)
    const observerOptions = { threshold: 0.1 };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

    // 2. Navbar Scrolled State
    const nav = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 20) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    });

    // 3. Smooth Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
                // If mobile nav is open, close it
                if (document.getElementById('mobileNav')?.classList.contains('active')) {
                    toggleMobileNav();
                }
            }
        });
    });
});

// 4. Global Mobile Nav Logic
window.toggleMobileNav = function() {
    const mobileNav = document.getElementById('mobileNav');
    const overlay = document.getElementById('overlay');
    if (mobileNav) mobileNav.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
}

// 5. Global Toast System
window.showToast = function(msg, type = 'info') {
    let t = document.getElementById('toast');
    if (!t) {
        t = document.createElement('div');
        t.id = 'toast';
        document.body.appendChild(t);
    }
    t.textContent = msg;
    t.className = `show ${type}`;
    setTimeout(() => { t.className = ''; }, 3500);
}
