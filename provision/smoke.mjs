// One-box smoke test of the SDK path: blueprint -> devbox -> fly-check -> one 3 s run -> delete.
import { createDevboxClient } from "@namespacelabs/sdk/devbox";
import { readFileSync } from "node:fs";
const spec = JSON.parse(readFileSync(new URL("../experiments/repro-93.json", import.meta.url), "utf8"));
const client = createDevboxClient();
let d;
try {
  try { const bp = await client.blueprints.get(spec.blueprint); console.log("blueprint exists v" + bp.version); }
  catch (err) {
    if (err?.code !== 5) throw err;
    await client.blueprints.create(spec.blueprint, { image: "builtin:base", size: spec.size, description: spec.description });
    const rpc = client.blueprints.rpc;
    const { template } = await rpc.fetchTemplate({ name: spec.blueprint });
    template.spec.instance.linux.imageRef = ""; template.spec.instance.linux.imageName = spec.image;
    await rpc.updateTemplate({ id: template.id, spec: template.spec });
    const bp = await client.blueprints.get(spec.blueprint);
    console.log("blueprint created:", bp.name, "v" + String(bp.version));
  }
  const t0 = Date.now();
  d = await client.devboxes.create({ name: "fly-smoke", blueprint: spec.blueprint, purpose: "namespace-fly smoke test" });
  console.log("created", d.name, d.id, "state", d.info.state, "in", Math.round((Date.now() - t0) / 1000), "s");
  let out;
  for (let i = 0; i < 60; i++) {
    try { out = await d.shell("fly-check", { timeoutMs: 20000 }); if (out.exitCode === 0) break; } catch (e) { out = { stderr: String(e) }; }
    await new Promise((r) => setTimeout(r, 5000));
  }
  console.log("fly-check after", Math.round((Date.now() - t0) / 1000), "s:\n" + (out.stdout || out.stderr));
  const envr = await d.shell("echo FLY_DOOMFLY=$FLY_DOOMFLY FLY_VENV=$FLY_VENV; nproc; free -g | sed -n 2p; df -h /workspaces | tail -1");
  console.log(envr.stdout.trim());
  await d.shell("mkdir -p /workspaces/namespace-fly");
  for (const f of ["fly_sim.py", "run_condition.py", "conditions.json", "stimuli.json", "shams.json"])
    await d.fs.upload(new URL("../" + f, import.meta.url).pathname, "/workspaces/namespace-fly/" + f);
  const run = await d.shell("mkdir -p /workspaces/w && cd /workspaces/w && /opt/fly/venv/bin/python /workspaces/namespace-fly/run_condition.py --condition dnpe017-off --doomfly /opt/fly/doomfly --seconds 3 --warmup 1 --out /workspaces/o 2>&1 | tail -1 | cut -c1-200");
  console.log("run:", run.stdout.trim());
} finally {
  if (d) { await d.delete(); console.log("deleted", d.name); }
  client.close();
}
