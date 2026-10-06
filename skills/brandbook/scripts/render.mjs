// SPDX-License-Identifier: CC-BY-4.0
// © 2026 Design House (https://designhouse.me)
//
// Renders and checks the brand book in a local Chromium. No npm packages: Chromium is driven over the
// DevTools Protocol on 127.0.0.1 through the WebSocket built into Node 22+. No internet connection.
//
//   node render.mjs check  brand/book/index.html [brand/labels]   # checks in the rendered page (see below)
//   node render.mjs pdf    brand/book/index.html brand/out/brandbook.pdf
//   node render.mjs shots  brand/book/index.html brand/out/shots  # book-1440.jpg, book-390.jpg, first screens
//   node render.mjs labels brand/labels brand/out/labels          # <id>.pdf at trim + bleed, <id>-preview.png, <id>-guides.png
//
// check, book (at 1440 and 390 px): horizontal scroll, images that didn't load, page errors, each brand font
// loaded and covering the language's letters (ą ć ę ł ń ó ś ź ż „ ” for Polish; the text is measured with two
// different fallbacks, equal widths mean no fallback glyph was used), logos in mockups smaller than their own
// min_px, generated images without the caption, text under 12 px (warning).
// check, labels: zone overflow in both axes, mandatory text ([data-legal]) x-height measured in the browser
// against 1.2 mm (0.9 mm when the largest surface is under 80 cm²) for food and supplements, fonts, images.
//
// Options: --chrome /path/to/chrome. Exit code: 0 = no errors, 1 = errors or a render error, 2 = bad input.

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const fail = (msg, code = 2) => {
  console.error(`ERROR: ${msg}`);
  process.exit(code);
};
if (typeof WebSocket === "undefined") fail(`Node 22 or newer is required (built-in WebSocket), found ${process.version}.`);
const argv = process.argv.slice(2);
const opt = (name) => { const i = argv.indexOf(`--${name}`); return i >= 0 ? argv.splice(i, 2)[1] : undefined; };
const chromeArg = opt("chrome");
const [mode, input, output] = argv;
if (!["check", "pdf", "shots", "labels"].includes(mode) || !input) fail("usage: node render.mjs check|pdf|shots|labels <input> [output]");

function findChrome() {
  if (chromeArg || process.env.CHROME) return chromeArg || process.env.CHROME;
  const fixed = [
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium",
  ];
  const found = fixed.find((p) => existsSync(p));
  if (found) return found;
  const cache = join(homedir(), ".cache/ms-playwright");
  const dirs = existsSync(cache) ? readdirSync(cache).filter((d) => /^chromium-\d+$/.test(d)).sort().reverse() : [];
  for (const d of dirs) for (const rel of ["chrome-linux64/chrome", "chrome-linux/chrome"]) if (existsSync(join(cache, d, rel))) return join(cache, d, rel);
  fail("could not find Chromium or Chrome. Give the path: --chrome /path/to/chromium");
}

// ------------------------------------------------------------------ Chromium over the DevTools Protocol
const within = (ms, p, what) => {
  let timer;
  const limit = new Promise((_, reject) => (timer = setTimeout(() => reject(new Error(`${what}: timed out after ${ms / 1000} s`)), ms)));
  return Promise.race([p, limit]).finally(() => clearTimeout(timer));
};
// Chromium's socket path in the profile is limited to ~100 characters; with a long TMPDIR the profile goes to /tmp.
const tmpBase = tmpdir().length > 40 && existsSync("/tmp") ? "/tmp" : tmpdir();
let browser;
process.on("exit", () => browser?.kill());
process.on("SIGINT", () => process.exit(130));

