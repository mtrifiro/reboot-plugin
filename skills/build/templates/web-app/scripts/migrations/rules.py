"""The rules a migration composes, for rewriting a backup so it loads
into an application whose API has moved on.

`rbt import` parses every exported state against the message types the
running application has *now*, by field name, and refuses a field it
does not know. A backup taken before an expunge therefore has to be
edited into the new shape before `scripts/restore.py` sends it: fields
the release removed go, fields it renamed are renamed, and anything
whose meaning changed is rewritten to keep the old meaning.
Renumbering tags alone needs nothing (the export is by field name), and
neither does a change of `--size`.

A migration is a module beside this one, `scripts/migrations/<name>.py`,
run with `scripts/restore.py ... --migration <name>`. It exposes

    def migrate(item: dict) -> dict | None

taking one export line (a dict with `state_type`, `state_ref` and one
of `state`, `sorted_map_entry`, `task`, `idempotent_mutation`) and
returning it changed, or `None` to leave it out; and, when it moves
types, `TYPE_MAP` (old full name -> new) for `compare_exports.py`. For
example:

    from migrations.rules import compose, drop_field, rename_field

    TYPE_MAP: dict[str, str] = {}

    migrate = compose(
        drop_field("todo.v1.Item", "legacy_flag"),
        rename_field("todo.v1.Item", "title", "name"),
    )

These rules are the whole vocabulary migrations have needed so far;
compose them in order, stopping at the first `None`. There is no
`__init__.py`: `scripts/` is on the path and `migrations` is a
namespace package.
"""

from __future__ import annotations

from typing import Callable, Optional

from reboot.aio.types import StateId, StateRef, StateTypeName, state_type_tag_for_name

Item = dict
Rule = Callable[[Item], Optional[Item]]


def drop_field(state_type: str, field: str) -> Rule:
    """Forget a state field the release removed."""

    def rule(item: Item) -> Optional[Item]:
        if item["state_type"] == state_type and "state" in item:
            item["state"].pop(field, None)
        return item

    return rule


def rename_field(state_type: str, old: str, new: str) -> Rule:
    """A field kept its tag and took a new name: the export used the old one."""

    def rule(item: Item) -> Optional[Item]:
        if item["state_type"] == state_type and "state" in item:
            state = item["state"]
            if old in state:
                state[new] = state.pop(old)
        return item

    return rule


def drop_type(state_type: str) -> Rule:
    """Leave out everything of a type the release no longer has."""

    def rule(item: Item) -> Optional[Item]:
        return None if item["state_type"] == state_type else item

    return rule


def drop_tasks(state_type: str, method: str) -> Rule:
    """Leave out tasks of a method the release removed; `method` as the
    export spells it (PascalCase, e.g. `RunLoop`)."""

    def rule(item: Item) -> Optional[Item]:
        task = item.get("task")
        if task is not None and item["state_type"] == state_type:
            if task.get("method") == method:
                return None
        return item

    return rule


ANY_TYPE_URL = "type.googleapis.com/"


def move_types(mapping: dict[str, str]) -> Rule:
    """State types that moved to another package, `old full name -> new`,
    with their method and field names unchanged.

    Rewrites everything an export keys by the type: the routing tag in
    every `state_ref` (a hash of the full name, `reboot/aio/types.py`,
    `state_type_tag_for_name`), the `state_type` and `state_ref` in a
    task's id and in a record's own id and `task_ids`, and the message
    names a task's `response` or `error` is packed under
    (`old.v1.ItemsSummaryResponse` -> `new.v1.ItemsSummaryResponse`).
    A message belongs to the longest moved type name it starts with,
    which is why one rule takes the whole map: `ItemsSummaryResponse`
    is Items', not Item's.
    """
    owners = sorted(mapping.items(), key=lambda kv: -len(kv[0]))
    old_tags = {old: state_type_tag_for_name(StateTypeName(old)) for old in mapping}

    def moved_ref(ref: str, old: str, new: str) -> str:
        tag, _, encoded = ref.partition(":")
        if tag != old_tags[old]:
            raise ValueError(f"{ref} is not a ref of {old}")
        # The id's only escape is `/` written as `\`; `from_id` re-encodes.
        return StateRef.from_id(
            StateTypeName(new), StateId(encoded.replace("\\", "/"))
        ).to_str()

    def move_id(holder: Optional[dict]) -> None:
        """Anything carrying `state_type` and `state_ref`: the line, a
        task id, a record."""
        if not holder:
            return
        old = holder.get("state_type", "")
        if old in mapping:
            holder["state_ref"] = moved_ref(holder["state_ref"], old, mapping[old])
            holder["state_type"] = mapping[old]

    def moved_message(full_name: str) -> str:
        for old, new in owners:
            if full_name.startswith(old):
                return new[: new.rfind(".")] + full_name[old.rfind("."):]
        return full_name

    def move_any(any_json: object) -> None:
        """A protobuf `Any` as JSON: `{"@type": "type.googleapis.com/<name>",
        ...}`; a `google.rpc.Status` carries more of them in `details`."""
        if not isinstance(any_json, dict):
            return
        url = any_json.get("@type")
        if isinstance(url, str) and url.startswith(ANY_TYPE_URL):
            any_json["@type"] = ANY_TYPE_URL + moved_message(url[len(ANY_TYPE_URL):])
        for detail in any_json.get("details") or []:
            move_any(detail)

    def rule(item: Item) -> Optional[Item]:
        move_id(item)
        task = item.get("task")
        if task is not None:
            move_id(task.get("task_id"))
            move_any(task.get("response"))
            move_any(task.get("error"))
        record = item.get("idempotent_mutation")
        if record is not None:
            move_id(record)
            for task_id in record.get("task_ids", []):
                move_id(task_id)
        return item

    return rule


def move_type(old: str, new: str) -> Rule:
    """One type moved; for several at once, `move_types` picks each
    message's owner correctly."""
    return move_types({old: new})


def drop_records(state_type: str) -> Rule:
    """Leave out a type's idempotency records.

    A record's key is the uuid5 of `'<service>.<method>'@<id>[: alias]`
    (`reboot/aio/idempotency.py`), and the service name carries the
    package: after a move nothing computes the old key again, so the
    records are inert. Their `response` bytes were also serialised under
    the tags of the release that wrote them.
    """

    def rule(item: Item) -> Optional[Item]:
        if item["state_type"] == state_type and "idempotent_mutation" in item:
            return None
        return item

    return rule


def compose(*rules: Rule) -> Rule:
    """Apply rules in order; the first `None` wins."""

    def migrate(item: Item) -> Optional[Item]:
        current: Optional[Item] = item
        for rule in rules:
            if current is None:
                return None
            current = rule(current)
        return current

    return migrate
