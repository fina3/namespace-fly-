// Provision and run a whole fly-brain knockout experiment on Namespace Devboxes
// from one experiment file, using the Namespace SDK.
//
//   cd provision && npm install
//   node provision.mjs ../experiments/knockouts-100.json [--keep] [--boxes N]
//
// What it does, in order:
//   1. makes sure the Blueprint exists (pointing at the pre-baked fly/doomfly image)
//   2. creates the Devboxes in parallel (or reuses ones with the same names) and waits until they run
//   3. phase 1: every named condition x every stimulus, spread round-robin over the boxes
//   4. picks the sham pairs on the box that ran the s1 control (needs the connectome graph)
//   5. phase 2: every sham x every stimulus, spread over the boxes
//   6. pulls every result file back into experiments/<name>/results/, verifies, compares
//   7. deletes the Devboxes (unless --keep), always, even after a failure
//
// Each job is still one `run_condition.py` call via run_batch.sh, so results are the same
// kind of files as the hand-run experiment and compare.py / verify_results.py apply unchanged.
import { createDevboxClient } from "@namespacelabs/sdk/devbox";
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..");
const REMOTE_REPO = "/workspaces/namespace-fly";
const REMOTE_OUT = "/workspaces/fly-out";
const SHIP = ["fly_sim.py", "run_condition.py", "run_batch.sh", "select_shams.py", "conditions.json"];

// ---------------------------------------------------------------- arguments
const args = process.argv.slice(2);
const specPath = args.find((a) => !a.startsWith("--"));
if (!specPath) {
  console.error("usage: node provision.mjs <experiment.json> [--keep] [--boxes N]");
  process.exit(2);
}
const KEEP = args.includes("--keep");
const boxesArg = args.indexOf("--boxes");
const spec = JSON.parse(readFileSync(specPath, "utf8"));
const N = boxesArg >= 0 ? Number(args[boxesArg + 1]) : spec.devboxes;
const EXP = resolve(REPO, "experiments", spec.name);
const log = (box, msg) => console.log(`${new Date().toISOString().slice(11, 19)} ${box ? `[${box}] ` : ""}${msg}`);

mkdirSync(join(EXP, "results"), { recursive: true });
writeFileSync(join(EXP, "stimuli.json"), JSON.stringify(spec.stimuli, null, 2) + "\n");
writeFileSync(join(EXP, "conditions.json"), readFileSync(join(REPO, "conditions.json")));
if (!existsSync(join(EXP, "neuron_types.npz"))) writeFileSync(join(EXP, "neuron_types.npz"), readFileSync(join(REPO, "neuron_types.npz")));
const codeCommit = spawnSync("git", ["-C", REPO, "rev-parse", "HEAD"], { encoding: "utf8" }).stdout.trim();

// ---------------------------------------------------------------- jobs
const conditions = Object.keys(JSON.parse(readFileSync(join(REPO, "conditions.json"), "utf8")));
const stimuli = Object.keys(spec.stimuli);
// Phase 1 job 0 is "s1 control": the sham selection needs its neuron counts, and it lands on box 0.
const phase1 = [];
for (const s of stimuli) for (const c of conditions) phase1.push(`${s} ${c}`);
const split = (jobs) => Array.from({ length: N }, (_, i) => jobs.filter((_, j) => j % N === i));

// ---------------------------------------------------------------- SDK helpers
const client = createDevboxClient();
const env = { FLY_DOOMFLY: spec.doomfly ?? "/opt/fly/doomfly", FLY_VENV: spec.venv ?? "/opt/fly/venv",
              FLY_REPO: REMOTE_REPO, FLY_OUT: REMOTE_OUT, SECS: String(spec.seconds), PAR: String(spec.runs_per_box) };

async function ensureBlueprint() {
  const { blueprint: name, image, size } = spec;
  try {
    const bp = await client.blueprints.get(name);
    log("", `blueprint ${name} exists (v${bp.version})`);
    return;
  } catch (err) {
    if (err?.code !== 5) throw err; // 5 = not found
  }
  // SDK 1.4.0 sends any image containing "/" as a raw registry ref, so a Custom Image name
  // such as fly/doomfly would be pulled from Docker Hub. Create with a placeholder, then set
  // the spec's imageName field directly; the server resolves it to the latest optimized build.
  await client.blueprints.create(name, { image: "builtin:base", size, description: spec.description ?? "" });
  const rpc = client.blueprints.rpc;
  const { template } = await rpc.fetchTemplate({ name });
  template.spec.instance.linux.imageRef = "";
  template.spec.instance.linux.imageName = image;
  await rpc.updateTemplate({ id: template.id, spec: template.spec });
  log("", `blueprint ${name} created from image ${image}, size ${size}`);
}

async function getOrCreate(name) {
  try {
    const d = await client.devboxes.get(name);
    if (d.info.state !== "running") await d.start();
    boxes.push(d);
    log(name, `reusing existing devbox (${d.id})`);
    return d;
  } catch (err) {
    if (err?.code !== 5) throw err;
  }
  const d = await client.devboxes.create({ name, blueprint: spec.blueprint, purpose: `namespace-fly ${spec.name}` });
  boxes.push(d);
  log(name, `created (${d.id})`);
  return d;
}

