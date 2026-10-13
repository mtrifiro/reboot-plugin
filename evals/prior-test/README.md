# Prior test: what models believe about Reboot

A Semantic Anchors-style prior test
(https://llm-coding.github.io/Semantic-Anchors/, "An Anchor Delivers
Only as Far as the Prior Reaches"): ask models about Reboot with no
skills, no context and no tools, and see what they already get right,
what they get wrong, and how. Skill words belong where the prior is
wrong; where it is right they are reading budget spent for nothing.

## How it runs

`run1.sh <model> <probe> <run> <outdir> <probesdir>` runs one probe in a
fresh `claude -p` from an empty directory under `/private/tmp/claude-501`
(the scratchpad path contains "reboot-plugin", which leaks the answer),
with `--setting-sources "" --strict-mcp-config --tools ""
--system-prompt "You are a helpful assistant."`. A canary run confirmed
no CLAUDE.md, memory, skills or the word "reboot" reach the model.
Never use a subagent: it inherits this project's context.

```sh
for m in claude-haiku-5-5 claude-sonnet-5-5 claude-opus-5-5 claude-fable-5-1; do
  for p in R1 R2 R3 R4 R5 R6 R7 R8 R9 E1 E2; do for r in 1 2; do echo "$m $p $r"; done; done
done | xargs -P 10 -L 1 sh -c "$PWD/run1.sh \$0 \$1 \$2 $PWD/<date> $PWD/probes"
```

Probes: R1 what Reboot is, R2 method kinds, R3 workflows and crashes,
R4 workflow call primitives, R5 `.rbtrc`, R6 `rbt` commands and layout,
R7 tests, R8 React, R9 bare "Reboot"; E1 write a bank (API, servicer,
entry), E2 write an Order workflow. Recall probes ask "what is X";
E probes ask the model to use it (recall and execution differ).

## 2026-10-13: four models × 11 probes × 2 runs

Graded against `skills/python` and its references. Runs agreed with
each other; stated confidence was "medium" whether the answer was right
or invented, so it is no signal.

### The main finding: the prior is protobuf-era Reboot

All 8 E1 runs wrote the API as a `.proto` file (`rbt.v1alpha1`
options, `_pb2` imports, `rbt protoc`); none used `reboot.api`. All 8
R6 runs described a `.proto` layout. Fable, the newest model, was the
most stale. Sonnet and Opus sometimes add "originally protobuf, now
pydantic" and then write protobuf anyway. This is the article's
"anchor lags practice" case: the training data holds the old Reboot
densely and the current one thinly, and models substitute the old one
without saying so. No skill says "not `.proto`"
(`grep -c proto skills/python/SKILL.md` is 0).

### Wrong in most or all runs, and where the skills stand

| Wrong belief | Runs | Skills today |
|---|---|---|
| API in `.proto`, `rbt protoc`, `_pb2` | E1 8/8, R6 8/8 | pydantic stated (`python/SKILL.md:17`), the old form never named |
| Tests are pytest/unittest harness tests | R7 8/8; none named Gherkin or `reboot.bdd` | `python/SKILL.md:231`, low in the file, not a Critical Rule |
| Workflow is an instance method using `self` | E2 8/8 | `servicer-workflow-declare.md:26-30`; not a Critical Rule |
| `context.state_id` in a reader/writer/transaction | E1, every run that needed the id | Critical Rule (`python/SKILL.md:89-92`) |
| Servicer takes `state` as a parameter | E1 4/8, E2 2/8, R1/R8 fable and haiku | Critical Rule (`python/SKILL.md:52-57`) |
| Authorizer missing, or present as bare `allow()` | E1 8/8 (4 missing, 4 `allow()`) | Critical Rule plus `servicer-authorizer.md:99` |
| `Field(tag=N)` zero default, `mcp=`, `factory=True` | E1 0/8 (follow from the proto miss) | Critical Rules; `api_lint.py` checks some |
| `.rbtrc` with `--name`, a `common` prefix, `protoc` lines | R5 most runs | `--name` covered; `common` uncovered |
| `until` resolves on "truthy", polls outside state | R4 5/8 | `servicer-workflow-wait.md:32-36,153` |
| Scope on `context.` instead of the ref | R4 2/8 | examples only, no Never |

### Right in all or nearly all runs (cut or thin candidates)

| Belief | Where the skills spell it out |
|---|---|
| `.rbtrc` is line-based (YAML 0/8, even Haiku's guess) | `python/SKILL.md:93`, `AGENTS.md` "(line-based, not YAML)", `lifecycle-rbtrc.md:105` |
| Four method kinds and their guarantees; transaction for cross-actor work; a writer can't call a writer | `api-methods.md:27-32`, `rpc-calls.md:51-54`, `python/SKILL.md:84-85` |
| Calls pass kwargs, not a request object | `python/SKILL.md:88-89` |
| `Application(servicers=[...]).run()` under `asyncio.run` | `python/SKILL.md:63-68` (keep only the registry detail) |
| A workflow replays from the top; memoized steps return their result; a bare `await` re-runs; stable idempotency key for Stripe | `servicer-workflow.md:19-21`, `servicer-workflow-external.md:36-37,87-88,159` |
| `Reboot()` harness shape | `testing-harness.md:31-59` |
| React hooks `useFoo({id})`, `{response, isLoading, aborted}`, `.pending` | `react-generated-client.md:37-65,83-86` |

Haiku got many of these wrong; the cuts assume builds run on Sonnet or
larger.

### No model knew (keep every word)

Default scopes, effect validation and alias poisoning in workflows;
`spawn(when=…)` from a workflow; Transaction `mode=`; mutations resolve
with `aborted` rather than throwing; ids real on every render;
`StateNotConstructed` storms; the six-live-reads HTTP/1.1 limit;
`--env-file`.

### On naming Temporal (the "anchor plus difference" idea)

No run named Temporal, Restate or DBOS, and the replay model was
already right without one. Naming Temporal would mostly import what is
wrong for Reboot (activities wrapping every call, retry policies with
backoff, signals). Not worth a line.

### Bare "Reboot"

Without context "Reboot" means restarting a machine (Haiku 0/2 found
the framework; the others list it last). Skill descriptions and the
reminder hook should keep saying "Reboot app" or reboot.dev, never the
bare word, wherever a trigger matters.

## Rerun

Rerun after a model release or a large skill change. A belief moving
from wrong to right frees words; one moving the other way (as Fable's
protobuf prior did) needs them.
