// Live-view test: one macOS Devbox, DOOMFLY installed, a fly brain playing Doom with the real game
// window on the box's screen, captured through the SDK display API (which is what the dashboard's
// Live grid shows). Namespace compute only; no Anthropic API.
//
//   node mac_display_test.mjs [--name fly-mac-01] [--size m] [--keep]
import { createDevboxClient } from "@namespacelabs/sdk/devbox";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..");
const args = process.argv.slice(2);
const flag = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const NAME = flag("--name", "fly-mac-01"), SIZE = flag("--size", "m"), KEEP = args.includes("--keep");
const OUT = join(REPO, "results/live-view"); mkdirSync(OUT, { recursive: true });
const log = (m) => console.log(`${new Date().toISOString().slice(11, 19)} ${m}`);

const client = createDevboxClient();
let d;
try {
  try { d = await client.devboxes.get(NAME); if (d.info.state !== "running") await d.start(); log(`reusing ${NAME}`); }
  catch (e) { if (e?.code !== 5) throw e; d = await client.devboxes.create({ name: NAME, os: "macos", size: SIZE, versionControl: {}, purpose: "namespace-fly: Live view test" }); log(`created ${NAME} (${d.id})`); }

  // wait for the agent, then look at the machine
  let info;
  for (let i = 0; ; i++) {
    try { info = (await d.shell("sw_vers -productVersion; uname -m; sysctl -n hw.ncpu; xcode-select -p; echo HOME=$HOME", { timeoutMs: 20000 })).stdout; break; }
    catch { if (i > 60) throw new Error("not ready"); await new Promise((r) => setTimeout(r, 5000)); }
  }
  log(`box: ${info.trim().replace(/\n/g, " | ")}`);
  const home = info.match(/HOME=(\S+)/)[1];
  const fly = `${home}/fly`, repo = `${home}/namespace-fly`;

  // display before anything runs
  const shot0 = await d.display.screenshot({ timeoutMs: 60000 });
  writeFileSync(join(OUT, "mac-00-desktop.png"), shot0.png);
  log(`display ${shot0.width}x${shot0.height} "${shot0.desktopName}" -> results/live-view/mac-00-desktop.png`);

  // install DOOMFLY + our scripts
  await d.shell(`mkdir -p ${repo}`);
  for (const f of ["fly_sim.py", "run_candidate.py", "live.html", "conditions.json", "shams.json"]) await d.fs.upload(join(REPO, f), `${repo}/${f}`);
  await d.fs.upload(join(HERE, "mac_setup.sh"), `${repo}/mac_setup.sh`);
  const t0 = Date.now();
  const setup = await d.shell(`bash ${repo}/mac_setup.sh 2>&1 | tail -3`);
  log(`setup (${Math.round((Date.now() - t0) / 60000)} min): ${setup.stdout.trim().split("\n").pop()}`);
  if (!setup.stdout.includes("SETUP_OK")) throw new Error("setup failed: " + setup.stdout.slice(-800));

  // a visible closed-loop game: intact brain, 60 s cap, real-time pacing, launched into the console user's GUI session
  const cmd = `${fly}/venv/bin/python ${repo}/run_candidate.py --candidate-id 0 --game-seed 41027 --max-tics 2100 --doomfly ${fly}/doomfly --show-window --realtime --out ${home}/fly-out/runs`;
  await d.shell(`mkdir -p ${home}/fly-out && cd ${home}/fly-out && (nohup ${cmd} > ${home}/fly-out/run.log 2>&1 &) ; sleep 1; echo started`);
  log("game started; capturing screenshots");
  for (let i = 1; i <= 6; i++) {
    await new Promise((r) => setTimeout(r, 10000));
    const shot = await d.display.screenshot({ timeoutMs: 60000 });
    writeFileSync(join(OUT, `mac-${String(i).padStart(2, "0")}.png`), shot.png);
    const tail = (await d.shell(`tail -1 ${home}/fly-out/run.log | cut -c1-120`)).stdout.trim();
    log(`shot ${i}: ${shot.png.length} bytes | run: ${tail}`);
  }
  log(`box ${NAME} (${d.id}) is ${KEEP ? "left running for the dashboard Live view" : "being deleted"}`);
} finally {
  if (d && !KEEP) { await d.delete(); log("deleted"); }
  client.close();
}
