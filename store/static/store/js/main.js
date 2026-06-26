// ===== MOBILE MENU =====
function toggleMenu() {
  const nav = document.getElementById('mobileNav');
  nav.classList.toggle('open');
}

// Close mobile menu when clicking outside
document.addEventListener('click', function (e) {
  const nav = document.getElementById('mobileNav');
  const btn = document.querySelector('.mobile-menu-btn');
  if (nav && btn && !nav.contains(e.target) && !btn.contains(e.target)) {
    nav.classList.remove('open');
  }
});

// ===== AUTO CLOSE ALERTS =====
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.5s';
      setTimeout(function () {
        alert.remove();
      }, 500);
    }, 4000);
  });
});

// ===== ACTIVE NAV LINK =====
document.addEventListener('DOMContentLoaded', function () {
  const links = document.querySelectorAll('.nav-links a');
  links.forEach(function (link) {
    if (link.href === window.location.href) {
      link.style.color = '#2563eb';
    }
  });
});