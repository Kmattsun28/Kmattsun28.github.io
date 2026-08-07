# 活動追加Workflow入力フォーム改善 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** GitHub Actionsの活動追加フォームを、活動タイプは選択式、日付は具体例付きの入力式にして、入力ミスを減らす。

**Architecture:** `workflow_dispatch`の入力定義だけをUI向けに改善し、登録処理は既存の`bin/add_site_entry.py`へ環境変数経由で渡す。日付の一般表記を正規化する処理は既存実装を利用し、Workflowの定義テストでUI契約を固定する。

**Tech Stack:** GitHub Actions YAML、Python 3.13、Python unittest、Prettier。

## Global Constraints

- GitHub Actionsの入力タイプは`boolean`、`choice`、`number`、`environment`、`string`の範囲で使用する。
- 日付はカレンダー型にせず、`YYYY-MM-DD`または`YYYY-MM-DD〜YYYY-MM-DD`を基本例とする。
- 既存の活動データ形式と`bin/add_site_entry.py`の重複・URL・日付範囲検証を変更しない。
- 無関係な`.claude/*`と`CLAUDE.md`のローカル変更をコミットしない。

---

### Task 1: Workflow入力契約の回帰テストを追加

**Files:**
- Modify: `tests/test_workflows.py`
- Test: `tests/test_workflows.py`

**Interfaces:**
- Consumes: `.github/workflows/add-activity.yml`のテキスト。
- Produces: 活動タイプが`choice`で、日付説明に標準例と代替表記が含まれることを検証するテスト。

- [ ] **Step 1: Write the failing test**

```python
    def test_add_activity_form_uses_clear_input_types(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "add-activity.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("type: choice", workflow)
        self.assertIn("シンポジウム", workflow)
        self.assertIn("その他", workflow)
        self.assertIn("YYYY-MM-DD〜YYYY-MM-DD", workflow)
        self.assertIn("/ and ~ are also accepted", workflow)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest discover -s tests -p 'test_workflows.py'`

Expected: FAIL because the current `type` input is `string` and has no choice options.

### Task 2: Workflow入力画面を改善

**Files:**
- Modify: `.github/workflows/add-activity.yml`

**Interfaces:**
- Consumes: GitHub `workflow_dispatch` input definitions.
- Produces: `inputs.type` as a `choice` value with stable Japanese options; `inputs.date` as a clearly documented free-text date field.

- [ ] **Step 1: Change the activity type input to a choice**

Replace the existing `type` input with:

```yaml
      type:
        description: Activity type
        required: true
        type: choice
        options:
          - シンポジウム
          - 国内学会発表
          - 国際学会発表
          - 受賞
          - 展示
          - イベント
          - その他
```

- [ ] **Step 2: Make the date description explicit**

Keep `date` as `type: string` and use:

```yaml
        description: "Activity date (YYYY-MM-DD or YYYY-MM-DD〜YYYY-MM-DD; / and ~ are also accepted)"
```

This avoids implying that GitHub provides a calendar picker while showing copyable examples.

- [ ] **Step 3: Run the workflow contract test**

Run: `python3 -m unittest discover -s tests -p 'test_workflows.py'`

Expected: PASS with all workflow tests passing.

### Task 3: Full verification and handoff

**Files:**
- Test: `tests/test_add_site_entry.py`
- Test: `tests/test_workflows.py`
- Check: `.github/workflows/add-activity.yml`

**Interfaces:**
- Consumes: Updated Workflow definition and existing date normalization tests.
- Produces: Verified repository changes ready for commit and push.

- [ ] **Step 1: Run all Python tests**

Run: `python3 -m unittest discover -s tests -p 'test_*.py'`

Expected: All tests pass, including common date-format normalization.

- [ ] **Step 2: Check Workflow formatting and whitespace**

Run: `npx prettier .github/workflows/add-activity.yml --check && git diff --check -- . ':!.claude/**' ':!CLAUDE.md'`

Expected: Prettier reports all matched files formatted and `git diff --check` reports no output.

- [ ] **Step 3: Review the staged scope**

Run: `git diff -- .github/workflows/add-activity.yml tests/test_workflows.py`

Expected: Only the activity input choice options and date guidance plus their regression test are present.

- [ ] **Step 4: Commit the implementation**

```bash
git add .github/workflows/add-activity.yml tests/test_workflows.py
git commit -m "feat: simplify activity workflow inputs"
```

- [ ] **Step 5: Push and verify the workflow definition is available on main**

```bash
git push origin main
```

Expected: `main` contains the updated Workflow, ready for the next manual activity entry.
