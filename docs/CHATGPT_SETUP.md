# ChatGPT Setup

Use `docs/CODEX_SETUP.md` instead when your goal is local Codex usage with Codex/ChatGPT plan quota. This project does not require `OPENAI_API_KEY` for either path.

Use the current official OpenAI documentation for Apps SDK/MCP servers and Secure MCP Tunnel:

- https://developers.openai.com/apps-sdk/build/mcp-server
- https://developers.openai.com/apps-sdk/deploy/connect-from-chatgpt
- https://developers.openai.com/api/docs/mcp
- https://developers.openai.com/api/docs/guides/tools-remote-mcp

General ChatGPT connector flow:

1. Enable the required ChatGPT developer/custom connector capability for your account or workspace.
2. Create or obtain a Secure MCP Tunnel in the OpenAI Platform.
3. Download the current tunnel client from the official source named by the docs.
4. Configure it to forward to:

   ```text
   http://127.0.0.1:3000/mcp
   ```

5. Run the tunnel client.
6. Run its doctor or diagnostic command.
7. In ChatGPT connector settings, select the tunnel.
8. Scan and review the exposed tools.
9. Start a new conversation with the connector enabled.
10. Set connector permissions conservatively.
11. Refresh connector metadata after changing tool definitions.

This project does not hard-code product UI labels because those can change.
