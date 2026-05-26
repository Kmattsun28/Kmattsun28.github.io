#!/usr/bin/env bash
FLAG="$(pwd)/.claude/state/pending-pattern-review"

if [ -f "$FLAG" ]; then
    FLAGGED_AT=$(cat "$FLAG")
    rm -f "$FLAG"
    echo "[skill-graph] 前回セッション(${FLAGGED_AT})のパターンレビュー: 汎用化できる知識・設計判断があれば /Users/kmattsun/Documents/My-skill-graph/skill-graph/10_Input/Staged/github-io/ にステージングしてください。なければスキップしてOK。"
fi
