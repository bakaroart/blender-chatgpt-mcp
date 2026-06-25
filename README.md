# blender-chatgpt-mcp

Control a local Blender scene from Codex or ChatGPT through MCP.

This project lets an AI assistant inspect your open Blender scene, create objects, edit materials, set cameras and lights, render previews, and save safe copies of your `.blend` file. Everything runs on your own computer.

## Read This First

- You do not need an OpenAI API key.
- Do not put `OPENAI_API_KEY` in this project.
- Do not put any ChatGPT, Codex, or OpenAI account token in this project.
- The only token this project uses is `BLENDER_BRIDGE_TOKEN`. It is a local password between the MCP server and Blender on your own computer.
- The default setup uses `127.0.0.1`, which means your own machine only.

For Codex, sign in with ChatGPT so usage follows your Codex/ChatGPT plan quota. This project does not call the OpenAI Platform API.

## What You Are Installing

There are two local pieces:

1. A Blender add-on that opens a private local bridge inside Blender.
2. A small Node.js MCP server that Codex or ChatGPT can talk to.

The path looks like this:

```text
Codex
  -> local MCP server at http://127.0.0.1:3000/mcp
  -> local Blender bridge at http://127.0.0.1:8765
  -> Blender
```

Optional ChatGPT connector setups can use Secure MCP Tunnel, but Codex local setup does not need a tunnel.

## How This Relates To Blender Lab MCP

Blender also has a Blender Lab MCP Server:

```text
https://www.blender.org/lab/mcp-server/
```

That project is a powerful general-purpose MCP server for exploring Blender through the Python API. Blender's own page warns that it can execute LLM-generated code in Blender without guards.

This project is intentionally more conservative. It exposes fixed tools with typed inputs, bounded file access, localhost-only defaults, and no arbitrary Python or shell execution. Use Blender Lab MCP when you want broad Python API exploration. Use this project when you want a safer Codex-oriented local bridge for common scene operations.

## What You Need

Install these first:

- Blender 5.1 or newer
- Node.js 20 or newer
- Codex CLI or Codex IDE extension, signed in with ChatGPT

This project targets Blender 5.1 or newer and is tested with Blender 5.1.2. Older Blender 3.x and 4.x releases are not supported.

On macOS, Blender is usually installed at `/Applications/Blender.app`. The helper scripts can find that automatically.

## Download This Project

If you are using Git:

```bash
git clone https://github.com/bakaroart/blender-chatgpt-mcp.git
cd blender-chatgpt-mcp
```

If you downloaded a ZIP from GitHub, unzip it, then open Terminal in the unzipped folder.

## Step 1: Install Project Dependencies

Run this once:

```bash
npm install
```

Then build the server and package the Blender add-on:

```bash
npm run build
npm run package:addon
```

This creates:

```text
dist/blender_chatgpt_bridge.zip
```

## Step 2: Install The Blender Add-On

Open Blender.

In Blender:

1. Open Preferences.
2. Go to Add-ons.
3. Choose Install from Disk.
4. Select `dist/blender_chatgpt_bridge.zip`.
5. Enable `Blender MCP Bridge`.

Then open the add-on preferences:

1. Set Project Root to this project folder.
2. Click Generate Token.
3. Click Copy Token.

Keep Blender open.

## Step 3: Create Your Local `.env` File

