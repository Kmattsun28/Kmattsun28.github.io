#!/usr/bin/env bash
INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    r = d.get('tool_response', {})
    print(r.get('exit_code', 0) if isinstance(r, dict) else 0)
except:
    print(0)
" 2>/dev/null || echo "0")

if [ "$EXIT_CODE" != "0" ] && [ -n "$EXIT_CODE" ]; then
    echo "[Gotcha候補] エラーを解決できたら以下にステージングしてください:"
    echo "  /Users/kmattsun/Documents/My-skill-graph/skill-graph/10_Input/Staged/github-io/$(date +%Y-%m-%d)-gotcha-<slug>.md"
    echo "  type: error / source_ws: github-io / root cause + solution + prevention を記録"
fi
