// Create or delete a set of Devboxes from the fly-doomfly Blueprint, for scripts that drive
// boxes by name with the devbox CLI (e.g. run_survival_search.py --devboxes ...).
//
//   node boxes.mjs create <prefix> <count>     -> <prefix>-01 ... <prefix>-NN, waits until fly-check passes
//   node boxes.mjs delete <prefix>             -> deletes every devbox whose name starts with <prefix>-
import { createDevboxClient } from "@namespacelabs/sdk/devbox";

const [action, prefix, count] = process.argv.slice(2);
if (!action || !prefix || (action === "create" && !count)) {
  console.error("usage: node boxes.mjs create <prefix> <count> | delete <prefix>");
  process.exit(2);
}
const client = createDevboxClient();
try {
  if (action === "create") {
    const names = Array.from({ length: Number(count) }, (_, i) => `${prefix}-${String(i + 1).padStart(2, "0")}`);
    const boxes = await Promise.all(names.map(async (name) => {
      const d = await client.devboxes.create({ name, blueprint: "fly-doomfly", purpose: `namespace-fly ${prefix}` });
      for (let i = 0; i < 90; i++) {
        try { if ((await d.shell("fly-check", { timeoutMs: 20000 })).exitCode === 0) return d; } catch {}
        await new Promise((r) => setTimeout(r, 5000));
      }
      throw new Error(`${name} not ready`);
    }));
    console.log(boxes.map((d) => d.name).join(","));
  } else if (action === "delete") {
    for (const d of (await client.devboxes.list({ limit: 100 })).items)
      if (d.name.startsWith(prefix + "-")) { await client.devboxes.delete(d.id); console.log("deleted", d.name); }
  } else {
    console.error("unknown action", action); process.exitCode = 2;
  }
} finally {
  client.close();
}
