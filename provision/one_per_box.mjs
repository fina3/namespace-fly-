// One run per Devbox: every variation of an experiment gets its own fresh Devbox, which is created
// from the pre-baked fly/doomfly image, runs exactly one simulation, hands back its result files and
// is deleted. 100 variations = 100 Devboxes.
//
//   node one_per_box.mjs ../experiments/knockouts-100.json [--concurrency 100] [--size s] [--only 3]
//
// Concurrency is how many boxes may exist at once. When Namespace refuses a creation with
// "per-user devbox limit reached", the script waits for a box to finish and retries, so with the
// current limit of 10 it runs in waves of 10; raise the limit and the same command runs all 100
// at once. Resumable: runs whose summary.json already exists are skipped.
//
// Needs experiments/<name>/shams.json from an earlier run of provision.mjs (sham pairs are selected
// from the connectome graph on a box; here every job must be independent).
import { createDevboxClient } from "@namespacelabs/sdk/devbox";
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url)), REPO = resolve(HERE, "..");
const args = process.argv.slice(2);
const specPath = args.find((a) => !a.startsWith("--"));
if (!specPath) { console.error("usage: node one_per_box.mjs <experiment.json> [--concurrency N] [--size s] [--only N]"); process.exit(2); }
const flag = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const spec = JSON.parse(readFileSync(specPath, "utf8"));
const CONCURRENCY = Number(flag("--concurrency", 100)), SIZE = flag("--size", "s"), ONLY = Number(flag("--only", 0));
const SRC = resolve(REPO, "experiments", spec.name);                 // where shams.json lives
const EXP = resolve(REPO, "experiments", `${spec.name}-1perbox`);     // where results go
const REMOTE = "/workspaces/namespace-fly", OUT = "/workspaces/fly-out";
const log = (box, m) => console.log(`${new Date().toISOString().slice(11, 19)} ${box ? `[${box}] ` : ""}${m}`);

// ---------------------------------------------------------------- jobs
const shamsPath = join(SRC, "shams.json");
if (!existsSync(shamsPath)) { console.error(`missing ${shamsPath}: run provision.mjs for this experiment first (it selects the sham pairs)`); process.exit(2); }
mkdirSync(join(EXP, "results"), { recursive: true });
for (const f of ["stimuli.json", "conditions.json", "shams.json", "neuron_types.npz"]) {
  const from = f === "conditions.json" ? join(REPO, f) : f === "stimuli.json" ? null : join(SRC, f);
  if (from) writeFileSync(join(EXP, f), readFileSync(from));
}
writeFileSync(join(EXP, "stimuli.json"), JSON.stringify(spec.stimuli, null, 2) + "\n");
const conditions = Object.keys(JSON.parse(readFileSync(join(REPO, "conditions.json"), "utf8")));
const shams = Object.keys(JSON.parse(readFileSync(shamsPath, "utf8")));
let jobs = [];
for (const s of Object.keys(spec.stimuli)) for (const arm of [...conditions, ...shams]) jobs.push({ stim: s, arm });
jobs = jobs.map((j, i) => ({ ...j, n: i + 1, box: `${spec.name}-r${String(i + 1).padStart(3, "0")}` }));
if (ONLY) jobs = jobs.slice(0, ONLY);
const todo = jobs.filter((j) => !existsSync(join(EXP, "results", j.stim, j.arm, "summary.json")));
log("", `${jobs.length} runs, ${jobs.length - todo.length} already done, ${todo.length} to run, up to ${CONCURRENCY} boxes at once, size ${SIZE}`);

// ---------------------------------------------------------------- one job = one box
const client = createDevboxClient();
const env = { FLY_DOOMFLY: "/opt/fly/doomfly", FLY_VENV: "/opt/fly/venv", FLY_REPO: REMOTE, FLY_OUT: OUT, SECS: String(spec.seconds), PAR: "1" };
const codeCommit = spawnSync("git", ["-C", REPO, "rev-parse", "HEAD"], { encoding: "utf8" }).stdout.trim();
const provenance = [];
let limitHits = 0;

