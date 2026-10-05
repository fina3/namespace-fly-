// The Live-view wall: N macOS Devboxes, each with DOOMFLY installed and a fly brain playing Doom on
// its screen in an endless loop (intact, DNp20 off, DNpe017 off, MeVP9 off, ...). The dashboard's
// Instances -> Live grid then shows them side by side. Namespace compute only; no Anthropic API.
//
//   node mac_wall.mjs up <count> [--prefix fly-mac] [--size m] [--res 1600x1200]
//   node mac_wall.mjs shots [--prefix fly-mac]        # one screenshot per box into results/live-view/
//   node mac_wall.mjs down [--prefix fly-mac]         # delete every box with the prefix
//
// Each box gets its own game seed (seed = 41027 + index), so the tiles don't play identical games.
import { createDevboxClient } from "@namespacelabs/sdk/devbox";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url)), REPO = resolve(HERE, "..");
const args = process.argv.slice(2);
const action = args[0], count = Number(args[1]);
const flag = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const PREFIX = flag("--prefix", "fly-mac"), SIZE = flag("--size", "m"), RES = flag("--res", "1600x1200");
const log = (m) => console.log(`${new Date().toISOString().slice(11, 19)} ${m}`);
const OUT = join(REPO, "results/live-view"); mkdirSync(OUT, { recursive: true });

const client = createDevboxClient();
async function ready(d) {
  for (let i = 0; i < 60; i++) {
    try { return (await d.shell("echo $HOME", { timeoutMs: 20000 })).stdout.trim(); } catch { await new Promise((r) => setTimeout(r, 5000)); }
  }
  throw new Error(`${d.name}: not ready`);
}
async function getOrCreate(name) {
  try { const d = await client.devboxes.get(name); if (d.info.state !== "running") await d.start(); log(`${name}: reusing`); return d; }
  catch (e) { if (e?.code !== 5) throw e; }
  const d = await client.devboxes.create({ name, os: "macos", size: SIZE, versionControl: {}, purpose: "namespace-fly: Live view wall" });
  log(`${name}: created (${d.id})`);
  return d;
}
async function bringUp(name, index) {
  const d = await getOrCreate(name);
  const home = await ready(d);
  const repo = `${home}/namespace-fly`, fly = `${home}/fly`;
  await d.shell(`mkdir -p ${repo} ${home}/fly-out; boxctl task mark fly-wall || true`);   // a background game loop is not 'activity': hold the box awake
  for (const f of ["fly_sim.py", "run_candidate.py", "live.html", "conditions.json", "shams.json"]) await d.fs.upload(join(REPO, f), `${repo}/${f}`);
  for (const f of ["mac_setup.sh", "mac_loop.sh"]) await d.fs.upload(join(HERE, f), `${repo}/${f}`);
  const t0 = Date.now();
  const setup = await d.shell(`bash ${repo}/mac_setup.sh 2>&1 | tail -1`);
  if (!setup.stdout.includes("SETUP_OK")) throw new Error(`${name}: setup failed: ${setup.stdout.slice(-400)}`);
  log(`${name}: DOOMFLY ready in ${Math.round((Date.now() - t0) / 1000)} s`);
  const seed = 41027 + index;
  await d.shell(`pkill -f mac_loop.sh; pkill -f run_candidate.py; sleep 1; (nohup bash ${repo}/mac_loop.sh ${fly} ${repo} ${seed} ${RES} > ${home}/fly-out/loop.log 2>&1 &); echo started`);
  log(`${name}: game loop started (seed ${seed})`);
  return d;
}

try {
  if (action === "up" && count > 0) {
    const names = Array.from({ length: count }, (_, i) => `${PREFIX}-${String(i + 1).padStart(2, "0")}`);
    const results = await Promise.allSettled(names.map((n, i) => bringUp(n, i)));
    const failed = results.filter((r) => r.status === "rejected");
    for (const f of failed) log(`FAILED: ${f.reason?.message ?? f.reason}`);
    log(`${results.length - failed.length} of ${names.length} boxes playing. Open the dashboard: Instances -> Live.`);
    if (failed.length) process.exitCode = 1;
  } else if (action === "shots") {
    for (const d of (await client.devboxes.list({ limit: 100 })).items) {
      if (!d.name.startsWith(PREFIX + "-")) continue;
      const h = await client.devboxes.get(d.name);
      const shot = await h.display.screenshot({ timeoutMs: 60000 });
      writeFileSync(join(OUT, `${d.name}.png`), shot.png);
      log(`${d.name}: ${shot.width}x${shot.height} -> results/live-view/${d.name}.png`);
    }
  } else if (action === "down") {
    for (const d of (await client.devboxes.list({ limit: 100 })).items)
      if (d.name.startsWith(PREFIX + "-")) { await client.devboxes.delete(d.id); log(`${d.name}: deleted`); }
  } else {
    console.error("usage: node mac_wall.mjs up <count> | shots | down   [--prefix fly-mac] [--size m] [--res 1600x1200]");
    process.exitCode = 2;
  }
} finally {
  client.close();
}