In the project folder, copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` in any text editor. On macOS, this works:

```bash
open -e .env
```

Find this line:

```text
BLENDER_BRIDGE_TOKEN=replace-with-token-generated-in-blender
```

Replace `replace-with-token-generated-in-blender` with the token you copied from Blender.

Do not add `OPENAI_API_KEY`. Do not add any OpenAI account secret.

Save the file.

## Step 4: Start The Blender Bridge

You can start the bridge from Blender or from Terminal.

### Option A: Start From Blender

In Blender:

1. Open the 3D View sidebar.
2. Open the MCP Bridge tab.
3. Click Start MCP Bridge.

### Option B: Start From Terminal

On macOS, you can also run:

```bash
npm run bridge:blender
```

This opens Blender and starts the bridge using the token in `.env`.

## Step 5: Start The MCP Server

Open a second Terminal window in the project folder and run:

```bash
npm run start
```

Leave this Terminal window open while you use Blender from Codex or ChatGPT.

## Step 6: Check That Everything Is Connected

Open another Terminal window and run:

```bash
curl http://127.0.0.1:3000/healthz
curl http://127.0.0.1:3000/readyz
curl http://127.0.0.1:8765/healthz
```

Good signs:

- `/healthz` says the MCP server is running.
- `/readyz` says the Blender bridge is available and authenticated.
- Blender bridge `/healthz` says the bridge is running.

If `/readyz` says `BRIDGE_UNAVAILABLE`, start the bridge in Blender.

If `/readyz` says authentication failed, copy the token from Blender into `.env` again and restart `npm run start`.

## Step 7: Connect Codex

This repository includes a project-scoped Codex config at:

```text
.codex/config.toml
```

It points Codex to:

```text
http://127.0.0.1:3000/mcp
```

Start a new Codex session in this project folder so Codex loads the config. In the Codex terminal UI, run:

```text
/mcp
```

You should see the Blender MCP server listed.

If Codex does not load the project config, copy this into your Codex `config.toml`:

```toml
[mcp_servers.blender_chatgpt]
url = "http://127.0.0.1:3000/mcp"
startup_timeout_sec = 20
tool_timeout_sec = 120
default_tools_approval_mode = "prompt"
```

For many Codex installs, the user config file is:

```text
~/.codex/config.toml
```

## Step 8: Try It In Codex

With Blender open, the Blender bridge running, and `npm run start` still running, ask Codex something like:

```text
Use the Blender MCP tools to inspect the scene, create a blue cube, add a camera and light, render a preview, and save a copy.
```

Keep tool approval set to prompt mode at first. This gives you a chance to review actions before Codex changes Blender.

## Optional: Run The Built-In Demo

After Blender and the MCP server are running:

```bash
npm run demo:mcp
```

For a larger scene:

```bash
npm run showcase:mcp
```

These commands use the same MCP tools Codex uses. They create objects, render a preview, and save a `.blend` copy under `dist/`.

## Optional: Use With ChatGPT Connector

Codex local setup is the simplest path. ChatGPT connector setup is optional and requires whatever ChatGPT developer/custom connector capability is available to your account or workspace.

For ChatGPT connector setups, forward this local MCP endpoint through Secure MCP Tunnel:

```text
http://127.0.0.1:3000/mcp
```

Then create or refresh the ChatGPT connector and review the exposed Blender tools. Product UI labels can change, so use the current official ChatGPT connector instructions for your account.

## What The Tools Can Do

The MCP server exposes fixed, typed Blender tools for:

- Getting Blender status and scene summaries
- Creating primitives like cubes, planes, spheres, cylinders, cones, and torus meshes
- Duplicating, renaming, transforming, hiding, and deleting exact object names
- Creating and assigning materials
- Creating and updating lights
- Creating or updating cameras
- Setting world background
- Rendering bounded previews
- Saving safe `.blend` copies under the configured project root

The server does not expose arbitrary Python execution, shell execution, unrestricted file access, generic Blender operator dispatch, or wildcard object deletion.

## Stopping Everything

To stop the MCP server, press `Ctrl+C` in the Terminal window running:

```bash
npm run start
```

To stop the Blender bridge, either click Stop MCP Bridge in Blender or close Blender.

## Updating Later

After pulling a new version from GitHub:

```bash
npm install
npm run build
npm run package:addon
```

Then reinstall `dist/blender_chatgpt_bridge.zip` in Blender.

## Troubleshooting

### `npm install` fails

Make sure Node.js 20 or newer is installed:

```bash
node --version
```

### Blender cannot be found

On macOS, install Blender in `/Applications`. If Blender is somewhere else, set `BLENDER_BIN` to the Blender executable path before running helper scripts.

### `/readyz` says `BRIDGE_UNAVAILABLE`

Blender is not reachable. Open Blender and start the MCP Bridge from the sidebar, or run:

```bash
npm run bridge:blender
```

### `/readyz` says authentication failed

The token in `.env` does not match Blender. Generate or copy the token from Blender again, paste it into `.env`, save the file, and restart:

```bash
npm run start
```

### Codex does not show the Blender server

Restart Codex in this project folder, then run:

```text
/mcp
```

If it still does not appear, copy the MCP config block from Step 7 into `~/.codex/config.toml`.

### Preview rendering fails

Try a smaller render size or fewer samples. The preview tool intentionally has size and timeout limits.

## Development Commands

For contributors:

```bash
npm run lint
npm run typecheck
npm test
npm run test:integration
npm run check
```

Run Blender smoke tests when Blender is installed:

```bash
npm run test:blender
```

## Public Repository Safety

The following files and folders should not be committed:

- `.env`
- `dist/`
- `node_modules/`
- rendered previews
- personal `.blend` outputs
- Codex or ChatGPT auth files
- OpenAI API keys or access tokens

The included `.gitignore` already ignores the common local outputs.

## More Documentation

- [Codex setup](docs/CODEX_SETUP.md)
- [Blender add-on installation](docs/INSTALL_BLENDER_ADDON.md)
- [Tool reference](docs/TOOL_REFERENCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security details](docs/SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
