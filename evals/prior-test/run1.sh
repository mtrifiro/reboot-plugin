#!/bin/zsh
# args: model probe run outdir probesdir
R=$(mktemp -d /private/tmp/claude-501/room.XXXX)
cd $R && claude -p --model $1 --setting-sources "" --strict-mcp-config --tools "" --no-session-persistence --system-prompt "You are a helpful assistant." "$(cat $5/$2.txt)" > $4/$2.$1.$3.txt 2>&1
rmdir $R 2>/dev/null; echo done $2 $1 $3
