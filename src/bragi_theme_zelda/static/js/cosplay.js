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

  // ===== Init =====

  function init() {
    initThemeToggle();
    initRupeeCounter();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
