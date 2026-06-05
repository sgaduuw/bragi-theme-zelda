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

  // ===== Init =====

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initThemeToggle);
  } else {
    initThemeToggle();
  }
})();
