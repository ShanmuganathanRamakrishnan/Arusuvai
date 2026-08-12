// web/kolam.js — the woven pulli-and-line kolam background.
//
// Extracted 2026-08-12 (D14) from two byte-for-byte-identical copies that had
// drifted into onboarding.js and dashboard.js (dashboard.js's own header
// called this "duplicated per-page rather than shared (see web/app.js)").
// app.js's version is NOT a third copy of this one -- it factors the pattern
// through a separate buildKolam() and is a documented, deliberate per-page
// variation (see app.js), so it is left as-is; this module only unifies the
// two copies that were actually identical.
//
// Same pattern as ArusuvaiAuth (auth.js) and ArusuvaiHeader (header.js):
// a plain script include, no build step, one global namespace.

(() => {
  "use strict";

  function render() {
    const host = document.getElementById("kolam");
    if (!host) return;
    const W = 1200, H = 1400, g = 128, amp = g * 0.44, per = g * 2;
    const f = (n) => Math.round(n * 100) / 100;
    let dotStr = "";
    let lineStr = "";
    for (let r = 0; r * g <= H + g; r++) {
      const y0 = r * g, ph = r % 2 ? Math.PI : 0;
      let d = "";
      for (let x = 0; x <= W; x += 14) {
        const y = y0 + amp * Math.sin((x / per) * 2 * Math.PI + ph);
        d += (x === 0 ? "M" : "L") + f(x) + " " + f(y) + " ";
      }
      lineStr += `<path d="${d.trim()}" fill="none" stroke="#3A5A40" stroke-width="1.4"></path>`;
    }
    for (let c = 0; c * g <= W + g; c++) {
      const x0 = c * g, ph = c % 2 ? Math.PI : 0;
      let d = "";
      for (let y = 0; y <= H; y += 14) {
        const x = x0 + amp * Math.sin((y / per) * 2 * Math.PI + ph);
        d += (y === 0 ? "M" : "L") + f(x) + " " + f(y) + " ";
      }
      lineStr += `<path d="${d.trim()}" fill="none" stroke="#3A5A40" stroke-width="1.4"></path>`;
    }
    for (let r = 0; r * g <= H + g; r++) {
      for (let c = 0; c * g <= W + g; c++) {
        dotStr += `<circle cx="${c * g - g / 2}" cy="${r * g - g / 2}" r="4.4" fill="#B98416"></circle>`;
      }
    }
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 1200 1400");
    svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
    svg.innerHTML = dotStr + lineStr;
    host.appendChild(svg);
  }

  const ArusuvaiKolam = { render };

  window.ArusuvaiKolam = ArusuvaiKolam;
})();
