// C Syntax Checker - Documentation Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle for mobile
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('open');
            }
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('open');
        });
    }

    // Section toggle for sidebar
    const sectionTitles = document.querySelectorAll('.sidebar-section-title');
    sectionTitles.forEach(function(title) {
        title.addEventListener('click', function() {
            const section = this.closest('.sidebar-section');
            section.classList.toggle('collapsed');
        });
    });

    // Sidebar item click handlers
    const sidebarItems = document.querySelectorAll('.sidebar-item');
    sidebarItems.forEach(function(item) {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);

            if (target) {
                // Close sidebar on mobile
                sidebar.classList.remove('open');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove('open');
                }

                // Smooth scroll to target
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });

                // Update active state
                sidebarItems.forEach(function(i) {
                    i.classList.remove('active');
                });
                this.classList.add('active');

                // Update URL hash without jumping
                history.pushState(null, '', '#' + targetId);
            }
        });
    });

    // Handle hash on page load
    if (window.location.hash) {
        const targetId = window.location.hash.substring(1);
        const target = document.getElementById(targetId);
        if (target) {
            setTimeout(function() {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    }

    // Copy code buttons
    const copyButtons = document.querySelectorAll('.copy-code-btn');
    copyButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const pre = this.closest('.code-block-wrapper').querySelector('pre');
            const code = pre.textContent;

            navigator.clipboard.writeText(code).then(function() {
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.background = '#4ec9b0';
                btn.style.color = '#0b0f12';

                setTimeout(function() {
                    btn.textContent = originalText;
                    btn.style.background = '#2d333b';
                    btn.style.color = '#8892a0';
                }, 2000);
            }).catch(function() {
                btn.textContent = 'Failed';
                setTimeout(function() {
                    btn.textContent = 'Copy';
                }, 2000);
            });
        });
    });

    // Highlight active section based on scroll
    const sections = document.querySelectorAll('.docs-content h2[id]');
    const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -60% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                sidebarItems.forEach(function(item) {
                    item.classList.remove('active');
                    if (item.getAttribute('href') === '#' + id) {
                        item.classList.add('active');
                    }
                });
            }
        });
    }, observerOptions);

    sections.forEach(function(section) {
        observer.observe(section);
    });

    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    const nav = document.querySelector('.nav');

    if (menuToggle && nav) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('open');
        });

        // Close nav when clicking a link
        nav.querySelectorAll('.nav-link').forEach(function(link) {
            link.addEventListener('click', function() {
                nav.classList.remove('open');
            });
        });
    }

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        // Focus search on Ctrl+K (if search is implemented)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            // Could implement search focus here
        }

        // Escape to close sidebar on mobile
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.remove('open');
            }
        }
    });

    // Add fade-in animation to sections on scroll
    const contentSections = document.querySelectorAll('.docs-content h2, .docs-content h3');
    const fadeObserverOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const fadeObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-section');
            }
        });
    }, fadeObserverOptions);

    contentSections.forEach(function(section) {
        fadeObserver.observe(section);
    });
});

// Handle browser back/forward
window.addEventListener('popstate', function() {
    if (window.location.hash) {
        const targetId = window.location.hash.substring(1);
        const target = document.getElementById(targetId);
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
});