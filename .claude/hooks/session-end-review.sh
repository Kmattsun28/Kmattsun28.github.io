#!/usr/bin/env bash
STATE_DIR="$(pwd)/.claude/state"
mkdir -p "$STATE_DIR"
echo "$(date '+%Y-%m-%d %H:%M')" > "$STATE_DIR/pending-pattern-review"

STAGED_DIR="/Users/kmattsun/Documents/My-skill-graph/skill-graph/10_Input/Staged/github-io"
mkdir -p "$STAGED_DIR"
COUNT=$(find "$STAGED_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

if [ "$COUNT" -gt "0" ]; then
    echo "📦 skill-graph: Staged/github-io/ に ${COUNT} 件 → skill-graphで「蒸留して」を実行してください"
fi
