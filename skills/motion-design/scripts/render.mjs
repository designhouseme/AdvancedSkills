// SPDX-License-Identifier: CC-BY-4.0
// © 2026 Design House (https://designhouse.me)
//
// Renders a film from an HTML composition: frames from a local Chromium → ffmpeg → MP4.
// No npm packages: Chromium is driven over the DevTools Protocol on a local port
// (127.0.0.1), through the WebSocket built into Node 22+. The script does not connect to the internet.
//
//   node render.mjs --src index.html --still 1,2.5      # stills: out/stills/still-0001.00.png …
//   node render.mjs --src index.html --from 4 --to 6    # a passage, e.g. to measure ms/frame
//   node render.mjs --src index.html --out film.mp4     # the whole film
//   node render.mjs --src index.html --preflight       # environment and asset checks
//   node render.mjs --src index.html --check-frames    # sampled raw-pixel repeatability
//
// Options: --sub 5 (subframes per frame, motion blur; default: SUB in the composition), --shutter 0.5, --fps 60,
// --workers N, --outdir out, --speed 0.75, --name Name, --params "w=1080&h=1920",
// --audio track.wav (only a supplied track; by default the film is silent),
// --chrome /path/to/chromium, --timeline timeline.generated.json, --timeout 30000 (milliseconds).
//
// The composition exposes: window.__ready (Promise), window.__render(t), window.__DURATION (s),
// and optionally window.__SIZE {w, h}, window.__CUES and window.__CUTS (output seconds).
// __render may be async; __ready and every __render are awaited before capture.
//
// Each worker is a separate Chromium with a contiguous range of frames and its own ffmpeg (segment crf 4,
// yuv444p). tmix averages the subframes within a segment, then concat and the final encode
// (crf 17, yuv420p). Exit code: 0 = done, 1 = render error, 2 = bad input.

import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, renameSync, rmSync, statfsSync, statSync, writeFileSync } from "node:fs";
import { cpus, freemem, homedir, tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const runId = `${Date.now()}-${process.pid}`;
// Resolve diagnostics independently of validation, so a bad option/tool cannot leave
// a previous successful check looking current. Ambiguous output paths are not guessed.
const invocation = process.argv.slice(2);
const diagnosticValue = (flag, fallback) => {
  const positions = invocation.flatMap((value, index) => value === flag ? [index] : []);
  if (!positions.length) return fallback;
  if (positions.length !== 1) return null;
  const value = invocation[positions[0] + 1];
  return value && !value.startsWith("--") ? value : null;
};
const diagnosticSource = diagnosticValue("--src", "index.html");
const diagnosticFolder = diagnosticValue("--outdir", "out");
const diagnosticDir = diagnosticSource && diagnosticFolder ? resolve(dirname(resolve(diagnosticSource)), diagnosticFolder) : null;
const recordFailure = (message) => {
  if (!diagnosticDir) return;
  const names = [...(invocation.includes("--preflight") ? ["environment.json"] : []),
    ...(invocation.includes("--check-frames") ? ["frame-check.json"] : [])];
  for (const name of names) {
    try {
      mkdirSync(diagnosticDir, { recursive: true });
      const path = join(diagnosticDir, name), tmp = `${path}.${runId}.tmp`;
      let current;
      try { current = JSON.parse(readFileSync(path, "utf8")); } catch {}
      const report = { ...(current?.runId === runId ? current : {}), version: 1, runId, status: "failed", error: message };
      writeFileSync(tmp, JSON.stringify(report, null, 2) + "\n");
      renameSync(tmp, path);
    } catch (error) { console.error(`Cannot record failed ${name}: ${error.message}`); }
  }
};
const fail = (msg, code = 2) => {
  console.error(`ERROR: ${msg}`);
  recordFailure(msg);
  process.exit(code);
};
if (typeof WebSocket === "undefined") fail(`Node 22 or newer is required (built-in WebSocket), found ${process.version}.`);

const flags = new Set(["help", "preflight", "check-frames"]);
const values = new Set(["src", "fps", "sub", "shutter", "workers", "outdir", "params", "name", "speed", "chrome", "still", "from", "to", "out", "audio", "timeline", "times", "timeout"]);
const args = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  if (!a.startsWith("--")) fail(`unexpected argument: ${a}`);
  const key = a.slice(2);
  if (key in args) fail(`duplicate option: ${a}`);
  if (flags.has(key)) args[key] = true;
  else if (values.has(key)) {
    const value = process.argv[++i];
    if (value === undefined || value.startsWith("--")) fail(`${a} needs a value`);
    args[key] = value;
  } else fail(`unknown option: ${a}`);
}
if (args.help) {
  console.log(`Usage: node render.mjs --src index.html [options]
  --preflight                 Check tools, local assets and composition; write environment.json
  --check-frames              Compare raw captured pixels after forward/reverse/shuffled/fresh seeks
  --times 0,0.5,1             Sample times for --check-frames (otherwise chosen from duration/cues/cuts)
  --timeline generated.json   Inject compiled window.__TIMELINE; validate size, duration and fps
  --still 0,1.5              PNG stills, before motion blur
  --from S --to S            Render a range (audio is trimmed to the same range)
  --fps 60 --sub 5 --shutter 0.5 --workers N
  --audio file.wav           Pad/trim supplied audio to the video duration; no automatic time stretching
  --out film.mp4 --outdir out --chrome PATH --timeout 30000
  --speed 0.75 --name NAME --params 'w=1080&h=1920'
Integer fps only. With --timeline, retime using compile_timeline.py --speed instead.`);
  process.exit(0);
}
const numeric = (key, fallback, { min = 0, integer = false, max = Infinity, exclusive = false } = {}) => {
  const n = Number(args[key] ?? fallback);
  if (!Number.isFinite(n) || (exclusive ? n <= min : n < min) || n > max || (integer && !Number.isSafeInteger(n)))
    fail(`--${key} must be ${integer ? "an integer" : "a number"} ${exclusive ? ">" : ">="} ${min}${Number.isFinite(max) ? ` and <= ${max}` : ""}`);
  return n;
};
const jsonFile = (path) => {
  try { return JSON.parse(readFileSync(path, "utf8")); } catch (error) { fail(`cannot read JSON ${path}: ${error.message}`); }
};
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const hashFile = (path) => hash(readFileSync(path));
const timelinePath = args.timeline ? resolve(args.timeline) : null;
const timeline = timelinePath ? jsonFile(timelinePath) : null;
if (timelinePath && (!timeline || timeline.version !== 1 || !Number.isSafeInteger(timeline.fps) || timeline.fps < 1 ||
    !Number.isSafeInteger(timeline.durationFrames) || timeline.durationFrames < 1 ||
    !Number.isFinite(timeline.duration) || Math.abs(timeline.duration - timeline.durationFrames / timeline.fps) > 1e-8 ||
    !Array.isArray(timeline.cuts) || !Array.isArray(timeline.cues))) fail("invalid compiled timeline; run compile_timeline.py");
