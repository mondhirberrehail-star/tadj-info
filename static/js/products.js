/**
 * products.js — bilingual product cards from Google Sheets CSV
 * CSV columns: name_fr, name_ar, category_fr, category_ar,
 *              price, image_url, image_url2, image_url3, available
 * Integrates with main.js applyLang(): all [data-ar][data-fr] elements
 * are updated automatically when the user switches FR ↔ AR.
 */

const CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTGTx5O-3s4k4UkY68v1KDvVknkKnf0wLlUJmVUdzUoSDdW0zh-64jJ_t2ndOoV-23ilPJDarWJyaU0/pub?gid=0&single=true&output=csv";
const WA_NUMBER = "213550249981";

const filtersEl = document.getElementById("products-filters");
const gridEl    = document.getElementById("products-grid");
const loadingEl = document.getElementById("products-loading");
const errorEl   = document.getElementById("products-error");

/* ── RFC-4180 CSV parser: handles quoted multi-line fields ── */
function parseCSV(text) {
  const rows = [];
  let cur = "", inQ = false, fields = [], i = 0;
  const push = () => { fields.push(cur); cur = ""; };
  while (i < text.length) {
    const ch = text[i];
    if (inQ) {
      if (ch === '"' && text[i + 1] === '"') { cur += '"'; i += 2; continue; }
      if (ch === '"') { inQ = false; i++; continue; }
      cur += ch;
    } else {
      if (ch === '"') { inQ = true; i++; continue; }
      if (ch === ',') { push(); i++; continue; }
      if (ch === '\n' || (ch === '\r' && text[i + 1] === '\n')) {
        push(); rows.push(fields); fields = [];
        i += ch === '\r' ? 2 : 1; continue;
      }
      cur += ch;
    }
    i++;
  }
  push();
  if (fields.length) rows.push(fields);
  const headers = rows[0].map(h => h.trim().toLowerCase().replace(/\s+/g, "_"));
  return rows.slice(1)
    .filter(r => r.some(f => f.trim()))
    .map(r => Object.fromEntries(headers.map((h, j) => [h, (r[j] ?? "").trim()])));
}

/* ── Extract direct image URL from BBCode [img]url[/img] ── */
function extractUrl(raw) {
  if (!raw) return "";
  const m = raw.match(/\[img\](https?:\/\/[^\[]+)\[\/img\]/i);
  return (m ? m[1] : raw).trim();
}

/* ── Collect up to 3 valid image URLs ── */
function getImages(p) {
  return ["image_url", "image_url2", "image_url3"]
    .map(k => extractUrl(p[k] || ""))
    .filter(u => u !== "");
}

/* ── Active language from <html data-lang="..."> ── */
function getLang() {
  return document.documentElement.getAttribute("data-lang") || "ar";
}

/* ── Pick FR or AR value, fallback to the other if empty ── */
function pick(frVal, arVal) {
  const lang = getLang();
  return lang === "fr"
    ? (frVal || arVal || "").trim()
    : (arVal || frVal || "").trim();
}

/* ── Build WhatsApp href using the name in the current language ── */
function waHref(nameFr, nameAr) {
  const name = pick(nameFr, nameAr);
  return `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(`السلام عليكم، نحب نطلب: ${name}`)}`;
}

/* ── Category fallback SVG icon ── */
function categoryIcon() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6M9 12h6M9 15h4"/></svg>`;
}

