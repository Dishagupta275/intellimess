// ── IntelliMess shared JS ──────────────────────────────────────

// Hamburger nav toggle (mobile)
function toggleNav() {
    const nav  = document.getElementById('navLinks');
    const btn  = document.getElementById('hamburger');
    if (!nav) return;
    const open = nav.classList.toggle('open');
    if (btn) btn.classList.toggle('open', open);
}

// Close nav when clicking outside
document.addEventListener('click', function(e) {
    const nav = document.getElementById('navLinks');
    const btn = document.getElementById('hamburger');
    if (!nav || !btn) return;
    if (!nav.contains(e.target) && !btn.contains(e.target)) {
        nav.classList.remove('open');
        btn.classList.remove('open');
    }
});

// Close nav when a nav link is tapped (mobile UX)
document.addEventListener('DOMContentLoaded', function() {
    const nav = document.getElementById('navLinks');
    if (!nav) return;
    nav.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => {
            nav.classList.remove('open');
            const btn = document.getElementById('hamburger');
            if (btn) btn.classList.remove('open');
        });
    });
});
