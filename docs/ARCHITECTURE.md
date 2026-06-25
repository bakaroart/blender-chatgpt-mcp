# Architecture

The integration has two local components.

1. The Blender add-on starts an authenticated HTTP JSON bridge bound to `127.0.0.1`. It uses Python standard-library networking only.
2. The TypeScript MCP server exposes Streamable HTTP at `/mcp`, validates tool input with Zod, calls the bridge with bearer authentication, and returns MCP `structuredContent`.

The Blender add-on targets Blender 5.1 or newer. Older Blender 3.x and 4.x releases are not part of the supported compatibility surface.

Blender Lab also publishes a general MCP server for Blender. This project deliberately takes a narrower approach: fixed tools, typed schemas, bounded file writes, and no arbitrary Python execution.

Codex can connect directly to the local Streamable HTTP MCP endpoint. ChatGPT connector setups can reach the same endpoint through Secure MCP Tunnel. In both modes, this project does not call OpenAI Platform APIs and does not use `OPENAI_API_KEY`; model usage and quota belong to the Codex or ChatGPT surface that invokes the MCP tools.

HTTP bridge worker threads never call `bpy`. They authenticate, parse bounded JSON, validate request envelopes, enqueue jobs, and wait. A `bpy.app.timers` callback runs on Blender's main thread and drains the command queue into fixed dispatcher functions.

The protocol version is `1.0.0`. TypeScript and Python maintain matching conceptual schemas and stable error codes.

`blender_batch_operations` is intentionally omitted in v1. Reliable rollback cannot be claimed across supported Blender versions without deeper undo-stack testing, and the brief allows omitting the batch tool when safe rollback is not demonstrably implemented.