/* ── Build carousel (multi-image) or single image or icon ── */
function buildMedia(images, altText) {
  if (images.length === 0) {
    const div = document.createElement("div");
    div.className = "product-card__icon";
    div.setAttribute("aria-hidden", "true");
    div.innerHTML = categoryIcon();
    return div;
  }

  if (images.length === 1) {
    const wrap = document.createElement("div");
    wrap.className = "product-card__img";
    const img = document.createElement("img");
    img.src = images[0]; img.alt = altText; img.loading = "lazy";
    img.addEventListener("error", () => {
      wrap.className = "product-card__icon";
      wrap.setAttribute("aria-hidden", "true");
      wrap.innerHTML = categoryIcon();
    });
    wrap.appendChild(img);
    return wrap;
  }

  // Multiple images → carousel
  const carousel = document.createElement("div");
  carousel.className = "product-card__carousel";
  const track = document.createElement("div");
  track.className = "carousel__track";
  let current = 0;

  images.forEach((url, idx) => {
    const slide = document.createElement("div");
    slide.className = "carousel__slide" + (idx === 0 ? " carousel__slide--active" : "");
    const img = document.createElement("img");
    img.src = url; img.alt = `${altText} ${idx + 1}`; img.loading = idx === 0 ? "eager" : "lazy";
    img.addEventListener("error", () => slide.remove());
    slide.appendChild(img);
    track.appendChild(slide);
  });
  carousel.appendChild(track);

  const prev = document.createElement("button");
  prev.className = "carousel__btn carousel__btn--prev";
  prev.setAttribute("data-ar", "السابق"); prev.setAttribute("data-fr", "Précédent");
  prev.setAttribute("aria-label", getLang() === "fr" ? "Précédent" : "السابق");
  prev.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>`;

  const next = document.createElement("button");
  next.className = "carousel__btn carousel__btn--next";
  next.setAttribute("data-ar", "التالي"); next.setAttribute("data-fr", "Suivant");
  next.setAttribute("aria-label", getLang() === "fr" ? "Suivant" : "التالي");
  next.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>`;

  const dots = document.createElement("div");
  dots.className = "carousel__dots";
  images.forEach((_, idx) => {
    const dot = document.createElement("span");
    dot.className = "carousel__dot" + (idx === 0 ? " carousel__dot--active" : "");
    dots.appendChild(dot);
  });

  function goTo(n) {
    const slides = track.querySelectorAll(".carousel__slide");
    const dotEls = dots.querySelectorAll(".carousel__dot");
    if (!slides.length) return;
    current = (n + slides.length) % slides.length;
    slides.forEach((s, i) => s.classList.toggle("carousel__slide--active", i === current));
    dotEls.forEach((d, i) => d.classList.toggle("carousel__dot--active", i === current));
  }

  prev.addEventListener("click", e => { e.stopPropagation(); goTo(current - 1); });
  next.addEventListener("click", e => { e.stopPropagation(); goTo(current + 1); });

  let touchStartX = 0;
  carousel.addEventListener("touchstart", e => { touchStartX = e.touches[0].clientX; }, { passive: true });
  carousel.addEventListener("touchend", e => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 40) goTo(dx < 0 ? current + 1 : current - 1);
  }, { passive: true });

  carousel.appendChild(prev);
  carousel.appendChild(next);
  carousel.appendChild(dots);
  return carousel;
}

/* ── Render one product card ── */
function renderCard(p) {
  const nameFr   = (p.name_fr     || p.name_ar     || "").trim();
  const nameAr   = (p.name_ar     || p.name_fr     || "").trim();
  const catFr    = (p.category_fr || p.category_ar || "").trim();
  const catAr    = (p.category_ar || p.category_fr || "").trim();

  const lang        = getLang();
  const displayName = lang === "fr" ? (nameFr || nameAr) : (nameAr || nameFr);
  const displayCat  = lang === "fr" ? (catFr  || catAr)  : (catAr  || catFr);

  const priceNum  = p.price ? parseFloat(p.price.replace(/[^\d.]/g, "")) : NaN;
  const priceHtml = !isNaN(priceNum)
    ? `<p class="product-card__price">${priceNum.toLocaleString("fr-DZ")} دج</p>`
    : `<p class="product-card__price product-card__price--quote"
          data-ar="حسب التشخيص" data-fr="Sur devis">
          ${lang === "fr" ? "Sur devis" : "حسب التشخيص"}
       </p>`;

  const images = getImages(p);

  const card = document.createElement("div");
  card.className     = "product-card aos-visible";
  card.dataset.category = catFr || catAr; // stable key for filter
  card.dataset.nameFr   = nameFr;
  card.dataset.nameAr   = nameAr;

  card.innerHTML = `
    <span class="product-card__badge"
          data-ar="${catAr}" data-fr="${catFr}">${displayCat}</span>
    <div class="product-card__body">
      <h3 class="product-card__name"
          data-ar="${nameAr}" data-fr="${nameFr}">${displayName}</h3>
      ${priceHtml}
    </div>
    <a href="${waHref(nameFr, nameAr)}"
       class="product-card__order"
       target="_blank" rel="noopener"
       data-name-fr="${nameFr}" data-name-ar="${nameAr}">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"
           style="vertical-align:-3px;margin-inline-end:6px">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
      </svg>
      <span data-ar="اطلب عبر واتساب" data-fr="Commander via WhatsApp">
        ${lang === "fr" ? "Commander via WhatsApp" : "اطلب عبر واتساب"}
      </span>
    </a>`;

  card.insertBefore(buildMedia(images, displayName), card.querySelector(".product-card__body"));
  return card;
}

