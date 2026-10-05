// Screenshot one box N times back to back (what a ~1 fps viewer sees). node mac_burst.mjs <box> [n]
import { createDevboxClient } from "@namespacelabs/sdk/devbox";
import { writeFileSync, mkdirSync } from "node:fs";
const [name, n = "4", tag = ""] = process.argv.slice(2);
const client = createDevboxClient();
mkdirSync("../results/live-view", { recursive: true });
try {
  const d = await client.devboxes.get(name);
  for (let i = 0; i < Number(n); i++) {
    const t0 = Date.now();
    const shot = await d.display.screenshot({ timeoutMs: 60000 });
    writeFileSync(`../results/live-view/${name}-burst${tag}-${i}.png`, shot.png);
    console.log(`shot ${i}: ${Date.now() - t0} ms`);
  }
} finally { client.close(); }
