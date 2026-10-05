// Start (or restart) the endless knockout demo loop on a macOS Devbox and grab one screenshot.
//   node mac_start_loop.mjs <devbox-name> [seed] [resolution]
import { createDevboxClient } from "@namespacelabs/sdk/devbox";
import { writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url)), REPO = resolve(HERE, "..");
const [name, seed = "41027", res = "1600x1200"] = process.argv.slice(2);
if (!name) { console.error("usage: node mac_start_loop.mjs <devbox-name> [seed] [resolution]"); process.exit(2); }

const client = createDevboxClient();
try {
  const d = await client.devboxes.get(name);
  if (d.info.state !== "running") { await d.start(); console.log(`started ${name}`); }
  const home = (await d.shell("echo $HOME", { timeoutMs: 120000 })).stdout.trim();
  // a background loop does not count as activity, so hold the box awake explicitly (cleared by mac_wall.mjs down / expire)
  await d.shell("boxctl task mark fly-wall || true");
  for (const f of ["run_candidate.py", "fly_sim.py"]) await d.fs.upload(join(REPO, f), `${home}/namespace-fly/${f}`);
  await d.fs.upload(join(HERE, "mac_loop.sh"), `${home}/namespace-fly/mac_loop.sh`);
  await d.shell(`pkill -f mac_loop.sh; pkill -f run_candidate.py; sleep 1; mkdir -p ${home}/fly-out; `
              + `(nohup bash ${home}/namespace-fly/mac_loop.sh ${home}/fly ${home}/namespace-fly ${seed} ${res} > ${home}/fly-out/loop.log 2>&1 &); echo started`);
  await new Promise((r) => setTimeout(r, 25000));
  const shot = await d.display.screenshot({ timeoutMs: 60000 });
  writeFileSync(join(REPO, "results/live-view", `${name}-loop.png`), shot.png);
  const tail = (await d.shell(`tail -2 ${home}/fly-out/loop-intact.log 2>/dev/null | cut -c1-160`)).stdout.trim();
  console.log(`loop running on ${name}; screenshot results/live-view/${name}-loop.png; log: ${tail}`);
} finally {
  client.close();
}