/* ── Build category filter tabs ── */
function buildFilters(products) {
  filtersEl.innerHTML = "";
  const lang = getLang();

  // Stable key = catFr (or catAr if no fr)
  const seen = new Map(); // catFr → catAr
  products.forEach(p => {
    const fr = (p.category_fr || p.category_ar || "").trim();
    const ar = (p.category_ar || p.category_fr || "").trim();
    if (fr && !seen.has(fr)) seen.set(fr, ar);
  });

  const allBtn = document.createElement("button");
  allBtn.className = "filter-btn filter-btn--active";
  allBtn.dataset.category = "all";
  allBtn.setAttribute("data-ar", "الكل");
  allBtn.setAttribute("data-fr", "Tout");
  allBtn.textContent = lang === "fr" ? "Tout" : "الكل";
  filtersEl.appendChild(allBtn);

  seen.forEach((arLabel, frKey) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.dataset.category = frKey;
    btn.setAttribute("data-ar", arLabel);
    btn.setAttribute("data-fr", frKey);
    btn.textContent = lang === "fr" ? frKey : arLabel;
    filtersEl.appendChild(btn);
  });

  filtersEl.addEventListener("click", e => {
    const btn = e.target.closest(".filter-btn");
    if (!btn) return;
    filtersEl.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("filter-btn--active"));
    btn.classList.add("filter-btn--active");
    const sel = btn.dataset.category;
    gridEl.querySelectorAll(".product-card").forEach(card => {
      card.classList.toggle("hidden", sel !== "all" && card.dataset.category !== sel);
    });
  });
}

/* ── Update WhatsApp hrefs when language changes ── */
function refreshWaLinks(lang) {
  gridEl.querySelectorAll(".product-card__order").forEach(a => {
    const name = lang === "fr" ? a.dataset.nameFr : a.dataset.nameAr;
    if (name) {
      a.href = `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(`السلام عليكم، نحب نطلب: ${name}`)}`;
    }
  });
}

/* ── Main loader ── */
async function loadProducts() {
  try {
    const res = await fetch(CSV_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rows = parseCSV(await res.text()).filter(r =>
      r.available?.toLowerCase() === "yes" &&
      (r.name_fr || r.name_ar || "").trim() !== ""
    );

    buildFilters(rows);
    rows.forEach(p => gridEl.appendChild(renderCard(p)));

    loadingEl.hidden = true;
    gridEl.hidden = false;

    // Watch for language changes → update WA links
    new MutationObserver(muts => {
      muts.forEach(m => {
        if (m.attributeName === "data-lang") {
          refreshWaLinks(document.documentElement.getAttribute("data-lang") || "ar");
        }
      });
    }).observe(document.documentElement, { attributes: true });

  } catch (err) {
    console.error("products.js:", err);
    loadingEl.hidden = true;
    errorEl.hidden = false;
  }
}

document.addEventListener("DOMContentLoaded", loadProducts);