if (timeline && args.speed !== undefined) fail("--speed with --timeline would retime twice; use compile_timeline.py --speed");
if ([args.preflight, args["check-frames"], args.still !== undefined].filter(Boolean).length > 1) fail("choose one of --preflight, --check-frames or --still");
if (args.times && !args["check-frames"]) fail("--times requires --check-frames");

const src = resolve(args.src ?? "index.html");
if (!existsSync(src) || !statSync(src).isFile()) fail(`composition not found: ${src}`);
const fps = numeric("fps", timeline?.fps ?? 60, { min: 1, integer: true });
if (timeline && fps !== timeline.fps) fail("--fps must match the compiled timeline");
let sub = args.sub !== undefined ? numeric("sub", 5, { min: 1, integer: true, max: 128 }) : null;
const shutter = numeric("shutter", 0.5, { min: 0, max: 1 });
const workers = numeric("workers", Math.max(1, Math.min(8, Math.floor(cpus().length / 2))), { min: 1, integer: true, max: 64 });
const timeout = numeric("timeout", 30000, { min: 1, integer: true });
if (args.speed !== undefined) numeric("speed", 1, { exclusive: true });
if (args.from !== undefined) numeric("from", 0);
if (args.to !== undefined) numeric("to", 0, { exclusive: true });
if (args.from !== undefined && args.to !== undefined && Number(args.to) <= Number(args.from)) fail("--to must be greater than --from");
const parseTimes = (value) => {
  const result = value.split(",").map((v) => v.trim() === "" ? NaN : Number(v));
  if (!result.length || result.some((t) => !Number.isFinite(t) || t < 0)) fail("sample times must be nonnegative numbers, separated by commas");
  return result;
};
if (args.still !== undefined) parseTimes(args.still);
if (args.times !== undefined) parseTimes(args.times);
const audio = args.audio ? resolve(args.audio) : null;
if (audio && (!existsSync(audio) || !statSync(audio).isFile())) fail(`audio file not found: ${audio}`);
const outDir = resolve(dirname(src), args.outdir ?? "out");
const query = new URLSearchParams(args.params ?? "");
query.set("capture", "1");
if (args.name) query.set("name", args.name);
if (args.speed) query.set("speed", args.speed);
if (timeline && query.has("speed")) fail("timeline speed belongs in compile_timeline.py, not --params");
const url = `${pathToFileURL(src).href}?${query}`;
const atomicJSON = (path, value) => {
  const tmp = `${path}.${runId}.tmp`;
  writeFileSync(tmp, JSON.stringify(value, null, 2) + "\n");
  renameSync(tmp, path);
};
const command = (program, argv, options = {}) => {
  const r = spawnSync(program, argv, { encoding: "utf8", timeout, maxBuffer: 8 * 1024 * 1024, ...options });
  if (r.error || r.status !== 0) throw new Error(`${program}: ${r.error?.message ?? r.stderr?.toString().slice(-1200) ?? `exit ${r.status}`}`);
  return r.stdout;
};

