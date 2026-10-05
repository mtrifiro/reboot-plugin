---
title: "Zod apps: move to Zod 4"
summary: "Change a zod 3.x pin to zod 4, adding skipLibCheck if type-checking fails."
kind: migration
audience: agent
applies: [mcp-ui, web-app]
when: "package.json pins zod 3.x"
---

## Zod apps: move to Zod 4

Reboot now pins `zod` 4.x throughout (the library itself imports
`zod/v4`). If the app's `package.json` lists `zod` with a 3.x range
(e.g. `^3.25.0`), change it to `"zod": "^4.0.0"`. If type-checking
then fails inside `node_modules` type definitions, add
`"skipLibCheck": true` to the `compilerOptions` of `tsconfig.json`
(Reboot's own examples now set it).
