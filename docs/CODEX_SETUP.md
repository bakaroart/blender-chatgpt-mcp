# Codex Setup

Use this path when you want Blender tools inside Codex using your Codex/ChatGPT plan quota instead of OpenAI Platform API billing.

## Authentication

Sign in to Codex with ChatGPT. Do not configure an OpenAI API key for this project, and do not add `OPENAI_API_KEY` to `.env`.

The only required secret is `BLENDER_BRIDGE_TOKEN`, generated in Blender Preferences by the add-on. It authenticates the local MCP server to the local Blender bridge.

## Local MCP Endpoint

Start Blender, start the Blender bridge, then start the MCP server:

```bash
npm run start
```

The server exposes Streamable HTTP MCP at:

```text
http://127.0.0.1:3000/mcp
```

## Codex Configuration

Codex supports Streamable HTTP MCP servers. Configure the local endpoint in your current Codex MCP configuration. For the CLI and IDE extension, that configuration is typically `~/.codex/config.toml`, or `.codex/config.toml` inside a trusted project.

```toml
[mcp_servers.blender_chatgpt]
url = "http://127.0.0.1:3000/mcp"
startup_timeout_sec = 20
tool_timeout_sec = 120
default_tools_approval_mode = "prompt"
```

Use `/mcp` in the Codex TUI to check whether the server is active. Keep mutating tools in prompt or approval mode until you are comfortable with the workflow.

## Readiness Checks

```bash
curl http://127.0.0.1:3000/healthz
curl http://127.0.0.1:3000/readyz
curl http://127.0.0.1:8765/healthz
```

`/readyz` returns `BRIDGE_UNAVAILABLE` until Blender is open and the add-on bridge is running.
