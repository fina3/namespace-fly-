// Run a Claude Managed Agent session on a Namespace Devbox, from code.
//
// How the pieces fit: Namespace registers itself with Anthropic as a *self-hosted* Managed
// Agents environment (devbox claude managed-agents setup-environment). Anthropic runs the agent
// loop; when a session starts, Anthropic calls Namespace's webhook and Namespace provisions a
// Devbox where the agent's bash / file tools execute. This script does the Anthropic side:
// make sure an agent exists, start a session on that environment, send it a task, and stream
// the result.
//
//   export ANTHROPIC_API_KEY=...            (Console API key; the CLI setup does not store one for us)
//   node agent_session.mjs --environments    # list environments; find the Namespace one (type self_hosted)
//   node agent_session.mjs --env env_... "Run fly-check and report what the box contains"
//   node agent_session.mjs --env env_... --budget-usd 5 "Run run_condition.py --condition control --seconds 10 ..."
//
// Flags: --env <id> (or FLY_AGENT_ENVIRONMENT_ID), --agent-name <name>, --model <id>, --budget-usd <n>,
//        --workspace <slug> (for the Console trace link), --no-stream (print the session id and exit).
import Anthropic from "@anthropic-ai/sdk";

const args = process.argv.slice(2);
const flag = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const has = (name) => args.includes(name);
const task = args.filter((a, i) => !a.startsWith("--") && !["--env", "--agent-name", "--model", "--budget-usd", "--workspace"].includes(args[i - 1])).join(" ");

const client = new Anthropic();   // ANTHROPIC_API_KEY from the environment

if (has("--environments")) {
  for await (const env of client.beta.environments.list()) {
    console.log(`${env.id}  ${env.config?.type ?? "?"}  ${env.name}`);
  }
  process.exit(0);
}

const environmentId = flag("--env", process.env.FLY_AGENT_ENVIRONMENT_ID);
if (!environmentId || !task) {
  console.error("usage: node agent_session.mjs --env env_... \"task for the agent\"   (or --environments to list)");
  process.exit(2);
}

// ---------------------------------------------------------------- agent (created once, reused by name)
const AGENT_NAME = flag("--agent-name", "fly-brain-devbox-agent");
const MODEL = flag("--model", "claude-opus-5");
const SYSTEM = `You are an experiment runner working inside a Namespace Devbox.
If the box was created from the fly/doomfly image, the DOOMFLY fly-brain simulation is pre-installed:
  /opt/fly/doomfly   DOOMFLY at a pinned commit with the MaleCNS v1.0 data, graph and native kernel
  /opt/fly/venv      Python 3.11 with its pinned packages (use /opt/fly/venv/bin/python)
  fly-check          prints what the image contains and proves the kernel loads
The experiment scripts live in the namespace-fly repository (github.com/fina3/namespace-fly-): clone it if it
is not present. Run what you are asked, report the exact commands you ran and their output, and never
describe results you did not observe. Simulations describe the DOOMFLY model, not real flies.`;

async function ensureAgent() {
  for await (const a of client.beta.agents.list()) {
    if (a.name === AGENT_NAME) return a;
  }
  const a = await client.beta.agents.create({
    name: AGENT_NAME,
    model: MODEL,
    system: SYSTEM,
    description: "Runs fly-brain (DOOMFLY) experiments on Namespace Devboxes",
    tools: [{ type: "agent_toolset_20260401", default_config: { enabled: true } }],
  });
  console.log(`created agent ${a.id} v${a.version}`);
  return a;
}

// ---------------------------------------------------------------- session
const agent = await ensureAgent();
const budget = flag("--budget-usd");
const session = await client.beta.sessions.create({
  agent: { type: "agent", id: agent.id, version: agent.version },
  environment_id: environmentId,
  title: task.slice(0, 80),
  ...(budget ? { budget: { type: "limit", max_list_cost: { amount: String(Math.round(Number(budget) * 100)), currency: "USD" } } } : {}),
  initial_events: [{ type: "user.message", content: [{ type: "text", text: task }] }],
});
console.log(`session ${session.id} (${session.status}) on ${environmentId}`);
console.log(`trace: https://platform.claude.com/workspaces/${flag("--workspace", "default")}/sessions/${session.id}`);
if (has("--no-stream")) process.exit(0);

// ---------------------------------------------------------------- stream until the agent is done
const stream = await client.beta.sessions.events.stream(session.id);
const t0 = Date.now();
const stamp = () => `${String(Math.round((Date.now() - t0) / 1000)).padStart(4)}s`;
for await (const event of stream) {
  switch (event.type) {
    case "agent.message":
      for (const block of event.content) if (block.type === "text") console.log(`${stamp()} agent: ${block.text}`);
      break;
    case "agent.tool_use":
      console.log(`${stamp()} tool ${event.name}: ${JSON.stringify(event.input).slice(0, 200)}`);
      break;
    case "agent.tool_result": {
      const text = (event.content ?? []).map((b) => b.text ?? "").join("").trim();
      if (text) console.log(`${stamp()}   -> ${text.slice(0, 300).replace(/\n/g, "\n       ")}`);
      break;
    }
    case "session.status_running":
      console.log(`${stamp()} running (Namespace is bringing up the Devbox)`);
      break;
    case "session.status_idle":
      if (event.stop_reason?.type === "requires_action") { console.log(`${stamp()} waiting on an approval or custom tool result`); continue; }
      console.log(`${stamp()} done: ${event.stop_reason?.type}`);
      process.exit(0);
    case "session.status_terminated":
      console.log(`${stamp()} terminated`);
      process.exit(0);
    case "session.error":
      console.error(`${stamp()} error: ${JSON.stringify(event).slice(0, 400)}`);
      process.exit(1);
  }
}
