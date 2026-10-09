import { describe, expect, test } from 'claude-code/testing'

import { applicationName, bashEditsApi, incompatibilities, isApiFile, isApiPath, normalizeType } from './schema'

const API = `from reboot.api import API, Field, Methods, Model, Reader, Type, Writer


class UserState(Model):
    count: int = Field(tag=1, default=0)
    label: str = Field(tag=2, default="")
    settings: Optional[Settings] = Field(tag=3, default=None, description="Settings.")


class IncrementRequest(Model):
    amount: int = Field(tag=1, default=0)


api = API(
    User=Type(
        state=UserState,
        description="The signed-in user and their own state.",
        methods=Methods(
            get=Reader(
                request=None,
                response=None,
                description="Get the user's count.",
                mcp=None,
            ),
            increment=Writer(
                request=IncrementRequest,
                response=None,
                description=(
                    "Add \`amount\` to the user's "
                    "count."
                ),
                mcp=None,
            ),
            create=Writer(
                request=None,
                response=None,
                factory=True,
                description="Create the user.",
                mcp=None,
            ),
            peek=Reader(
                request=None,
                response=None,
                mcp=None,
            ),
        ),
    ),
)
`

const edit = (from: string, to: string) => incompatibilities(API, API.replace(from, to))

describe('compatible changes pass', () => {
  test('no change', () => expect(incompatibilities(API, API)).toEqual([]))

  test('a new field with a default, a new method or Type', () => {
    expect(edit('    label: str', '    note: str = Field(tag=4, default="")\n    label: str')).toEqual([])
    expect(edit('    label: str', '    tags: list[str] = Field(tag=4, default_factory=list)\n    label: str')).toEqual([])
    expect(edit('            get=Reader(', '            fetch=Reader(description="Fetch."),\n            get=Reader(')).toEqual([])
  })

  test('a renamed field that keeps its tag', () => {
    expect(edit('    label: str = Field(tag=2', '    title: str = Field(tag=2')).toEqual([])
  })

  test('a reworded Type description and an mcp= change', () => {
    expect(edit('their own state.', 'their state.')).toEqual([])
    expect(edit('description="Get the user\'s count.",\n                mcp=None', 'description="Get the user\'s count.",\n                mcp=Tool()')).toEqual([])
  })

  test('Writer to Transaction, and a renamed request model', () => {
    expect(edit('increment=Writer(', 'increment=Transaction(')).toEqual([])
    expect(incompatibilities(API, API.replaceAll('IncrementRequest', 'AddRequest'))).toEqual([])
  })

  test('the same type spelled another way', () => {
    expect(edit('Optional[Settings]', 'Settings | None')).toEqual([])
    expect(edit('Optional[Settings]', 'None | Settings')).toEqual([])
    expect(edit('    count: int', '    count: int ')).toEqual([])
  })

  test('a field whose default holds parentheses is still seen', () => {
    const nested = API.replace('default=None, description="Settings."', 'default_factory=lambda: Settings(), description="Settings (x)."')
    expect(incompatibilities(nested, nested)).toEqual([])
    expect(incompatibilities(nested, nested.replace('    settings: Optional[Settings] = Field(tag=3, default_factory=lambda: Settings(), description="Settings (x).")\n', ''))).toEqual([
      'field `UserState.settings` (tag 3) is deleted or its tag changed',
    ])
  })
})