class Chrome {
  static async launch() {
    const profile = mkdtempSync(join(tmpBase, `brandbook-chrome-${process.pid}-`));
    const flags = [
      "--headless=new", "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1", `--user-data-dir=${profile}`,
      "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--disable-background-networking", "--mute-audio",
      "--hide-scrollbars", "--force-color-profile=srgb", "--allow-file-access-from-files",
      ...(process.getuid?.() === 0 ? ["--no-sandbox"] : []),
      "about:blank",
    ];
    const proc = spawn(findChrome(), flags, { stdio: ["ignore", "ignore", "pipe"], detached: true });
    const c = new Chrome(proc, profile);
    const ws = await new Promise((res, rej) => {
      let buf = "", found = false;
      proc.stderr.on("data", (d) => {
        if (found) return;
        buf += d;
        const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
        if (m) { found = true; res(m[1]); }
      });
      proc.on("exit", (code) => !found && rej(new Error(`Chromium exited before startup (code ${code}): ${buf.slice(-300)}`)));
      proc.on("error", rej);
    });
    await c.connect(ws);
    return c;
  }
  constructor(proc, profile) { this.proc = proc; this.profile = profile; this.seq = 0; this.pending = new Map(); this.listeners = new Set(); }
  connect(wsUrl) {
    return new Promise((res, rej) => {
      const ws = new WebSocket(wsUrl);
      ws.onopen = () => res();
      ws.onerror = () => rej(new Error("could not connect to DevTools"));
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve: ok, reject } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          msg.error ? reject(new Error(msg.error.message)) : ok(msg.result);
        } else if (msg.method) for (const l of this.listeners) l(msg);
      };
      this.ws = ws;
    });
  }
  send(method, params = {}, sessionId) {
    const id = ++this.seq;
    this.ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    return new Promise((ok, reject) => this.pending.set(id, { resolve: ok, reject }));
  }
  once(method, sessionId) {
    return new Promise((ok) => {
      const l = (msg) => { if (msg.method === method && msg.sessionId === sessionId) { this.listeners.delete(l); ok(msg.params); } };
      this.listeners.add(l);
    });
  }
  kill() {
    try { this.ws?.close(); } catch {}
    try { process.kill(-this.proc.pid, "SIGKILL"); } catch { try { this.proc.kill("SIGKILL"); } catch {} }
    rmSync(this.profile, { recursive: true, force: true });
  }
}