async function createWithRetry(job) {
  for (;;) {
    try {
      return await client.devboxes.create({ name: job.box, imageName: spec.image, size: SIZE, versionControl: {}, purpose: `namespace-fly ${spec.name}: ${job.stim} ${job.arm}` });
    } catch (e) {
      if (!/devbox limit reached/.test(e.rawMessage ?? e.message ?? "")) throw e;
      if (limitHits++ === 0) log(job.box, "account box limit reached; continuing in waves as boxes free up");
      await new Promise((r) => setTimeout(r, 15000));
    }
  }
}

async function sh(d, script, opts = {}) {
  const r = await d.shell(script, { env, ...opts });
  if (r.exitCode !== 0) throw new Error(`[${d.name}] exit ${r.exitCode}: ${(r.stderr || r.stdout).trim().slice(-300)}`);
  return r.stdout;
}

async function runJob(job) {
  const t0 = Date.now();
  let d;
  try {
    try { d = await client.devboxes.get(job.box); await d.delete(); } catch {}   // a leftover from an interrupted run
    d = await createWithRetry(job);
    for (let i = 0; ; i++) {
      try { await sh(d, "fly-check >/dev/null", { timeoutMs: 20000 }); break; }
      catch { if (i > 60) throw new Error("not ready"); await new Promise((r) => setTimeout(r, 5000)); }
    }
    const tReady = Date.now();
    await sh(d, `mkdir -p ${REMOTE} ${OUT}`);
    for (const f of ["fly_sim.py", "run_condition.py", "run_batch.sh", "conditions.json"]) await d.fs.upload(join(REPO, f), `${REMOTE}/${f}`);
    for (const f of ["stimuli.json", "shams.json"]) await d.fs.upload(join(EXP, f), `${REMOTE}/${f}`);
    const jobsFile = join(tmpdir(), `${job.box}.txt`);
    writeFileSync(jobsFile, `${job.stim} ${job.arm}\n`);
    await d.fs.upload(jobsFile, `${OUT}/job.txt`);
    await sh(d, `bash ${REMOTE}/run_batch.sh ${OUT}/job.txt`);
    await sh(d, `cd ${OUT} && tar -czf run.tgz results`);
    const local = join(tmpdir(), `${job.box}.tgz`);
    await d.fs.download(`${OUT}/run.tgz`, local);
    execFileSync("tar", ["-xzf", local, "-C", EXP]);
    rmSync(local); rmSync(jobsFile);
    provenance.push({ run: `${job.stim}/${job.arm}`, devbox: job.box, id: d.id, size: SIZE, ready_s: Math.round((tReady - t0) / 1000), total_s: Math.round((Date.now() - t0) / 1000) });
    log(job.box, `${job.stim} ${job.arm}: done in ${Math.round((Date.now() - t0) / 1000)} s (box ready after ${Math.round((tReady - t0) / 1000)} s)`);
  } finally {
    if (d) { try { await d.delete(); } catch (e) { log(job.box, `delete failed: ${e.message}`); } }
  }
}

// ---------------------------------------------------------------- pool
const failures = [];
let next = 0;
async function worker() {
  while (next < todo.length) {
    const job = todo[next++];
    try { await runJob(job); } catch (e) { failures.push(`${job.stim}/${job.arm}: ${e.message}`); log(job.box, `FAILED: ${e.message}`); }
  }
}
try {
  const t0 = Date.now();
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, todo.length) }, worker));
  writeFileSync(join(EXP, "provenance.json"), JSON.stringify({ experiment: spec, mode: "one run per devbox", concurrency: CONCURRENCY, size: SIZE,
    code_commit: codeCommit, runs: provenance, failures, finished_at: new Date().toISOString() }, null, 2) + "\n");
  log("", `${provenance.length} runs on ${provenance.length} devboxes in ${Math.round((Date.now() - t0) / 60000)} min; ${failures.length} failed`);
  if (!ONLY && !failures.length) {
    for (const script of ["verify_results.py", "compare.py"]) {
      const r = spawnSync("python3", [join(REPO, script)], { env: { ...process.env, FLY_ROOT: EXP }, encoding: "utf8" });
      log("", `${script}: ${r.status === 0 ? "ok" : "FAILED"} ${(r.stdout + r.stderr).trim().split("\n").slice(-1)[0]}`);
    }
  }
  if (failures.length) process.exitCode = 1;
} finally {
  client.close();
}