async function sh(d, script, opts = {}) {
  const r = await d.shell(script, { env, ...opts });
  if (r.exitCode !== 0) throw new Error(`[${d.name}] exit ${r.exitCode}: ${(r.stderr || r.stdout).trim().slice(-400)}`);
  return r.stdout;
}

async function waitReady(d) {
  for (let i = 0; i < 90; i++) {
    try {
      const out = await sh(d, "fly-check", { timeoutMs: 20000 });
      log(d.name, out.trim().split("\n").pop());
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 5000));
    }
  }
  throw new Error(`${d.name}: not ready after 7.5 minutes`);
}

async function ship(d, files) {
  await sh(d, `mkdir -p ${REMOTE_REPO} ${REMOTE_OUT} && rm -rf ${REMOTE_OUT}/results ${REMOTE_OUT}/logs ${REMOTE_OUT}/work`);
  for (const [local, remote] of files) await d.fs.upload(local, remote);
}

async function runJobs(d, jobs, label) {
  if (!jobs.length) return;
  const local = join(tmpdir(), `fly-jobs-${d.name}-${label}.txt`);
  writeFileSync(local, jobs.join("\n") + "\n");
  await d.fs.upload(local, `${REMOTE_OUT}/jobs-${label}.txt`);
  const t0 = Date.now();
  const out = await sh(d, `bash ${REMOTE_REPO}/run_batch.sh ${REMOTE_OUT}/jobs-${label}.txt`);
  log(d.name, `${label}: ${out.trim().split("\n").pop()} in ${Math.round((Date.now() - t0) / 60000)} min`);
}

async function pull(d) {
  await sh(d, `cd ${REMOTE_OUT} && tar -czf results.tgz results`);
  const local = join(tmpdir(), `fly-results-${d.name}.tgz`);
  await d.fs.download(`${REMOTE_OUT}/results.tgz`, local);
  execFileSync("tar", ["-xzf", local, "-C", EXP]);
  rmSync(local);
}

// ---------------------------------------------------------------- main
const names = Array.from({ length: N }, (_, i) => `${spec.name}-${String(i + 1).padStart(2, "0")}`);
const boxes = [];
try {
  log("", `experiment ${spec.name}: ${stimuli.length} stimuli x (${conditions.length} conditions + ${spec.shams.pairs} shams) = `
         + `${stimuli.length * (conditions.length + spec.shams.pairs)} runs on ${N} devboxes, ${spec.runs_per_box} at a time each`);
  await ensureBlueprint();
  await Promise.all(names.map(getOrCreate));
  boxes.sort((a, b) => a.name.localeCompare(b.name));   // job 0 (s1 control) must land on box 01
  await Promise.all(boxes.map(waitReady));

  const shipped = SHIP.map((f) => [join(REPO, f), `${REMOTE_REPO}/${f}`]);
  shipped.push([join(EXP, "stimuli.json"), `${REMOTE_REPO}/stimuli.json`]);
  await Promise.all(boxes.map((d) => ship(d, shipped)));
  log("", `phase 1: ${phase1.length} runs`);
  await Promise.all(split(phase1).map((jobs, i) => runJobs(boxes[i], jobs, "main")));

  log(boxes[0].name, `selecting ${spec.shams.pairs} sham pairs (seed ${spec.shams.seed})`);
  await sh(boxes[0], `cd ${REMOTE_REPO} && ${env.FLY_VENV}/bin/python select_shams.py --doomfly ${env.FLY_DOOMFLY} `
                   + `--pairs ${spec.shams.pairs} --seed ${spec.shams.seed} --control-counts ${REMOTE_OUT}/results/s1/control/neuron_counts.npz`);
  await boxes[0].fs.download(`${REMOTE_REPO}/shams.json`, join(EXP, "shams.json"));
  await boxes[0].fs.download(`${REMOTE_REPO}/neuron_types.npz`, join(EXP, "neuron_types.npz"));
  const shams = Object.keys(JSON.parse(readFileSync(join(EXP, "shams.json"), "utf8")));
  await Promise.all(boxes.map((d) => d.fs.upload(join(EXP, "shams.json"), `${REMOTE_REPO}/shams.json`)));
  const phase2 = [];
  for (const sham of shams) for (const s of stimuli) phase2.push(`${s} ${sham}`);
  log("", `phase 2: ${phase2.length} sham runs`);
  await Promise.all(split(phase2).map((jobs, i) => runJobs(boxes[i], jobs, "sham")));

  await Promise.all(boxes.map(pull));
  writeFileSync(join(EXP, "provenance.json"), JSON.stringify({
    experiment: spec, code_commit: codeCommit, devboxes: boxes.map((d) => ({ name: d.name, id: d.id })),
    finished_at: new Date().toISOString() }, null, 2) + "\n");
  for (const script of ["verify_results.py", "compare.py"]) {
    const r = spawnSync("python3", [join(REPO, script)], { env: { ...process.env, FLY_ROOT: EXP }, encoding: "utf8" });
    log("", `${script}: ${r.status === 0 ? "ok" : "FAILED"} ${(r.stdout + r.stderr).trim().split("\n").slice(-1)[0]}`);
    if (r.status !== 0) process.exitCode = 1;
  }
  log("", `results in ${EXP}`);
} finally {
  if (KEEP) log("", `keeping ${boxes.length} devboxes (--keep)`);
  else await Promise.all(boxes.map(async (d) => { await d.delete(); log(d.name, "deleted"); }));
  client.close();
}
