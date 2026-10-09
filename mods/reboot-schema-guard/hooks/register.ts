import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { applicationName, bashEditsApi, incompatibilities, isApiFile, isApiPath } from './schema'

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

/**
 * Where the project holds state the API must boot over: `rbt dev run`'s
 * local state, or a production deploy the project's `scripts/deploy.sh`
 * has recorded in its ledger (a fresh clone or an expunged dev state still
 * answers to production). Null when there is none.
 */
async function stateOf($: EngineInterface, root: string): Promise<string | null> {
  const dev = `${root}/.rbt/dev`
  if (await $.fs.exists(dev)) {
    const name = applicationName(await $.fs.read(`${root}/.rbtrc`))
    const has = name ? await $.fs.exists(`${dev}/${name}`) : (await $.fs.list(dev)).some(entry => entry.kind === 'dir')
    if (has) return dev
  }
  if (await $.fs.exists(`${root}/deploy/ledger.jsonl`)) return `${root}/deploy/ledger.jsonl, a production deploy`

  return null
}

async function readOr($: EngineInterface, path: string): Promise<string | null> {
  try {
    return await $.fs.read(path)
  } catch {
    return null
  }
}

export const register: Register = on => {
  // The rules count as read once the whole file has been; a partial read
  // (`limit`, `offset`) hasn't shown the table.
  on('tool.call', { tool: 'Read' }, async ($, e, next) => {
    const ran = await next(e)
    const { limit, offset } = e as { limit?: number; offset?: number }
    if (e.file_path.endsWith(`/${RULES}`) && ran.isError !== true && limit === undefined && offset === undefined) {
      await update($, hasReadRules, () => true)
    }

    return ran
  }).catch(($, e, next) => next(e))

  // After compaction the rules are out of the model's context: read them again.
  on('session.compact', async ($, e, next) => {
    const compacted = await next(e)
    await update($, hasReadRules, () => false)

    return compacted
  })

  // Fails open: a guard that breaks must not stop the build.
  on('tool.call', { tool: ['Edit', 'Write'] }, async ($, e, next) => {
    if (!isApiPath(e.file_path)) return next(e)
    const root = await projectOf($, e.file_path)
    if (!root || !isApiFile(e.file_path, root)) return next(e)
    const state = await stateOf($, root)
    if (state === null) return next(e)

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
          `${$.plugin.name}: this app has persisted state (${state}), and the runtime ` +
          `refuses to boot over these API changes:\n- ${problems.join('\n- ')}\n` +
          `Make the change additively instead (a new method or field, the old one kept), per ` +
          `${RULES_PATH}. Expunging dev state would also allow it, but deletes the app's data: ` +
          `ask the user before running \`rbt dev expunge\`.`,
      }
    }
    if (!(await read($, hasReadRules))) {
      return {
        deny:
          `${$.plugin.name}: this app has persisted state (${state}), so only additive ` +
          `API changes boot. Read ${RULES_PATH} and check this change against its table, ` +
          `then make the edit again.`,
      }
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  // A shell command that rewrites an API file bypasses the check above;
  // in a project with state, send it through Edit or Write instead.
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    if (!bashEditsApi(e.command)) return next(e)
    const root = await projectOf($, `${await $.session.cwd()}/.`)
    if (!root) return next(e)
    const state = await stateOf($, root)
    if (state === null) return next(e)

    return {
      deny:
        `${$.plugin.name}: this app has persisted state (${state}), and this command rewrites an ` +
        `API definition file where the guard can't check it. Make the change with the Edit or ` +
        `Write tool instead, additively per ${RULES_PATH}.`,
    }
  }).catch(($, e, next) => next(e))
}