function findChrome() {
  if (args.chrome || process.env.CHROME) return args.chrome || process.env.CHROME;
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
const chrome = findChrome();
let toolsInfo;
try {
  toolsInfo = { node: process.version, chrome: command(chrome, ["--version"]).trim(),
    ffmpeg: command("ffmpeg", ["-version"]).split("\n")[0], ffprobe: command("ffprobe", ["-version"]).split("\n")[0] };
  const encoders = command("ffmpeg", ["-hide_banner", "-encoders"]);
  const filters = command("ffmpeg", ["-hide_banner", "-filters"]);
  if (!/\blibx264\b/.test(encoders)) fail("ffmpeg lacks libx264");
  if (audio && !/\baac\b/.test(encoders)) fail("ffmpeg lacks AAC");
  for (const filter of ["tmix", "select", "setpts", ...(audio ? ["apad", "atrim", "asetpts"] : [])])
    if (!new RegExp(`\\b${filter}\\b`).test(filters)) fail(`ffmpeg lacks ${filter}`);
  if (audio) {
    const info = JSON.parse(command("ffprobe", ["-v", "error", "-show_streams", "-of", "json", audio]));
    if (!info.streams?.some((s) => s.codec_type === "audio")) fail(`no audio stream in ${audio}`);
  }
} catch (error) { fail(error.message); }
mkdirSync(outDir, { recursive: true });

// A timeout that clears its timer. Without clearTimeout, Promise.race holds on to the result
// (a ~4 MB frame) until the timer expires, and at a dozen or so frames per second Node dies with OOM.
const within = (ms, p, what) => {
  let timer;
  const limit = new Promise((_, reject) => (timer = setTimeout(() => reject(new Error(`${what}: timed out after ${ms / 1000} s`)), ms)));
  return Promise.race([p, limit]).finally(() => clearTimeout(timer));
};

// ------------------------------------------------------------------
// Chromium over the DevTools Protocol
// ------------------------------------------------------------------
// Profiles are removed only after the process exits, and all of them once more at the end:
// a closing Chromium can still write files into the profile after the folder has been removed.
const profiles = new Set();
const sweep = () => {
  for (const p of profiles) rmSync(p, { recursive: true, force: true });
};
// Every Chromium of this run, from launch until it closes. An abort kills all of them, including one that is
// still opening its page; before this, such a browser outlived the render.
const running = new Set();
const encoders = new Set();
const resourceHashes = new Map();
const killAll = () => {
  for (const c of running) c.kill();
  for (const p of encoders) { try { p.kill("SIGKILL"); } catch {} }
};
process.on("exit", () => (killAll(), sweep()));
process.on("SIGINT", () => process.exit(130));
process.on("SIGTERM", () => process.exit(143));

// Chromium's sockets in the profile have a path length limit (about 100 characters): with a long TMPDIR
// Chromium dies with "Socket path too long", so in that case the profile goes to /tmp.
const tmpBase = tmpdir().length > 40 && existsSync("/tmp") ? "/tmp" : tmpdir();
// The profile name carries this run's PID, so cleaning up after a crash touches only this run, not renders in other folders.
const profilePrefix = join(tmpBase, `motion-chrome-${process.pid}-`);

class Chrome {
  static async launch() {
    const profile = mkdtempSync(profilePrefix);
    profiles.add(profile);
    const flags = [
      "--headless=new", "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1", `--user-data-dir=${profile}`,
      "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--disable-background-networking", "--mute-audio",
      "--hide-scrollbars", "--force-color-profile=srgb", "--font-render-hinting=none", "--disable-lcd-text", "--allow-file-access-from-files",
      ...(process.getuid?.() === 0 ? ["--no-sandbox"] : []), // Chromium does not start as root without this flag
      "about:blank",
    ];
    // its own process group, so a kill also ends the renderer and GPU processes
    const proc = spawn(chrome, flags, { stdio: ["ignore", "ignore", "pipe"], detached: true });
    const c = new Chrome(proc, profile);
    running.add(c);
    try {
      const ws = await within(timeout, new Promise((res, rej) => {
        let buf = "";
        let found = false;
        // read stderr to the end, otherwise a clogged pipe can stall Chromium
        proc.stderr.on("data", (d) => {
          if (found) return;
          buf += d;
          const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
          if (m) {
            found = true;
            res(m[1]);
          }
        });
        proc.on("exit", (code) => !found && rej(new Error(`Chromium exited before startup (code ${code}): ${buf.slice(-300)}`)));
        proc.on("error", rej);
      }), "Chromium start");
      await within(timeout, c.connect(ws), "DevTools connection");
      return c;
    } catch (error) {
      await c.close();
      throw error;
    }
  }
  constructor(proc, profile) {
    this.proc = proc;
    this.profile = profile;
    this.seq = 0;
    this.pending = new Map();
    this.listeners = new Set();
  }
  connect(wsUrl) {
    return new Promise((res, rej) => {
      const ws = new WebSocket(wsUrl);
      ws.onopen = () => res();
      ws.onerror = () => rej(new Error("could not connect to DevTools"));
      ws.onclose = () => {
        for (const { reject } of this.pending.values()) reject(new Error("connection to Chromium closed"));
        this.pending.clear();
      };
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve, reject } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          if (msg.error) reject(new Error(`${msg.error.message}`));
          else resolve(msg.result);
        } else if (msg.method) for (const listen of this.listeners) listen(msg);
      };
      this.ws = ws;
    });
  }
  send(method, params = {}, sessionId) {
    const id = ++this.seq;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      try { this.ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) })); }
      catch (error) { this.pending.delete(id); reject(error); }
    });
  }
  once(method, sessionId) {
    return new Promise((resolve) => {
      const listen = (msg) => {
        if (msg.method === method && msg.sessionId === sessionId) {
          this.listeners.delete(listen);
          resolve(msg.params);
        }
      };
      this.listeners.add(listen);
    });
  }
  // Graceful close: Browser.close also ends the child processes (network, GPU), which after a bare
  // SIGKILL of the main process live on for a moment and recreate the profile folder.
  async close() {
    const exited = new Promise((r) => (this.proc.exitCode !== null || this.proc.signalCode !== null ? r() : this.proc.once("exit", r)));
    try {
      await within(2000, this.send("Browser.close"), "closing Chromium");
    } catch {}
    await within(5000, exited, "Chromium exit").catch(() => this.hardKill());
    try { this.ws?.close(); } catch {}
    rmSync(this.profile, { recursive: true, force: true });
    profiles.delete(this.profile);
    running.delete(this);
  }
  hardKill() {
    try { process.kill(-this.proc.pid, "SIGKILL"); } catch { try { this.proc.kill("SIGKILL"); } catch {} }
  }
  // Emergency (Ctrl+C, error): no waiting; the sweep at exit removes the profile folder.
  kill() {
    try { this.ws?.close(); } catch {}
    this.hardKill();
    running.delete(this);
  }
}

