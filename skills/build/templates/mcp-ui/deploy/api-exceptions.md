# API removals approved for deploy

`scripts/deploy.sh` refuses a deploy when a line was removed from `api/`
since the commit production runs (`scripts/api_removals.py`): a removed
method or field, or a reworded description, needs an expunge and a
restore. Reboot allows a few such changes (an `mcp=` option, a field's
`description=`; `python/references/api-schema-evolution.md`). List each
one here, file and exact line, and delete it once it has shipped:

<!--
- file: api/bank/v1/bank.py
  removed: `description="The balance, in cents.",`
  why: a field's description may change (api-schema-evolution.md)
-->
