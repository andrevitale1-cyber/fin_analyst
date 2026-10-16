# Development workflow

These are the user's standing preferences for this project:

- Use the installed **Ponytail** skill for every development task. Read its `SKILL.md` and follow the smallest complete solution approach.
- Use **Headroom** during development to manage context efficiently. Prefer its MCP file-reading and compression tools for substantial reads and large outputs, with focused searches first. The local installation is at `../.tools/headroom/headroom-ai/` in the project workspace.
- Whenever the user asks to clone, copy, or take inspiration from a website, use **clone-website**. Read `../design-reference-cloner/.agents/skills/clone-website/SKILL.md`; the command entry point is `../design-reference-cloner/.claude/commands/clone-website.md`.
- If a required skill or tool is unavailable, look for its current location, explain the limitation, and continue the work that can be completed. Do not claim to have used an unavailable tool.

Keep synced files under the parent workspace's `sources/` directory read-only.
