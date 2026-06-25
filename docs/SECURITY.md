# Security

## Threat Model

The model can produce untrusted arguments. The connector controls a local desktop application, so every input is treated as hostile until validated.

## Trust Boundaries

- Codex, ChatGPT, and MCP tool arguments are untrusted.
- The local MCP server is trusted only to validate and forward typed operations.
- The Blender bridge validates again before queuing operations.
- Blender's `bpy` API is reached only on Blender's main thread.

## Controls

- No arbitrary code execution: no Python source, shell source, Blender operator names, module names, property paths, arbitrary attributes, eval, exec, terminal, or command tools.
- Localhost only: Blender bridge binds to `127.0.0.1`; MCP defaults to `127.0.0.1`.
- Bridge token: high-entropy bearer token, constant-time comparison, never logged.
- Secure MCP Tunnel: exposes the local MCP endpoint to ChatGPT without making Blender public.
- File sandbox: save-copy targets are relative `.blend` paths under the configured project root, with symlink and traversal checks.
- Resource limits: request size, object count, material slots, preview dimensions, samples, timeouts, queue depth, and image payload size are bounded.
- Destructive tools: deletion and modifier removal are separate tools, annotated destructive, validate exact names, and push undo checkpoints where supported.
- Logging: structured audit lines include request ID, operation, duration, success/failure, and sanitized code only.
- No OpenAI API key: do not put `OPENAI_API_KEY` in `.env`; the Blender token is a local bridge secret, not a model credential.

## Prompt Injection

Scene names, object names, material names, and file names can contain misleading text. The MCP server instructions tell the model to inspect first, use exact names, and trust only successful tool results.

## Unsupported

Public hosting, shared multi-user deployment, OAuth delegation, and production authorization are not implemented in the MVP. Rotate the Blender token after suspected exposure.
