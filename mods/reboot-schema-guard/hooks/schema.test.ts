import { describe, expect, test } from 'claude-code/testing'

import { applicationName, incompatibilities, isApiFile } from './schema'

const API = `from reboot.api import API, Field, Methods, Model, Reader, Type, Writer


class UserState(Model):
    count: int = Field(tag=1, default=0)
    label: str = Field(tag=2, default="")


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
        ),
    ),
)
`

const edit = (from: string, to: string) => incompatibilities(API, API.replace(from, to))

describe('compatible changes pass', () => {
  test('no change', () => expect(incompatibilities(API, API)).toEqual([]))

  test('a new field, method or Type', () => {
    expect(edit('    label: str', '    note: str = Field(tag=3, default="")\n    label: str')).toEqual([])
    expect(edit('            get=Reader(', '            peek=Reader(description="Peek."),\n            get=Reader(')).toEqual([])
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
})

describe('refused changes are named', () => {
  test('a reworded method description, even split across literals', () => {
    expect(edit("Get the user's count.", "Read the user's count.")).toEqual([
      "method `User.get`'s `description=` changes",
    ])
    expect(edit('"count."', '"total."')).toEqual(["method `User.increment`'s `description=` changes"])
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
})

describe('paths and .rbtrc', () => {
  test('only hand-written API files', () => {
    expect(isApiFile('/w/todo/api/todo/v1/todo.py')).toBe(true)
    expect(isApiFile('/w/todo/backend/api/todo/v1/todo_rbt.py')).toBe(false)
    expect(isApiFile('/w/todo/backend/src/servicers/todo.py')).toBe(false)
  })

  test('the application name', () => {
    expect(applicationName('dev run --python\ndev run --application-name=todo-list\n')).toBe('todo-list')
    expect(applicationName('dev run --python\n')).toBe(null)
  })
})
