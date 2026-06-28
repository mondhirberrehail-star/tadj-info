/* ═══════════════════════════════════════════════════════════════
   TADJ-INFO — Main JavaScript
   ═══════════════════════════════════════════════════════════════ */

'use strict';

/* ── Language toggle ────────────────────────────────────────── */
const html = document.documentElement;
const langToggle = document.getElementById('lang-toggle');
let currentLang = localStorage.getItem('tadj_lang') || 'ar';

function applyLang(lang) {
  currentLang = lang;
  html.setAttribute('data-lang', lang);
  html.setAttribute('lang', lang);
  html.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
  localStorage.setItem('tadj_lang', lang);

  // Swap aria-label on elements with data-ar-label / data-fr-label
  document.querySelectorAll('[data-ar-label][data-fr-label]').forEach(el => {
    el.setAttribute('aria-label', lang === 'ar' ? el.dataset.arLabel : el.dataset.frLabel);
  });

  // Swap all [data-ar] / [data-fr] text content
  document.querySelectorAll('[data-ar][data-fr]').forEach(el => {
    const txt = lang === 'ar' ? el.dataset.ar : el.dataset.fr;
    if (el.tagName === 'INPUT' || el.tagName === 'OPTION') {
      el.placeholder = txt;
    } else {
      el.textContent = txt;
    }
  });

  // Swap select placeholder option
  document.querySelectorAll('option[data-ar][data-fr]').forEach(opt => {
    opt.textContent = lang === 'ar' ? opt.dataset.ar : opt.dataset.fr;
  });
}

if (langToggle) {
  langToggle.addEventListener('click', () => {
    applyLang(currentLang === 'ar' ? 'fr' : 'ar');
  });
}
// Apply on load
applyLang(currentLang);


/* ── Navbar: scroll class + active link ─────────────────────── */
const navbar = document.getElementById('navbar');

function updateNavbar() {
  if (!navbar) return;
  navbar.classList.toggle('scrolled', window.scrollY > 20);

  // Highlight active nav link based on scroll position
  const sections = document.querySelectorAll('section[id]');
  let current = '';
  sections.forEach(sec => {
    if (window.scrollY >= sec.offsetTop - 100) current = sec.id;
  });
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === `#${current}`);
  });
}
window.addEventListener('scroll', updateNavbar, { passive: true });
updateNavbar();


/* ── Mobile hamburger ───────────────────────────────────────── */
const hamburger  = document.getElementById('hamburger');
const navLinks   = document.getElementById('nav-links');

if (hamburger && navLinks) {
  hamburger.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    hamburger.classList.toggle('open', open);
    hamburger.setAttribute('aria-expanded', open);
    hamburger.setAttribute('aria-label', open ? 'إغلاق القائمة' : 'فتح القائمة');
  });

  // Close on link click
  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      navLinks.classList.remove('open');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
    });
  });
}


/* ── Product filter ─────────────────────────────────────────── */
const filterBtns  = document.querySelectorAll('.filter-btn');
const productCards = document.querySelectorAll('.product-card');

filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('filter-btn--active'));
    btn.classList.add('filter-btn--active');
    const cat = btn.dataset.category;

    productCards.forEach(card => {
      const match = cat === 'all' || card.dataset.category === cat;
      card.classList.toggle('hidden', !match);
      // Re-trigger AOS for newly shown cards
      if (match && !card.classList.contains('aos-visible')) {
        requestAnimationFrame(() => card.classList.add('aos-visible'));
      }
    });
  });
});


/* ── "Order now" card links pre-fill form ───────────────────── */
document.querySelectorAll('.product-card__order').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const productName = currentLang === 'ar'
      ? link.dataset.productAr
      : link.dataset.productFr;

    const select = document.getElementById('product');
    if (select) {
      // Find matching option (by Arabic name, always stored as value)
      const arName = link.dataset.productAr;
      const opt = [...select.options].find(o => o.value === arName);
      if (opt) { select.value = arName; }
    }
    document.getElementById('order')?.scrollIntoView({ behavior: 'smooth' });
  });
});