async function openPage(url, width, height, { mobile = false, scale = 1, media = "screen" } = {}) {
  const { targetId } = await browser.send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await browser.send("Target.attachToTarget", { targetId, flatten: true });
  const s = (m, p) => browser.send(m, p, sessionId);
  const problems = [];
  browser.listeners.add((msg) => {
    if (msg.sessionId !== sessionId) return;
    if (msg.method === "Runtime.exceptionThrown") problems.push(msg.params.exceptionDetails?.exception?.description ?? msg.params.exceptionDetails?.text);
    if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "error") problems.push(msg.params.args.map((a) => a.value ?? a.description).join(" "));
    if (msg.method === "Log.entryAdded" && msg.params.entry.level === "error") problems.push(`${msg.params.entry.text} ${msg.params.entry.url ?? ""}`.trim());
  });
  await s("Page.enable"); await s("Runtime.enable"); await s("Log.enable");
  await s("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: scale, mobile });
  await s("Emulation.setEmulatedMedia", { media });
  const loaded = browser.once("Page.loadEventFired", sessionId);
  await s("Page.navigate", { url });
  await within(30000, loaded, `loading ${url}`);
  const evaluate = async (expression) => {
    const r = await s("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
    return r.result.value;
  };
  return { s, evaluate, problems, close: () => browser.send("Target.closeTarget", { targetId }) };
}

// Lazy images and label iframes would stay empty in a PDF or a full-page shot: load them all first.
const LOAD_ALL = `(async () => {
  await (window.__bookReady || window.__labelReady || Promise.resolve());
  for (const el of document.querySelectorAll('[loading="lazy"]')) el.loading = "eager";
  const wait = (el) => new Promise((r) => { if (el.tagName === "IMG" && el.complete) return r(); el.addEventListener("load", r, { once: true }); el.addEventListener("error", r, { once: true }); setTimeout(r, 8000); });
  await Promise.all([...document.images, ...document.querySelectorAll("iframe")].map(wait));
  await document.fonts.ready;
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  return true;
})()`;

const errors = [], warnings = [];
const err = (m) => { errors.push(m); console.log(`ERROR: ${m}`); };
const warn = (m) => { warnings.push(m); console.log(`WARNING: ${m}`); };

// In-page probes. FONTS: brand families from the embedded JSON, loaded and covering the language's letters.
const FONT_PROBE = `(() => {
  const el = document.getElementById("brand-data") || document.getElementById("label-data");
  const d = JSON.parse(el.textContent);
  const fams = (d.type && d.type.families) || (d.brand && d.brand.families) || [];
  const lang = (d.meta && d.meta.language) || (d.brand && d.brand.language) || "pl";
  const letters = lang === "en" ? "AaGg“”’" : "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ„”";
  const ctx = document.createElement("canvas").getContext("2d");
  const out = [];
  for (const f of fams) {
    const loaded = [...document.fonts].some((ff) => ff.family.replace(/["']/g, "") === f.family && ff.status === "loaded");
    const missing = [];
    for (const ch of letters) {
      ctx.font = '40px "' + f.family + '", monospace'; const a = ctx.measureText(ch).width;
      ctx.font = '40px "' + f.family + '", serif'; const b = ctx.measureText(ch).width;
      if (Math.abs(a - b) > 0.01) missing.push(ch);
    }
    out.push({ family: f.family, loaded, missing: missing.join(" ") });
  }
  return out;
})()`;

const BOOK_PROBE = `(() => {
  const vw = document.documentElement.clientWidth;
  const wide = [];
  if (document.documentElement.scrollWidth > vw + 1)
    for (const el of document.querySelectorAll("main *")) {
      const r = el.getBoundingClientRect();
      if (r.right > vw + 1 && !el.closest(".scroll") && getComputedStyle(el).position !== "fixed") wide.push(el.tagName.toLowerCase() + (el.className ? "." + String(el.className).split(" ")[0] : "") + " " + Math.round(r.right - vw) + "px");
    }
  const broken = [...document.images].filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.getAttribute("src"));
  const logos = [...document.querySelectorAll("[data-logo]")].map((el) => {
    const s = Number(el.dataset.scale || 1), w = el.getBoundingClientRect().width / s;
    return { w: Math.round(w), min: Number(el.dataset.minPx), where: el.closest("figure,section")?.id || el.closest("figure")?.querySelector("figcaption")?.textContent || "" };
  }).filter((x) => x.min && x.w + 0.5 < x.min);
  const d = JSON.parse(document.getElementById("brand-data").textContent);
  const label = (d.imagery && d.imagery.ai && d.imagery.ai.label) || "";
  const uncaptioned = [...document.querySelectorAll('figure[data-generated="true"]')].filter((f) => {
    const t = (f.querySelector("figcaption") || {}).textContent || "";
    return !(label ? t.includes(label) : /wizualizacja|visuali[sz]ation/i.test(t));
  }).map((f) => f.querySelector("img")?.getAttribute("src"));
  let small = 0; const smallEx = [];
  const walker = document.createTreeWalker(document.getElementById("main"), NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode, p = n.parentElement;
    if (!n.textContent.trim() || !p || p.closest(".mock, iframe, .no-print") || !p.offsetParent) continue;
    const fs = parseFloat(getComputedStyle(p).fontSize);
    if (fs < 12) { small++; if (smallEx.length < 3) smallEx.push(n.textContent.trim().slice(0, 30) + " (" + fs + "px)"); }
  }
  return { wide: wide.slice(0, 6), broken, logos, uncaptioned, small, smallEx };
})()`;

const LABEL_PROBE = `(() => {
  const d = JSON.parse(document.getElementById("label-data").textContent);
  const L = d.label, f = L.format;
  const pxmm = 96 / 25.4;
  const over = [...document.querySelectorAll(".inner")].map((el) => ({
    zone: el.parentElement.dataset.zone,
    v: (el.scrollHeight - el.clientHeight) / pxmm, h: (el.scrollWidth - el.clientWidth) / pxmm
  })).filter((o) => o.v > 0.2 || o.h > 0.2);
  const ctx = document.createElement("canvas").getContext("2d");
  const xs = [...document.querySelectorAll("[data-legal]")].filter((el) => el.dataset.legal !== "info").map((el) => {
    const cs = getComputedStyle(el);
    ctx.font = cs.fontWeight + " " + cs.fontSize + " " + cs.fontFamily;
    const xh = ctx.measureText("x").actualBoundingBoxAscent / pxmm;
    return { key: el.dataset.legal, xh, pt: parseFloat(cs.fontSize) * 0.75 };
  });
  const broken = [...document.images].filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.getAttribute("src"));
  const rgb = (s) => (s.match(/[0-9.]+/g) || []).slice(0, 3).map(Number);
  const lin = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const lum = (s) => { const [r, g, b] = rgb(s); return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b); };
  const sheet = getComputedStyle(document.querySelector(".sheet"));
  const [la, lb] = [lum(sheet.color), lum(sheet.backgroundColor)].sort((a, b) => b - a);
  return { id: L.id, category: L.category, surface: f.largest_surface_cm2, over, xs, broken, contrast: (la + 0.05) / (lb + 0.05) };
})()`;

function fontReport(fonts, where) {
  for (const f of fonts) {
    if (!f.loaded) err(`${where}: the font "${f.family}" did not load (check the file path in type.families and @font-face)`);
    else if (f.missing) err(`${where}: "${f.family}" has no glyphs for: ${f.missing} (the text falls back to another font)`);
  }
}

async function checkBook(file) {
  const url = pathToFileURL(file).href;
  for (const [w, hgt, mobile] of [[1440, 900, false], [390, 844, true]]) {
    const p = await openPage(url, w, hgt, { mobile });
    await within(60000, p.evaluate(LOAD_ALL), "loading the book");
    const r = await p.evaluate(BOOK_PROBE);
    const where = `book at ${w} px`;
    if (r.wide.length) err(`${where}: the page scrolls sideways; too wide: ${r.wide.join(", ")}`);
    if (w === 1440) {
      fontReport(await p.evaluate(FONT_PROBE), "book");
      for (const b of r.broken) err(`book: image did not load: ${b}`);
      for (const l of r.logos) err(`book: a logo in "${l.where.trim().slice(0, 40)}" is ${l.w} px wide at full size, below its own minimum of ${l.min} px`);
      for (const u of r.uncaptioned) err(`book: generated image without the caption: ${u}`);
      if (r.small) warn(`book: ${r.small} text fragments under 12 px, e.g. ${r.smallEx.join("; ")}`);
      for (const pr of [...new Set(p.problems)]) err(`book: page error: ${pr}`);
    }
    await p.close();
  }
}

async function checkLabels(dir) {
  const files = readdirSync(dir).filter((f) => f.endsWith(".html")).sort();
  if (!files.length) warn(`no label files in ${dir}`);
  for (const f of files) {
    const p = await openPage(`${pathToFileURL(join(dir, f)).href}?mode=preview`, 1200, 1200);
    await within(60000, p.evaluate(LOAD_ALL), `loading ${f}`);
    const r = await p.evaluate(LABEL_PROBE);
    fontReport(await p.evaluate(FONT_PROBE), `label ${r.id}`);
    for (const o of r.over) err(`label ${r.id}, zone ${o.zone}: content overflows by ${o.v > 0.2 ? `${o.v.toFixed(1)} mm vertically` : ""}${o.v > 0.2 && o.h > 0.2 ? " and " : ""}${o.h > 0.2 ? `${o.h.toFixed(1)} mm horizontally` : ""}; shorten optional text or change the format, don't shrink mandatory text`);
    for (const b of r.broken) err(`label ${r.id}: image did not load: ${b}`);
    if (r.contrast < 4.5) warn(`label ${r.id}: text on the label colour has a contrast of ${r.contrast.toFixed(1)}:1; small print needs at least 4.5:1 to stay legible (WCAG is not a print norm, but the threshold works)`);
    const legalCat = ["food", "supplement"].includes(r.category);
    const need = r.surface && r.surface < 80 ? 0.9 : 1.2;
    const low = r.xs.filter((x) => x.xh + 0.005 < need);
    if (low.length) {
      const worst = low.reduce((a, b) => (a.xh < b.xh ? a : b));
      const pt = (need / (worst.xh / worst.pt)).toFixed(1);
      const msg = `label ${r.id}: x-height of mandatory text is ${worst.xh.toFixed(2)} mm (${low.map((x) => x.key).join(", ")}), needs ${need} mm${r.surface ? ` (largest surface ${r.surface} cm²)` : ""}: set legal_pt to at least ${pt}`;
      legalCat ? err(`${msg} (Regulation (EU) 1169/2011, art. 13)`) : warn(`${msg}; not a legal minimum for this category, but below it the text is hard to read`);
    } else if (r.xs.length) {
      const min = Math.min(...r.xs.map((x) => x.xh));
      console.log(`label ${r.id}: smallest mandatory x-height ${min.toFixed(2)} mm (needs ${need} mm)`);
    }
    for (const pr of [...new Set(p.problems)]) err(`label ${r.id}: page error: ${pr}`);
    await p.close();
  }
}

async function pdf(file, out) {
  const p = await openPage(pathToFileURL(file).href, 1440, 900, { media: "print" });
  await within(90000, p.evaluate(LOAD_ALL), "loading for PDF");
  await p.evaluate(`(window.dispatchEvent(new Event("beforeprint")), true)`);
  const { data } = await within(120000, p.s("Page.printToPDF", { printBackground: true, preferCSSPageSize: true }), "printing to PDF");
  writeFileSync(out, Buffer.from(data, "base64"));
  await p.close();
  const pages = (Buffer.from(data, "base64").toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []).length;
  console.log(`${out}: ${pages} pages, ${(statSync(out).size / 1e6).toFixed(1)} MB`);
  if (statSync(out).size > 20e6) warn(`${out} is over 20 MB; too big to email`);
}

async function shots(file, dir) {
  mkdirSync(dir, { recursive: true });
  for (const [w, hgt, mobile] of [[1440, 900, false], [390, 844, true]]) {
    const p = await openPage(pathToFileURL(file).href, w, hgt, { mobile });
    await within(60000, p.evaluate(LOAD_ALL), "loading the book");
    const first = await p.s("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(dir, `first-${w}.png`), Buffer.from(first.data, "base64"));
    const full = Math.min(await p.evaluate("document.documentElement.scrollHeight"), 30000);
    await p.evaluate(`(document.getElementById("toast")?.remove(), document.querySelector(".bar") && (document.querySelector(".bar").style.position = "static"), true)`);
    const { data } = await p.s("Page.captureScreenshot", { format: "jpeg", quality: 80, captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: full, scale: 1 } });
    writeFileSync(join(dir, `book-${w}.jpg`), Buffer.from(data, "base64"));
    console.log(join(dir, `book-${w}.jpg`), `${w} × ${full}`);
    // One image per section: a whole book in one picture is too small to read.
    mkdirSync(join(dir, "sections"), { recursive: true });
    const rects = await p.evaluate(`[...document.querySelectorAll(".cover, section.s")].map((el) => { const r = el.getBoundingClientRect(); return { id: el.id || "cover", x: r.left, y: r.top + scrollY, w: r.width, h: Math.min(r.height, 6000) }; })`);
    for (const r of rects) {
      const shot = await p.s("Page.captureScreenshot", { format: "jpeg", quality: 82, captureBeyondViewport: true, clip: { x: Math.max(0, r.x - 16), y: Math.max(0, r.y - 8), width: Math.min(w, r.w + 32), height: r.h + 16, scale: 1 } });
      writeFileSync(join(dir, "sections", `${r.id}-${w}.jpg`), Buffer.from(shot.data, "base64"));
    }
    console.log(`${join(dir, "sections")}/: ${rects.length} sections at ${w} px`);
    await p.close();
  }
}

async function labels(dir, out) {
  mkdirSync(out, { recursive: true });
  for (const f of readdirSync(dir).filter((x) => x.endsWith(".html")).sort()) {
    const id = basename(f, ".html");
    for (const m of ["preview", "guides"]) {
      const url = `${pathToFileURL(join(dir, f)).href}?mode=${m}`;
      const p = await openPage(url, 1200, 1200, { media: m === "preview" ? "print" : "screen" });
      await within(60000, p.evaluate(LOAD_ALL), `loading ${f}`);
      const size = await p.evaluate(`(() => { const r = document.getElementById("page").getBoundingClientRect(); return { w: r.width, h: r.height }; })()`);
      const shot = await p.s("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: size.w, height: size.h, scale: 4 } });
      writeFileSync(join(out, `${id}-${m}.png`), Buffer.from(shot.data, "base64"));
      const { data } = await p.s("Page.printToPDF", { printBackground: true, preferCSSPageSize: true });
      writeFileSync(join(out, m === "preview" ? `${id}.pdf` : `${id}-guides.pdf`), Buffer.from(data, "base64"));
      await p.close();
    }
    console.log(`${join(out, id)}.pdf, -preview.png, -guides.png, -guides.pdf`);
  }
}

const src = resolve(input);
if (!existsSync(src)) fail(`not found: ${src}`);
try {
  browser = await within(60000, Chrome.launch(), "Chromium start");
  if (mode === "check") {
    await checkBook(src);
    const labelDir = output ? resolve(output) : resolve(src, "../../labels");
    if (existsSync(labelDir)) await checkLabels(labelDir);
    console.log(`Checked: the book${existsSync(labelDir) ? " and labels" : ""}. Result: ${errors.length} ${errors.length === 1 ? "error" : "errors"}, ${warnings.length} ${warnings.length === 1 ? "warning" : "warnings"}.`);
  } else if (mode === "pdf") await pdf(src, resolve(output ?? "brandbook.pdf"));
  else if (mode === "shots") await shots(src, resolve(output ?? "shots"));
  else if (mode === "labels") await labels(src, resolve(output ?? "labels-out"));
} catch (e) {
  console.error(`ERROR: ${e.message}`);
  browser?.kill();
  process.exit(1);
}
browser.kill();
process.exit(errors.length ? 1 : 0);
