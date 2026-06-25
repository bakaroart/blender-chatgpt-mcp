# blender-chatgpt-mcp Agent Notes

## Architecture

Codex connects directly to the local TypeScript Streamable HTTP MCP server at `127.0.0.1:3000/mcp`; ChatGPT connector setups can reach the same endpoint through Secure MCP Tunnel. The MCP server validates tool inputs with Zod, sends authenticated JSON envelopes to the Blender bridge at `127.0.0.1:8765`, and returns MCP `structuredContent` plus concise text. The Blender add-on runs a standard-library `ThreadingHTTPServer`; HTTP worker threads authenticate, parse, validate, and enqueue only. Blender API calls happen from the `bpy.app.timers` queue drain on Blender's main thread.

## Commands

- `npm install`
- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run lint`
- `npm run typecheck`
- `npm test`
- `npm run test:integration`
- `npm run test:blender`
- `npm run package:addon`
- `npm run check`

## Coding Conventions

- Keep TypeScript strict and avoid `any`.
- Keep pure Python modules importable without `bpy`.
- Use fixed operation names and typed schemas only.
- Target Blender 5.1+ behavior; do not claim older Blender compatibility without tests.
- Prefer Blender data APIs; use `bpy.ops` only for narrow operations that need Blender context.
- Keep bridge responses structured and stable.

## Security Invariants

- No arbitrary Python, shell, Blender operator, module, property-path, or generic attribute execution.
- Bridge binds only to `127.0.0.1`.
- MCP defaults to `127.0.0.1`; non-loopback bind is development-only and unsupported for public deployment.
- Every bridge command requires a bearer token compared with constant-time comparison.
- File writes stay under the configured Blender project root.
- Do not log tokens, raw environment values, base64 image bodies, prompt text, or full scene dumps.
- Mutations are never retried automatically after ambiguous failures.
- Do not add OpenAI API calls or `OPENAI_API_KEY` requirements. Codex usage should work through ChatGPT/Codex sign-in and plan quota; `BLENDER_BRIDGE_TOKEN` is only a local bridge token.

## Tests

Run `npm run check` before completion. Run `npm run test:blender` when Blender is installed and discoverable. The integration tests bind a temporary localhost fake bridge; sandboxed environments may need permission for localhost listen.
