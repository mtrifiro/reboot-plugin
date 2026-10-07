import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { applicationName, incompatibilities, isApiFile } from './schema'

const hasReadRules = atom({ plugin: 'reboot-schema-guard', key: 'hasReadRules' } as const, false)

const RULES = 'api-schema-evolution.md'
const RULES_PATH = `the reboot plugin's skills/python/references/${RULES}`

const parent = (path: string) => path.replace(/\/[^/]*$/, '') || '/'

/** The nearest ancestor of `path` holding a `.rbtrc`, up to six levels. */
async function projectOf($: EngineInterface, path: string): Promise<string | null> {
  let dir = parent(path)
  for (let i = 0; i < 6 && dir !== '/'; i++) {
    if (await $.fs.exists(`${dir}/.rbtrc`)) return dir
    dir = parent(dir)
  }

  return null
}

/** Whether `rbt dev run` has written state for the project. */
async function hasState($: EngineInterface, root: string): Promise<boolean> {
  const dev = `${root}/.rbt/dev`
  if (!(await $.fs.exists(dev))) return false
  const name = applicationName(await $.fs.read(`${root}/.rbtrc`))
  if (name) return $.fs.exists(`${dev}/${name}`)

  return (await $.fs.list(dev)).some(entry => entry.kind === 'dir')
}

async function readOr($: EngineInterface, path: string): Promise<string | null> {
  try {
    return await $.fs.read(path)
  } catch {
    return null
  }
}

export const register: Register = on => {
  on('tool.call', { tool: 'Read' }, async ($, e, next) => {
    const ran = await next(e)
    if (e.file_path.endsWith(`/${RULES}`) && ran.isError !== true) {
      await update($, hasReadRules, () => true)
    }

    return ran
  }).catch(($, e, next) => next(e))

  // Fails open: a guard that breaks must not stop the build.
  on('tool.call', { tool: ['Edit', 'Write'] }, async ($, e, next) => {
    if (!isApiFile(e.file_path)) return next(e)
    const root = await projectOf($, e.file_path)
    if (!root || !(await hasState($, root))) return next(e)

    const before = await readOr($, e.file_path)
    if (before === null) return next(e)
    let after: string
    if (e.tool === 'Write') after = e.content
    else if (e.replace_all) after = before.split(e.old_string).join(e.new_string)
    else after = before.replace(e.old_string, () => e.new_string)

    const problems = incompatibilities(before, after)
    if (problems.length > 0) {
      return {
        deny:
          `${$.plugin.name}: this app has persisted state (${root}/.rbt/dev), and the runtime ` +
          `refuses to boot over these API changes:\n- ${problems.join('\n- ')}\n` +
          `Make the change additively instead (a new method or field, the old one kept), per ` +
          `${RULES_PATH}. Expunging dev state would also allow it, but deletes the app's data: ` +
          `ask the user before running \`rbt dev expunge\`.`,
      }
    }
    if (!(await read($, hasReadRules))) {
      return {
        deny:
          `${$.plugin.name}: this app has persisted state (${root}/.rbt/dev), so only additive ` +
          `API changes boot. Read ${RULES_PATH} and check this change against its table, ` +
          `then make the edit again.`,
      }
    }

    return next(e)
  }).catch(($, e, next) => next(e))
}
