# Contributing

Thanks for helping improve `blender-chatgpt-mcp`.

## Development

Use Node.js 20 or later.

```bash
npm ci
npm run check
npm run build
npm run package:addon
```

Run Blender 5.1+ smoke tests when Blender is installed locally:

```bash
npm run test:blender
```

## Safety Rules

- Do not add OpenAI API calls or `OPENAI_API_KEY` requirements.
- Do not commit `.env`, bridge tokens, Codex auth files, ChatGPT access tokens, API keys, rendered previews, `.blend` scene outputs, or `dist/`.
- Keep Blender operations allowlisted and typed. Do not add generic Python execution, shell execution, arbitrary `bpy.ops` dispatch, or unrestricted file paths.
- Keep compatibility work focused on Blender 5.1+ unless the project explicitly adds another supported version range.
- Keep the default network bind to loopback addresses.

## Pull Requests

Describe what changed, why it changed, and which checks you ran. Include screenshots or preview renders only when they are small and intentionally added as documentation assets.