async function preparePage(c) {
  const { targetInfos } = await c.send("Target.getTargets");
  const target = targetInfos.find((t) => t.type === "page") ?? (await c.send("Target.createTarget", { url: "about:blank" }));
  const { sessionId } = await c.send("Target.attachToTarget", { targetId: target.targetId, flatten: true });
  const s = (method, params) => c.send(method, params, sessionId);
  let logged = 0;
  const pageErrors = [];
  const requests = new Map();
  const resources = new Set();
  const assertHealthy = () => {
    if (pageErrors.length) throw new Error(`composition failed: ${[...new Set(pageErrors)].join("; ").slice(0, 2500)}`);
  };
  c.listeners.add((msg) => {
    if (msg.sessionId !== sessionId) return;
    if (msg.method === "Runtime.exceptionThrown") {
      const d = msg.params.exceptionDetails;
      pageErrors.push(d?.exception?.description ?? d?.text ?? "uncaught exception");
    }
    if (msg.method === "Runtime.consoleAPICalled") {
      const text = msg.params.args.map((a) => a.value ?? a.description).join(" ");
      if (msg.params.type === "error") pageErrors.push(text);
      // console.log and the like: at most 50 per browser, so a log inside update(t) can't flood the log
      else if (logged < 50) console.error(`[console.${msg.params.type}]`, text, ++logged === 50 ? "(further messages from this browser are not shown)" : "");
    }
    if (msg.method === "Network.requestWillBeSent") {
      const u = msg.params.request.url;
      requests.set(msg.params.requestId, u);
      if (/^(https?|wss?):/i.test(u)) pageErrors.push(`remote resource blocked: ${u}`);
      if (u.startsWith("file:")) {
        resources.add(u);
        try {
          const path = fileURLToPath(u), digest = hashFile(path);
          if (resourceHashes.has(path) && resourceHashes.get(path) !== digest) pageErrors.push(`asset changed during capture: ${path}`);
          else resourceHashes.set(path, digest);
        } catch (error) { pageErrors.push(`local asset unavailable: ${u} (${error.message})`); }
      }
    }
    if (msg.method === "Network.loadingFailed") {
      const u = requests.get(msg.params.requestId);
      if (u && !msg.params.canceled) pageErrors.push(`resource failed: ${u} (${msg.params.errorText})`);
    }
  });
  const evaluate = async (expression) => {
    const r = await s("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
    return r.result.value;
  };
  await s("Page.enable");
  await s("Runtime.enable");
  await s("Network.enable");
  await s("Network.setBlockedURLs", { urls: ["http://*", "https://*", "ws://*", "wss://*"] });
  if (timeline) await s("Page.addScriptToEvaluateOnNewDocument", { source: `window.__TIMELINE = ${JSON.stringify(timeline)};` });
  await s("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
  const loaded = c.once("Page.loadEventFired", sessionId);
  await s("Page.navigate", { url });
  await loaded;
  await evaluate(`(async () => {
    if (!window.__ready || typeof window.__ready.then !== 'function') throw new Error('missing __ready Promise');
    await window.__ready;
    if (typeof window.__render !== 'function') throw new Error('missing __render(t)');
    await document.fonts.ready;
    for (const f of document.fonts) if (f.status === 'error') throw new Error('font failed: ' + f.family);
    await Promise.all([...document.images].map(async (img) => {
      await img.decode();
      if (!img.naturalWidth) throw new Error('image failed: ' + img.src);
    }));
  })()`);
  assertHealthy();
  const size = (await evaluate("window.__SIZE ?? null")) ?? { w: 1920, h: 1080 };
  if (![size.w, size.h].every((n) => Number.isSafeInteger(n) && n > 0 && n % 2 === 0)) throw new Error("__SIZE needs positive even integer w/h for H.264");
  if (timeline && (size.w !== timeline.size?.width || size.h !== timeline.size?.height)) throw new Error("composition size differs from compiled timeline");
  await s("Emulation.setDeviceMetricsOverride", { width: size.w, height: size.h, deviceScaleFactor: 1, mobile: false });
  await s("Page.bringToFront");
  const duration = await evaluate("window.__DURATION");
  if (!Number.isFinite(duration) || duration <= 0) throw new Error("__DURATION must be finite and positive");
  if (timeline && Math.abs(duration - timeline.duration) > 1e-8) throw new Error("composition duration differs from compiled timeline");
  const declaredFPS = await evaluate("window.__FPS ?? null");
  if (declaredFPS !== null && declaredFPS !== fps) throw new Error("composition __FPS differs from output fps");
  const cues = timeline?.cues ?? (await evaluate("window.__CUES ?? []")) ?? [];
  if (!Array.isArray(cues) || cues.some((cue) => !cue || typeof cue !== "object" || Array.isArray(cue) || !Number.isFinite(cue.t) || cue.t < 0 || cue.t >= duration ||
    (cue.d !== undefined && (!Number.isFinite(cue.d) || cue.d < 0 || cue.t + cue.d > duration + 1e-8))))
    throw new Error("__CUES must contain valid t/d within the film");
  const cuts = timeline?.cuts ?? await evaluate("window.__CUTS ?? []");
  if (!Array.isArray(cuts) || cuts.some((t) => !Number.isFinite(t) || t <= 0 || t >= duration)) throw new Error("__CUTS must contain seconds strictly inside the film");
  const subframes = await evaluate("window.__SUB ?? null");
  if (sub === null && subframes !== null && (!Number.isSafeInteger(subframes) || subframes < 1 || subframes > 128)) throw new Error("__SUB must be an integer from 1 to 128");
  return { c, s, sessionId, evaluate, duration, subframes, size, cues, cuts: [...new Set(cuts)].sort((a, b) => a - b), assertHealthy, resources };
}

// With many browsers at once, a single one can get stuck at startup: a timeout and a retry.
async function openPage(tries = 3) {
  for (let k = 1; ; k++) {
    let c;
    try {
      c = await Chrome.launch();
      return await within(timeout, preparePage(c), "page setup");
    } catch (error) {
      await c?.close();
      if (k >= tries || !/timed out|Chromium exited|DevTools connection/.test(error.message)) throw error;
      console.error(`\n${error.message}, retrying (${k}/${tries - 1})`);
    }
  }
}

async function frame(ctx, t) {
  // An async seek/decode must finish BEFORE the layout/capture barrier.
  await within(timeout, ctx.evaluate(`(async () => { await window.__render(${t}); await new Promise(requestAnimationFrame); })()`), `frame ${t.toFixed(3)} s`);
  ctx.assertHealthy();
  const { data } = await within(timeout, ctx.s("Page.captureScreenshot", { format: "png", optimizeForSpeed: true }), `screenshot ${t.toFixed(3)} s`);
  ctx.assertHealthy();
  return Buffer.from(data, "base64");
}

function assetSnapshot(ctx) {
  return [...ctx.resources].map((url) => fileURLToPath(url)).filter((p, i, all) => all.indexOf(p) === i).sort()
    .map((path) => ({ path, sha256: hashFile(path) }));
}

function unchangedInputs(environment) {
  for (const entry of [environment.source, environment.timeline, environment.audio, ...[...resourceHashes].map(([path, sha256]) => ({ path, sha256 }))].filter(Boolean))
    if (hashFile(entry.path) !== entry.sha256) throw new Error(`input changed during capture: ${entry.path}; render again from stable inputs`);
  environment.assets = [...resourceHashes].sort(([a], [b]) => a.localeCompare(b)).map(([path, sha256]) => ({ path, sha256 }));
}

async function checkFrames(ctx) {
  const reportPath = join(outDir, "frame-check.json");
  const last = Math.max(0, Math.ceil(ctx.duration * fps) - 1) / fps;
  const suggested = [0, last / 4, last / 2, last * 3 / 4, last];
  for (const t of [...ctx.cuts, ...ctx.cues.map((cue) => cue.t)].slice(0, 40))
    suggested.push(Math.max(0, t - 1 / fps), t, Math.min(last, t + 1 / fps));
  const times = [...new Set(args.times ? parseTimes(args.times) : suggested.map((t) => Math.round(t * fps) / fps))].sort((a, b) => a - b);
  if (times.some((t) => t >= ctx.duration)) throw new Error("check times must be before __DURATION (end is exclusive)");
  if (times.length > 128) throw new Error("at most 128 check times; split a larger check into runs");
  const report = { version: 1, runId, status: "not_checked", source: { path: src, sha256: hashFile(src) },
    timeline: timelinePath ? { path: timelinePath, sha256: hashFile(timelinePath) } : null,
    toolchain: toolsInfo, query: query.toString(), fps, size: ctx.size, times, comparisons: [],
    scope: "Exact RGBA pixels before encoding, sampled times on this machine. Not a check of every frame or cross-platform equivalence." };
  atomicJSON(reportPath, report);
  const baseline = new Map();
  const evidenceDir = join(outDir, `frame-check-${runId}`);
  const raw = (png) => command("ffmpeg", ["-v", "error", "-i", "pipe:0", "-f", "rawvideo", "-pix_fmt", "rgba", "pipe:1"],
    { encoding: null, input: png, maxBuffer: ctx.size.w * ctx.size.h * 4 + 1024 * 1024 });
  const capture = async (page, t, pass) => {
    const png = await frame(page, t);
    const pixels = raw(png);
    if (pixels.length !== ctx.size.w * ctx.size.h * 4) throw new Error(`incomplete decoded screenshot at ${t}`);
    const digest = hash(pixels);
    if (pass === "forward") { baseline.set(t, { digest, png }); return; }
    const expected = baseline.get(t);
    const equal = digest === expected.digest;
    const result = { t, pass, status: equal ? "passed" : "failed", expected: expected.digest, actual: digest };
    if (!equal) {
      mkdirSync(evidenceDir, { recursive: true });
      const stem = `${pass}-${String(times.indexOf(t)).padStart(3, "0")}`;
      const a = join(evidenceDir, `${stem}-expected.png`), b = join(evidenceDir, `${stem}-actual.png`), diff = join(evidenceDir, `${stem}-diff.png`);
      writeFileSync(a, expected.png); writeFileSync(b, png);
      command("ffmpeg", ["-v", "error", "-y", "-i", a, "-i", b, "-filter_complex", "blend=all_mode=difference", "-frames:v", "1", diff]);
      result.evidence = { expected: a, actual: b, difference: diff };
    }
    report.comparisons.push(result);
  };
  try {
    for (const t of times) await capture(ctx, t, "forward");
    for (const t of [...times].reverse()) await capture(ctx, t, "reverse");
    // Fixed permutation; no random seed or clock enters the composition.
    const shuffled = times.filter((_, i) => i % 2).reverse().concat(times.filter((_, i) => !(i % 2)));
    for (const t of shuffled) await capture(ctx, t, "shuffled");
    // A second browser models a separate render worker, independent of the first page's state.
    const other = await openPage();
    try { for (const t of times) await capture(other, t, "second-browser"); }
    finally { await other.c.close(); }
    // Reload for EACH selected sample, so a seek never relies on an earlier sampled time.
    const coldBrowser = await Chrome.launch();
    try {
      for (const t of times) {
        coldBrowser.listeners.clear();
        const fresh = await within(timeout, preparePage(coldBrowser), "fresh page setup");
        await capture(fresh, t, "fresh-page");
        await coldBrowser.send("Target.detachFromTarget", { sessionId: fresh.sessionId });
      }
    } finally { await coldBrowser.close(); }
    unchangedInputs(report);
    report.status = report.comparisons.some((r) => r.status === "failed") ? "failed" : "passed";
  } catch (error) {
    report.status = "failed";
    report.error = error.message;
  } finally {
    await ctx.c.close();
    atomicJSON(reportPath, report);
  }
  console.log(`${report.status}: ${report.comparisons.length} frame comparisons; ${reportPath}`);
  if (report.status !== "passed") throw new Error(report.error ?? "frame determinism failed; inspect frame-check.json and difference images");
}

async function main() {
const probe = await openPage();
const duration = probe.duration;
sub ??= Number(probe.subframes ?? 5);
const disk = statfsSync(outDir);
const environment = { version: 1, runId, toolchain: toolsInfo, source: { path: src, sha256: hashFile(src) },
  timeline: timelinePath ? { path: timelinePath, sha256: hashFile(timelinePath) } : null,
  audio: audio ? { path: audio, sha256: hashFile(audio) } : null,
  query: query.toString(), fps, sub, shutter, workers, duration, size: probe.size, cuts: probe.cuts,
  availableMemoryBytes: freemem(), availableDiskBytes: disk.bavail * disk.bsize, network: "remote URLs blocked during capture",
  status: "passed", assets: assetSnapshot(probe) };
atomicJSON(join(outDir, "environment.json"), environment);
// Legacy HTML owns its cues. A compiled timeline is never overwritten from a worker page.
if (!timeline) atomicJSON(join(outDir, "cues.json"), { duration, cuts: probe.cuts, cues: probe.cues });
if (args.preflight) {
  await frame(probe, 0);
  unchangedInputs(environment);
  atomicJSON(join(outDir, "environment.json"), environment);
  await probe.c.close();
  console.log(`preflight passed: ${join(outDir, "environment.json")}`);
  return;
}
if (args["check-frames"]) { await checkFrames(probe); return; }

// ------------------------------------------------------------------
// Stills
// ------------------------------------------------------------------
if (args.still) {
  // Each round of stills goes into a clean folder, so the sheet never mixes old frames with new ones.
  const stillDir = join(outDir, "stills");
  rmSync(stillDir, { recursive: true, force: true });
  mkdirSync(stillDir, { recursive: true });
  const ctx = probe;
  try {
    for (const t of parseTimes(args.still)) {
      if (t >= duration) throw new Error("still times must be before __DURATION (end is exclusive)");
      const file = join(stillDir, `still-${t.toFixed(2).padStart(7, "0")}.png`); // still-0012.40.png: sorts by time
      writeFileSync(file, await frame(ctx, t));
      console.log(file);
    }
  } finally {
    await ctx.c.close();
  }
  return;
}

// ------------------------------------------------------------------
// Film or passage
// ------------------------------------------------------------------
await probe.c.close();
if (!(Number.isInteger(sub) && sub >= 1)) fail(`--sub must be a whole number from 1 up, got ${args.sub ?? probe.subframes}`);

const t0 = Number(args.from ?? 0);
const t1 = Math.min(Number(args.to ?? duration), duration);
if (![t0, t1].every(Number.isFinite)) fail(`--from and --to must be numbers of seconds, got "${args.from}" and "${args.to}"`);
const first = Math.round(t0 * fps);
const total = Math.round(t1 * fps) - first;
if (total <= 0) fail(`empty range: from ${t0} to ${t1} s`);
const per = Math.ceil(total / workers);
const segDir = mkdtempSync(join(outDir, ".render-"));

console.log(`${total} frames × ${sub} subframes, ${workers} workers, ${fps} fps, ${(t1 - t0).toFixed(2)} s`);
// [x] in the pattern: pkill -f would otherwise also match the shell that runs it; find instead of a glob, which zsh aborts on
const notSelf = (p) => `${p.slice(0, -2)}[${p.slice(-2, -1)}]${p.slice(-1)}`;
console.log(`if this run is killed, clean up only its own processes: pkill -f '${notSelf(profilePrefix)}'; pkill -f '${notSelf(`${segDir}/`)}'; find ${tmpBase} -maxdepth 1 -name '${basename(profilePrefix)}*' -exec rm -rf {} +`);
const started = Date.now();
let done = 0;
function startEncoder(argv) {
  const proc = spawn("ffmpeg", argv, { stdio: ["pipe", "inherit", "inherit"] });
  encoders.add(proc);
  const done = new Promise((resolve, reject) => {
    proc.once("error", reject);
    proc.once("close", (code) => { encoders.delete(proc); code === 0 ? resolve() : reject(new Error(`ffmpeg exit ${code}`)); });
  });
  // Attach a rejection handler immediately; it may fail before all frames have been written.
  done.catch(() => {});
  proc.stdin.on("error", () => {});
  return { proc, done };
}

async function worker(w) {
  const a = first + w * per;
  const b = Math.min(first + total, a + per);
  if (a >= b) return null;
  const ctx = await openPage();
  if (ctx.duration !== duration || ctx.size.w !== probe.size.w || ctx.size.h !== probe.size.h || JSON.stringify(ctx.cuts) !== JSON.stringify(probe.cuts)) {
    await ctx.c.close();
    throw new Error("composition metadata differs between render workers");
  }
  const seg = join(segDir, `seg-${String(w).padStart(2, "0")}.mkv`);
  // tmix averages the last `sub` subframes; select keeps every `sub`-th one, which is a full frame.
  const vf = sub > 1 ? [`tmix=frames=${sub}`, `select='eq(mod(n\\,${sub})\\,${sub - 1})'`, `setpts=N/${fps}/TB`] : [];
  const { proc: ff, done: closed } = startEncoder(
    ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps * sub), "-i", "-", ...(vf.length ? ["-vf", vf.join(",")] : []),
      "-r", String(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "4", "-pix_fmt", "yuv444p", seg],
  );
  try {
    for (let i = a; i < b; i++) {
      const frameTime = i / fps;
      const cutFloor = ctx.cuts.filter((cut) => cut <= frameTime + 1e-9).at(-1) ?? 0;
      for (let k = 0; k < sub; k++) {
        const t = (i + (sub > 1 ? (k / (sub - 1) - 1) * shutter : 0)) / fps; // subframes end at the frame's time
        const png = await frame(ctx, Math.max(cutFloor, t));
        await within(timeout, Promise.race([
          new Promise((resolve, reject) => ff.stdin.write(png, (error) => error ? reject(error) : resolve())),
          closed.then(() => { throw new Error("encoder exited before all frames were written"); }),
        ]), "writing frame to ffmpeg");
      }
      done++;
      if (done % 30 === 0) {
        const el = (Date.now() - started) / 1000;
        process.stdout.write(`\r${done}/${total}  ${((el / done) * 1000).toFixed(0)} ms/frame  ETA ${(((total - done) * el) / done).toFixed(0)} s   `);
      }
    }
    ff.stdin.end();
    await closed;
  } finally {
    if (ff.exitCode === null) ff.kill();
    await ctx.c.close();
  }
  return seg;
}

let segs;
try {
  segs = (await Promise.all(Array.from({ length: workers }, (_, w) => worker(w)))).filter(Boolean);
} catch (error) {
  killAll();
  fail(`render aborted: ${error.message}`, 1);
}
const secs = (Date.now() - started) / 1000;
console.log(`\nframes done in ${secs.toFixed(0)} s (${((secs / total) * 1000).toFixed(0)} ms/frame overall)`);

const list = join(segDir, "list.txt");
// Generated segment names are quote-free; FFmpeg resolves them beside list.txt.
writeFileSync(list, segs.map((s) => `file '${basename(s)}'`).join("\n"));
const name = args.out ?? (args.from || args.to ? `part-${t0}-${t1}.mp4` : "film.mp4");
const withAudio = Boolean(audio);
const final = resolve(outDir, name);
if ([src, audio, timelinePath].includes(final)) throw new Error("output must not overwrite an input file");
mkdirSync(dirname(final), { recursive: true });
const tmp = join(segDir, "final.mp4");
const outputDuration = total / fps;
const enc = ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", list, ...(withAudio ? ["-i", audio] : []),
  "-map", "0:v:0", ...(withAudio ? ["-map", "1:a:0", "-af", `apad,atrim=start=${first / fps}:duration=${outputDuration},asetpts=PTS-STARTPTS`] : []),
  "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-tune", "animation",
  ...(withAudio ? ["-c:a", "aac", "-b:a", "192k"] : ["-an"]), "-t", String(outputDuration), "-movflags", "+faststart", "-f", "mp4", tmp];
const finalEncoder = startEncoder(enc);
finalEncoder.proc.stdin.end();
await finalEncoder.done;
const actual = JSON.parse(command("ffprobe", ["-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", tmp]));
const video = actual.streams?.find((s) => s.codec_type === "video");
if (!video || Number(video.nb_read_frames) !== total || video.width !== probe.size.w || video.height !== probe.size.h)
  throw new Error("encoded video does not match expected frame count or size");
if (Math.abs(Number(video.duration) - outputDuration) > 1 / fps + 0.001) throw new Error("encoded duration differs from the requested frame range");
// The finished file is moved into place at the end: an interrupted render never leaves a cut-off MP4 under the target name.
unchangedInputs(environment);
try { renameSync(tmp, final); }
catch (error) {
  if (error.code !== "EXDEV") throw error;
  const localTmp = `${final}.${runId}.tmp`;
  try { copyFileSync(tmp, localTmp); renameSync(localTmp, final); }
  finally { rmSync(localTmp, { force: true }); }
}
atomicJSON(`${final}.render.json`, { ...environment, artifact: { path: final, sha256: hashFile(final), bytes: statSync(final).size },
  fromFrame: first, endFrame: first + total, frameCount: total, outputDuration, audioPolicy: withAudio ? "original speed; padded and trimmed to video range" : "silent" });
rmSync(segDir, { recursive: true, force: true });
console.log(final);
}

try { await main(); }
catch (error) {
  console.error(`ERROR: ${error.message}`);
  recordFailure(error.message);
  process.exitCode = 1;
} finally {
  await Promise.allSettled([...running].map((c) => c.close()));
  killAll();
  sweep();
}
