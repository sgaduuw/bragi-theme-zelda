/* bragi-theme-zelda cosplay.js
 *
 * Pure flavour JS. Four features will live in this file by v0.1.0:
 *   - Theme toggle persistence (this task)
 *   - Rupee counter (Task 16)
 *   - PUSH START splash (Task 17)
 *   - Item-acquired flourish (Task 18)
 *
 * Vanilla, no framework. Target: <3 KB gzipped at the end of Task 18.
 * Loaded with `defer` so it never blocks first paint. Every feature is
 * absent (not broken) under no-JS.
 */

(function () {
  "use strict";

  // ===== Theme toggle =====

  function applyTheme(theme) {
    if (theme === "la-green" || theme === "gb-pocket") {
      document.documentElement.setAttribute("data-theme", theme);
      try { localStorage.setItem("zelda-theme", theme); } catch (e) {}
    } else {
      document.documentElement.removeAttribute("data-theme");
      try { localStorage.removeItem("zelda-theme"); } catch (e) {}
    }
  }

  function currentTheme() {
    try { return localStorage.getItem("zelda-theme") || ""; } catch (e) { return ""; }
  }

  function nextTheme(t) {
    // Cycle: auto -> la-green -> gb-pocket -> auto.
    if (t === "" || t === null) return "la-green";
    if (t === "la-green") return "gb-pocket";
    return "";
  }

  function initThemeToggle() {
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;
    btn.addEventListener("click", function () {
      applyTheme(nextTheme(currentTheme()));
    });
  }

  // ===== Rupee counter =====

  function readRupees() {
    try { return parseInt(localStorage.getItem("zelda-rupees") || "0", 10); }
    catch (e) { return 0; }
  }
  function writeRupees(n) {
    try { localStorage.setItem("zelda-rupees", String(n)); } catch (e) {}
  }
  function renderRupees(n) {
    var span = document.querySelector(".rupee-counter .count");
    if (span) span.textContent = String(n);
  }

  function awardRupeesForPage() {
    // Award once per page-load, capped per page.
    var key = "zelda-rupees-seen-" + location.pathname;
    try { if (sessionStorage.getItem(key)) return; } catch (e) {}

    var article = document.querySelector("main article, main");
    if (!article) return;
    // ~100 chars = 1 rupee, cheap heuristic, no NLP.
    var award = Math.max(1, Math.floor(article.textContent.length / 100 / 5));
    award = Math.min(award, 50);  // cap so one mega-page doesn't dominate.
    var n = readRupees() + award;
    writeRupees(n);
    renderRupees(n);
    try { sessionStorage.setItem(key, "1"); } catch (e) {}
  }

  function initRupeeCounter() {
    var btn = document.querySelector(".rupee-counter");
    if (!btn) return;
    renderRupees(readRupees());
    awardRupeesForPage();
    btn.addEventListener("click", function () {
      if (confirm("Reset rupee counter to 0?")) {
        writeRupees(0);
        renderRupees(0);
      }
    });
  }

  // ===== PUSH START splash =====

  function shouldShowSplash() {
    try { return !sessionStorage.getItem("zelda-splash-seen"); }
    catch (e) { return false; }
  }
  function markSplashSeen() {
    try { sessionStorage.setItem("zelda-splash-seen", "1"); } catch (e) {}
  }

  function showSplash() {
    var splash = document.createElement("div");
    splash.className = "push-start-splash";
    splash.setAttribute("role", "dialog");
    splash.setAttribute("aria-labelledby", "splash-title");
    splash.innerHTML =
      '<div class="push-start-splash__inner">' +
      '<h2 id="splash-title" class="push-start-splash__brand">ZELDA.NL</h2>' +
      '<p class="push-start-splash__cta">PUSH START</p>' +
      '<button class="push-start-splash__skip" type="button">Skip</button>' +
      '</div>';
    document.body.appendChild(splash);

    var skip = splash.querySelector(".push-start-splash__skip");
    skip.focus();

    function dismiss() {
      splash.classList.add("is-dismissed");
      window.setTimeout(function () { splash.remove(); }, 350);
      markSplashSeen();
      document.removeEventListener("keydown", onKey, true);
    }
    function onKey(e) {
      if (e.key === "Escape" || e.key === "Enter" || e.key === " ") dismiss();
    }
    splash.addEventListener("click", dismiss);
    document.addEventListener("keydown", onKey, true);
  }

  function initSplash() {
    if (!shouldShowSplash()) return;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", showSplash);
    } else {
      showSplash();
    }
  }

  // ===== Item-acquired flourish =====

  // Maps html[data-section] -> {sprite, label}. New section = add a row.
  var ITEM_FOR_SECTION = {
    "la":  { sprite: "la_pearl",        label: "LINK'S AWAKENING GUIDE" },
    "oot": { sprite: "kokiri_emerald",  label: "OCARINA OF TIME GUIDE" }
  };

  function maybeShowItemAcquired() {
    var section = document.documentElement.getAttribute("data-section");
    if (!section) return;
    var item = ITEM_FOR_SECTION[section];
    if (!item) return;
    var key = "zelda-acquired-" + section;
    try {
      if (sessionStorage.getItem(key)) return;
      sessionStorage.setItem(key, "1");
    } catch (e) { return; }

    var flourish = document.createElement("div");
    flourish.className = "item-acquired";
    flourish.setAttribute("role", "dialog");
    flourish.setAttribute("aria-label", "You got the " + item.label + "!");
    flourish.innerHTML =
      '<div class="item-acquired__inner">' +
      '<img class="item-acquired__sprite" src="/theme/zelda/static/sprites/items/' + item.sprite + '.png" alt="">' +
      '<p class="item-acquired__text">You got the<br><strong>' + item.label + '</strong>!</p>' +
      '<button class="item-acquired__dismiss" type="button">OK</button>' +
      '</div>';
    document.body.appendChild(flourish);

    var btn = flourish.querySelector(".item-acquired__dismiss");
    btn.focus();
    function dismiss() {
      flourish.classList.add("is-dismissed");
      window.setTimeout(function () { flourish.remove(); }, 350);
      document.removeEventListener("keydown", onKey, true);
    }
    function onKey(e) {
      if (e.key === "Escape" || e.key === "Enter" || e.key === " ") dismiss();
    }
    btn.addEventListener("click", dismiss);
    document.addEventListener("keydown", onKey, true);
  }

  // ===== Init =====

  function init() {
    initThemeToggle();
    initRupeeCounter();
    initSplash();
    maybeShowItemAcquired();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