describe('refused changes are named', () => {
  test('a reworded method description, even split across literals', () => {
    expect(edit("Get the user's count.", "Read the user's count.")).toEqual([
      "method `User.get`'s `description=` changes",
    ])
    expect(edit('"count."', '"total."')).toEqual(["method `User.increment`'s `description=` changes"])
  })

  test('a description added to a method that had none', () => {
    expect(edit('            peek=Reader(\n', '            peek=Reader(\n                description="Peek.",\n')).toEqual([
      "method `User.peek` gains a `description=` (it is part of the method's options)",
    ])
  })

  test('a deleted method, field or Type', () => {
    expect(edit('            get=Reader(', '            fetch=Reader(')).toEqual([
      'method `User.get` is deleted or renamed',
    ])
    expect(edit('    label: str = Field(tag=2, default="")\n', '')).toEqual([
      'field `UserState.label` (tag 2) is deleted or its tag changed',
    ])
    expect(edit('    User=Type(', '    Member=Type(')).toEqual(['state type `User` is deleted or renamed'])
  })

  test('a changed tag, type or method kind', () => {
    expect(edit('Field(tag=2,', 'Field(tag=5,')).toEqual([
      'field `UserState.label` (tag 2) is deleted or its tag changed',
    ])
    expect(edit('    count: int', '    count: list[int]')).toEqual([
      'field `UserState.count` (tag 1) changes type, int → list[int]',
    ])
    expect(edit('increment=Writer(', 'increment=Workflow(')).toEqual([
      'method `User.increment` changes kind, Writer → Workflow',
    ])
  })

  test('Writer to Transaction on a factory constructor', () => {
    expect(edit('            create=Writer(', '            create=Transaction(')).toEqual([
      'method `User.create` changes kind on a `factory=True` constructor, Writer → Transaction',
    ])
  })

  test('a field added without a default, or a default removed', () => {
    expect(edit('    label: str', '    note: str = Field(tag=4)\n    label: str')).toEqual([
      'field `UserState.note` (tag 4) is added without a default',
    ])
    expect(edit('Field(tag=2, default="")', 'Field(tag=2)')).toEqual([
      "field `UserState.label` (tag 2) loses its default (required-ness can't change)",
    ])
  })
})

describe('paths, commands and .rbtrc', () => {
  test('only hand-written API files, judged from the project root', () => {
    expect(isApiFile('/w/todo/api/todo/v1/todo.py')).toBe(true)
    expect(isApiFile('/w/todo/backend/api/todo/v1/todo_rbt.py')).toBe(false)
    expect(isApiFile('/w/todo/backend/api/todo/v1/todo.py', '/w/todo')).toBe(false)
    expect(isApiFile('/w/todo/backend/src/servicers/todo.py')).toBe(false)
    // A project that itself lives under a directory named web.
    expect(isApiFile('/home/me/web/todo/api/todo/v1/todo.py', '/home/me/web/todo')).toBe(true)
    expect(isApiFile('/home/me/web/todo/api/todo/v1/todo.py')).toBe(false)
    expect(isApiPath('/home/me/web/todo/api/todo/v1/todo.py')).toBe(true)
    expect(isApiPath('/w/todo/backend/api/todo/v1/todo_rbt.py')).toBe(false)
  })

  test('shell commands that rewrite an API file', () => {
    for (const command of [
      "sed -i '' 's/old/new/' api/todo/v1/todo.py",
      'sed -i.bak -e s/a/b/ api/todo/v1/todo.py',
      "perl -pi -e 's/a/b/' api/todo/v1/todo.py",
      'cat > api/todo/v1/todo.py <<EOF\nx\nEOF',
      'echo x >> api/todo/v1/todo.py',
      'mv /tmp/todo.py api/todo/v1/todo.py',
      'cp api/todo/v1/todo.py.bak api/todo/v1/todo.py',
      'rm api/todo/v1/todo.py',
      'git checkout -- api/todo/v1/todo.py',
      'git restore api/todo/v1/todo.py',
      'python3 gen.py | tee api/todo/v1/todo.py',
    ]) {
      expect([command, bashEditsApi(command)]).toEqual([command, true])
    }
    for (const command of [
      'cat api/todo/v1/todo.py',
      'grep -n Field api/todo/v1/todo.py',
      "sed -n '1,40p' api/todo/v1/todo.py",
      'git diff api/todo/v1/todo.py',
      'uv run mypy backend/ tests/',
      'sed -i s/a/b/ backend/src/servicers/todo.py',
    ]) {
      expect([command, bashEditsApi(command)]).toEqual([command, false])
    }
  })

  test('type spellings', () => {
    expect(normalizeType('Optional[str]')).toBe('None|str')
    expect(normalizeType('str | None')).toBe('None|str')
    expect(normalizeType('List[Optional[int]]')).toBe('list[int|None]')
    expect(normalizeType('dict[str, int]')).toBe('dict[str,int]')
  })

  test('the application name', () => {
    expect(applicationName('dev run --python\ndev run --application-name=todo-list\n')).toBe('todo-list')
    expect(applicationName('dev run --python\n')).toBe(null)
  })
})