/* ── Order form submission ──────────────────────────────────── */
const orderForm   = document.getElementById('order-form');
const submitBtn   = document.getElementById('submit-btn');
const formFeedback = document.getElementById('form-feedback');

function showFieldError(fieldId, errorId, message) {
  const field = document.getElementById(fieldId);
  const errEl  = document.getElementById(errorId);
  if (field)  field.classList.add('error');
  if (errEl)  { errEl.textContent = message; errEl.classList.add('visible'); }
}
function clearErrors() {
  document.querySelectorAll('.form-input, .form-select').forEach(el => el.classList.remove('error'));
  document.querySelectorAll('.form-error').forEach(el => { el.textContent = ''; el.classList.remove('visible'); });
  if (formFeedback) { formFeedback.hidden = true; formFeedback.className = 'form-feedback'; }
}

if (orderForm) {
  orderForm.addEventListener('submit', async e => {
    e.preventDefault();
    clearErrors();

    const data = {
      customer_name : orderForm.querySelector('[name=customer_name]').value.trim(),
      phone         : orderForm.querySelector('[name=phone]').value.trim(),
      address       : orderForm.querySelector('[name=address]').value.trim(),
      product       : orderForm.querySelector('[name=product]').value,
      order_type    : orderForm.querySelector('[name=order_type]:checked')?.value || '',
      note          : orderForm.querySelector('[name=note]').value.trim(),
    };

    // Client-side validation
    let hasError = false;
    if (!data.customer_name) {
      showFieldError('customer_name', 'error-name', 'الاسم واللقب مطلوب');
      hasError = true;
    }
    if (!data.phone) {
      showFieldError('phone', 'error-phone', 'رقم الهاتف مطلوب');
      hasError = true;
    }
    if (!data.product) {
      showFieldError('product', 'error-product', 'يرجى اختيار منتج أو خدمة');
      hasError = true;
    }
    if (hasError) return;

    // Loading state
    const btnText    = submitBtn.querySelector('.submit-btn__text');
    const btnLoading = submitBtn.querySelector('.submit-btn__loading');
    submitBtn.disabled = true;
    if (btnText)    btnText.hidden    = true;
    if (btnLoading) btnLoading.hidden = false;

    try {
      const res  = await fetch('/api/orders', {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify(data),
      });
      const json = await res.json();

      if (json.success) {
        formFeedback.className  = 'form-feedback form-feedback--success';
        formFeedback.textContent = currentLang === 'ar'
          ? `✓ تم إرسال طلبك بنجاح! سنتواصل معك قريباً على ${data.phone}`
          : `✓ Demande envoyée ! Nous vous contacterons bientôt au ${data.phone}`;
        formFeedback.hidden = false;
        orderForm.reset();
      } else {
        const msgs = json.errors?.join(' — ') || 'حدث خطأ، حاول مجدداً';
        formFeedback.className  = 'form-feedback form-feedback--error';
        formFeedback.textContent = msgs;
        formFeedback.hidden = false;
      }
    } catch {
      formFeedback.className  = 'form-feedback form-feedback--error';
      formFeedback.textContent = currentLang === 'ar'
        ? 'خطأ في الاتصال، تأكد من اتصالك بالإنترنت وأعد المحاولة'
        : 'Erreur réseau, vérifiez votre connexion et réessayez';
      formFeedback.hidden = false;
    } finally {
      submitBtn.disabled = false;
      if (btnText)    btnText.hidden    = false;
      if (btnLoading) btnLoading.hidden = true;
      formFeedback.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });
}


/* ── AOS (Animate On Scroll) — minimal, no library ─────────── */
const aosObserver = new IntersectionObserver(
  entries => entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('aos-visible');
      aosObserver.unobserve(entry.target);
    }
  }),
  { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
);

document.querySelectorAll('[data-aos]').forEach((el, i) => {
  el.style.transitionDelay = `${i % 6 * 80}ms`;
  aosObserver.observe(el);
});


/* ── PWA Service Worker registration ────────────────────────── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}
