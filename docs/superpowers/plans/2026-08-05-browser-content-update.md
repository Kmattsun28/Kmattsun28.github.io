# Browser Content Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** GitHub ActionsのWebフォームから研究実績・活動を入力し、ローカル編集と手動のGit操作なしでサイトへ公開できるようにする。

**Architecture:** 研究実績用と活動用の2つの`workflow_dispatch` workflowを追加する。各workflowは入力を環境変数でPython更新スクリプトへ渡し、スクリプトが既存YAMLを検証して追記する。成功時は`SITE_UPDATE_TOKEN`で自動commit・pushし、既存の`deploy.yml`がサイトをビルドして公開する。第1段階では表示テンプレートとBibTeXの正本管理は変更しない。

**Tech Stack:** Python 3.13、PyYAML、Python標準ライブラリ`unittest`、GitHub Actions、Jekyll/GitHub Pages

## Global Constraints

- 更新対象は研究実績が`_data/publications.yml`、活動が`_data/activities.yml`に限定する。
- 入力検証に失敗した場合、対象YAMLを変更せずworkflowを失敗させる。
- YAML全体を再ダンプせず、既存コメント・順序・書式を保ったまま新しいエントリを追記する。
- workflowのcheckoutとpushにはRepository Secret `SITE_UPDATE_TOKEN`を使う。
- `SITE_UPDATE_TOKEN`は対象リポジトリ限定のfine-grained PATで、ContentsのRead and write権限だけを持つ。
- 研究実績と活動のworkflowは同じ`content-entry` concurrency groupを使い、`cancel-in-progress: false`にする。
- 第1段階では`_bibliography/papers.bib`、Liquidテンプレート、ページURL、サイトデザインを変更しない。
- 新規Python依存は追加せず、既存の`requirements.txt`にある`pyyaml`を使う。
- すべてのコマンドはリポジトリルートから実行する。

---

## File Map

### Create

- `bin/add_site_entry.py` — 研究実績・活動の入力正規化、検証、YAML追記を担当するCLI。
- `tests/test_add_site_entry.py` — 更新スクリプトの検証とファイル追記の単体テスト。
- `.github/workflows/add-publication.yml` — 研究実績をWebフォームから追加するworkflow。
- `.github/workflows/add-activity.yml` — 活動をWebフォームから追加するworkflow。
- `docs/content-update.md` — 初回のSecret設定と日常の更新手順を説明する利用者向け文書。

### Modify

- なし。既存の`deploy.yml`は変更せず、pushトリガーを利用する。

### Intentionally unchanged

- `_data/publications.yml`
- `_data/activities.yml`
- `_bibliography/papers.bib`
- `_pages/publications.md`
- `_pages/activities-ja.md`
- `_includes/publications_list.html`
- `_includes/activities_list.html`

---

## Task 1: YAML更新スクリプトをTDDで実装する

**Files:**
- Create: `tests/test_add_site_entry.py`
- Create: `bin/add_site_entry.py`

**Interfaces:**
- `load_entries(path: pathlib.Path) -> list[dict]`
- `normalize_publication(values: Mapping[str, str]) -> dict`
- `normalize_activity(values: Mapping[str, str]) -> dict`
- `validate_entry(kind: str, entry: Mapping[str, object], existing: Sequence[Mapping[str, object]]) -> None`
- `append_entry(path: pathlib.Path, entry: Mapping[str, object]) -> None`
- `add_entry(kind: str, values: Mapping[str, str], output_path: pathlib.Path) -> dict`
- CLI: `python bin/add_site_entry.py publication ...` または `python bin/add_site_entry.py activity ...`。両subcommandにテスト用の任意`--output`を持たせ、省略時だけ本番の既定パスを使う。

### Step 1: 失敗するテストを書く

`tests/test_add_site_entry.py`を作り、`unittest`と一時ディレクトリを使って、次の契約をテストする。

```python
class AddSiteEntryTests(unittest.TestCase):
    def test_appends_publication_without_rewriting_existing_content(self):
        original = (
            "# Publications list\n\n"
            "- title: \"Existing paper\"\n"
            "  authors: \"Author A\"\n"
            "  venue: \"Venue\"\n"
            "  year: 2024\n"
            "  url: \"https://example.com/old\"\n"
        )
        path = self.write_yaml("publications.yml", original)

        result = add_entry(
            "publication",
            {
                "title": "新しい論文",
                "authors": "松本亘平, Author B",
                "venue": "Example Conference",
                "year": "2026",
                "url": "https://example.com/new",
            },
            path,
        )

        self.assertEqual(result["year"], 2026)
        updated = path.read_text(encoding="utf-8")
        self.assertTrue(updated.startswith(original))
        self.assertIn('title: 新しい論文', updated)
        self.assertIn('url: https://example.com/new', updated)

    def test_appends_activity_with_unicode_period_date(self):
        path = self.write_yaml("activities.yml", "[]\n")

        result = add_entry(
            "activity",
            {
                "title": "研究展示",
                "date": "2026-08-01〜2026-08-03",
                "type": "展示",
                "venue": "名古屋大学",
                "description": "説明",
                "url": "",
            },
            path,
        )

        self.assertEqual(result["date"], "2026-08-01〜2026-08-03")
        self.assertIn("研究展示", path.read_text(encoding="utf-8"))

    def test_rejects_invalid_year_and_url(self):
        path = self.write_yaml("publications.yml", "[]\n")
        with self.assertRaises(ValueError):
            add_entry("publication", {"title": "P", "authors": "A", "venue": "V", "year": "26", "url": ""}, path)
        with self.assertRaises(ValueError):
            add_entry("publication", {"title": "P", "authors": "A", "venue": "V", "year": "2026", "url": "example.com"}, path)

    def test_rejects_duplicate_publication_and_activity(self):
        publication_path = self.write_yaml(
            "publications.yml",
            "- title: Existing\n  authors: A\n  venue: V\n  year: 2026\n  url: ''\n",
        )
        with self.assertRaises(ValueError):
            add_entry("publication", {"title": " Existing ", "authors": "B", "venue": "W", "year": "2026", "url": ""}, publication_path)

        activity_path = self.write_yaml(
            "activities.yml",
            "- title: Event\n  date: 2026-08-01\n  type: 展示\n  venue: ''\n  description: ''\n  url: ''\n",
        )
        with self.assertRaises(ValueError):
            add_entry("activity", {"title": "event", "date": "2026-08-01", "type": "発表", "venue": "", "description": "", "url": ""}, activity_path)
```

The test module should import the script from `bin/` by adding the repository's `bin` directory to `sys.path`. Its `setUp` helper should create a `TemporaryDirectory`, and `write_yaml` should return a `pathlib.Path` inside it.

### Step 2: テストが想定どおり失敗することを確認する

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: FAIL because `bin/add_site_entry.py` and its public functions do not exist yet. The test file is discovered without requiring a `tests/__init__.py` package marker.

### Step 3: 最小実装を書く

`bin/add_site_entry.py`に次を実装する。

- `argparse`のsubcommand `publication` と `activity`
- 必須文字列を`strip()`し、空文字を拒否する処理
- `publication`の`year`を4桁の整数へ変換する処理
- `activity`の`date`を`YYYY-MM-DD`または`YYYY-MM-DD〜YYYY-MM-DD`として検証する処理
- `datetime.strptime`で実在する日付を検証し、期間は開始日が終了日を超えないことを検証する処理
- `urllib.parse.urlparse`で任意URLのschemeが`http`または`https`、netlocが空でないことを検証する処理
- 重複比較用に、タイトルを小文字化して連続空白を1つに正規化する処理
- 論文の重複キーを正規化タイトルと年、活動の重複キーを正規化タイトルと日付にする処理
- 論文エントリを`title`, `authors`, `venue`, `year`, `url`の順で生成する処理
- 活動エントリを`title`, `date`, `type`, `venue`, `description`, `url`の順で生成する処理
- `yaml.safe_load`で既存YAMLを読み込み、トップレベルがリストであることを検証する処理
- 新しいエントリだけを`yaml.safe_dump([entry], allow_unicode=True, sort_keys=False, width=1000)`でYAML化する処理。既存エントリがある場合は既存テキストの末尾へ追記し、ファイルが空リスト`[]`だけの場合はその部分を新しいリスト項目へ置き換える
- 追記後の内容を一時ファイルに書き、`os.replace`で対象ファイルへ置き換える処理。検証やdumpに失敗した場合は元ファイルを変更しない
- 成功時に追加したエントリをJSON形式で標準出力へ表示し、失敗時はエラーメッセージを標準エラーへ出して終了コード1を返すCLI

CLIの出力先はsubcommandで固定する。

```text
publication -> _data/publications.yml
activity    -> _data/activities.yml
```

CLIの`--output`を指定した場合はそのパスを使う。workflowでは`--output`を指定せず、上記の既定パスを使う。

### Step 4: テストを実行して成功を確認する

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m py_compile bin/add_site_entry.py
```

Expected: 全テストがPASSし、`py_compile`が終了コード0になる。

### Step 5: コミットする

```bash
git add bin/add_site_entry.py tests/test_add_site_entry.py
git commit -m "feat: add validated site content entry script"
```

---

## Task 2: 研究実績追加workflowを実装する

**Files:**
- Create: `.github/workflows/add-publication.yml`

**Interfaces:**
- Consumes: `bin/add_site_entry.py publication`のCLI
- Produces: `_data/publications.yml`への1件の追記、自動commit、default branchへのpush

### Step 1: workflow定義のテスト条件を先に確認する

実装前に、workflowが次の条件を満たす構造になることをチェックリスト化する。

- `workflow_dispatch.inputs`に`title`, `authors`, `venue`, `year`, `url`がある
- `title`, `authors`, `venue`, `year`が`required: true`
- `url`のdefaultが空文字
- `permissions.contents`が`write`
- `concurrency.group`が`content-entry`
- `concurrency.cancel-in-progress`が`false`
- checkoutのtokenが`${{ secrets.SITE_UPDATE_TOKEN }}`
- checkoutのrefが`${{ github.event.repository.default_branch }}`
- `actions/setup-python@v5`でPython `3.13`を使う
- `pyyaml`だけをインストールする
- ユーザー入力をshell文字列へ直接埋め込まず、stepの`env`経由でPythonへ渡す
- `git add`の対象が`_data/publications.yml`だけ
- push先が`${{ github.event.repository.default_branch }}`

### Step 2: workflowを作成する

次の構造で`.github/workflows/add-publication.yml`を作る。

```yaml
name: Add publication

on:
  workflow_dispatch:
    inputs:
      title:
        description: Publication title
        required: true
        type: string
      authors:
        description: Comma-separated authors
        required: true
        type: string
      venue:
        description: Conference or journal
        required: true
        type: string
      year:
        description: Four-digit publication year
        required: true
        type: string
      url:
        description: Optional paper or project URL
        required: false
        default: ""
        type: string

permissions:
  contents: write

concurrency:
  group: content-entry
  cancel-in-progress: false

jobs:
  add-publication:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.SITE_UPDATE_TOKEN }}
          ref: ${{ github.event.repository.default_branch }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install YAML dependency
        run: python -m pip install pyyaml
      - name: Validate and append publication
        env:
          ENTRY_TITLE: ${{ inputs.title }}
          ENTRY_AUTHORS: ${{ inputs.authors }}
          ENTRY_VENUE: ${{ inputs.venue }}
          ENTRY_YEAR: ${{ inputs.year }}
          ENTRY_URL: ${{ inputs.url }}
        run: |
          python bin/add_site_entry.py publication \
            --title "$ENTRY_TITLE" \
            --authors "$ENTRY_AUTHORS" \
            --venue "$ENTRY_VENUE" \
            --year "$ENTRY_YEAR" \
            --url "$ENTRY_URL"
      - name: Commit and push
        env:
          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add _data/publications.yml
          git diff --cached --quiet && exit 0
          git commit -m "content: add publication"
          git push origin "HEAD:${DEFAULT_BRANCH}"
```

The exact input descriptions may be written in Japanese, but the input names must remain stable because the workflow passes them to the CLI.

### Step 3: YAML and shell safetyを確認する

Run:

```bash
python -m pip install pyyaml
python - <<'PY'
from pathlib import Path
import yaml

path = Path(".github/workflows/add-publication.yml")
yaml.safe_load(path.read_text(encoding="utf-8"))
print(f"valid YAML: {path}")
PY
git diff --check -- .github/workflows/add-publication.yml
```

Expected: YAML parseが成功し、diff checkが終了コード0になる。入力値が`${{ inputs.* }}`からshellコードとして実行される場所がないことを目視確認する。

### Step 4: コミットする

```bash
git add .github/workflows/add-publication.yml
git commit -m "feat: add browser publication workflow"
```

---

## Task 3: 活動追加workflowを実装する

**Files:**
- Create: `.github/workflows/add-activity.yml`

**Interfaces:**
- Consumes: `bin/add_site_entry.py activity`のCLI
- Produces: `_data/activities.yml`への1件の追記、自動commit、default branchへのpush

### Step 1: 研究実績workflowとの差分を定義する

活動workflowの入力は`title`, `date`, `type`, `venue`, `description`, `url`とする。

- `title`, `date`, `type`は必須
- `venue`, `description`, `url`は任意でdefaultを空文字にする
- 研究実績workflowと同じ`content-entry` concurrency groupを使う
- 研究実績workflowと同じ`SITE_UPDATE_TOKEN`、Python 3.13、`pyyaml`、default branch pushを使う
- `git add`の対象は`_data/activities.yml`だけにする

### Step 2: workflowを作成する

`.github/workflows/add-activity.yml`を作り、次のCLI呼び出しを含める。

```bash
python bin/add_site_entry.py activity \
  --title "$ENTRY_TITLE" \
  --date "$ENTRY_DATE" \
  --type "$ENTRY_TYPE" \
  --venue "$ENTRY_VENUE" \
  --description "$ENTRY_DESCRIPTION" \
  --url "$ENTRY_URL"
```

研究実績workflowと同じcheckout、setup-python、dependency install、commit、pushの構造を使い、対象ファイルだけを`_data/activities.yml`へ置き換える。

### Step 3: YAMLと差分を検証する

Run:

```bash
python - <<'PY'
from pathlib import Path
import yaml

path = Path(".github/workflows/add-activity.yml")
yaml.safe_load(path.read_text(encoding="utf-8"))
print(f"valid YAML: {path}")
PY
git diff --check -- .github/workflows/add-activity.yml
```

Expected: YAML parseが成功し、diff checkが終了コード0になる。

### Step 4: コミットする

```bash
git add .github/workflows/add-activity.yml
git commit -m "feat: add browser activity workflow"
```

---

## Task 4: 初回設定と日常運用を文書化する

**Files:**
- Create: `docs/content-update.md`

**Interfaces:**
- Consumes: `.github/workflows/add-publication.yml`, `.github/workflows/add-activity.yml`
- Produces: 利用者が初回設定と通常更新を再現できる日本語手順

### Step 1: 文書の内容を作る

`docs/content-update.md`には次の節を含める。

1. この仕組みでできること
2. 初回だけ行う`SITE_UPDATE_TOKEN`の作成とRepository Secretへの登録
3. 研究実績の追加方法
4. 活動の追加方法
5. 入力エラーが出た場合の確認方法
6. 誤登録を戻す方法
7. BibTeXは第1段階では自動更新されないこと

PATの値そのものや、Secretの値を表示する手順は文書に書かない。トークン権限は「対象リポジトリ限定、Contents Read and write」と明記する。

### Step 2: 文書をレビューする

Run:

```bash
git diff --check -- docs/content-update.md
```

Expected: diff checkが終了コード0になる。文書内の通常更新手順に、ローカルエディタ、ターミナル、`git push`が不要であることが明記されている。

### Step 3: コミットする

```bash
git add docs/content-update.md
git commit -m "docs: document browser content update workflow"
```

---

## Task 5: ローカル検証とGitHub上の本番確認を行う

**Files:**
- Test: `tests/test_add_site_entry.py`
- Verify: `bin/add_site_entry.py`, `.github/workflows/add-publication.yml`, `.github/workflows/add-activity.yml`, `docs/content-update.md`

### Step 1: Pythonテストを実行する

Run:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m py_compile bin/add_site_entry.py
git diff --check
```

Expected: 全テストがPASS、コンパイル成功、diff check成功。

### Step 2: 一時コピーを使って実データ形式を検証する

実データを変更しないため、`--output`で一時YAMLを指定する。

```bash
tmp_dir=$(mktemp -d)
cp _data/publications.yml "$tmp_dir/publications.yml"
python bin/add_site_entry.py publication \
  --title "Verification-only publication" \
  --authors "Test Author" \
  --venue "Verification Venue" \
  --year 2099 \
  --url https://example.com/verification \
  --output "$tmp_dir/publications.yml"
```

実データへ検証用レコードを追加しない。

### Step 3: Secretを設定する

GitHubリポジトリの設定で、対象リポジトリ限定のfine-grained PATを作成し、Repository Secret名を`SITE_UPDATE_TOKEN`にする。Contents権限はRead and writeだけにする。

### Step 4: 研究実績workflowを本番実行する

GitHub Actionsの`Add publication`をdefault branchに対して手動実行し、実在する新規または検証用の公開可能な研究実績を1件入力する。

確認項目:

- workflowが成功する
- default branchに`content: add publication` commitが1件作成される
- 変更ファイルが`_data/publications.yml`だけである
- `deploy.yml`が起動してJekyll buildが成功する
- `/publications/`に入力内容が表示される

検証用レコードを使った場合は、サイトへ残さないようにGitHub上でそのcommitをrevertし、revert後のdeploy成功も確認する。

### Step 5: 活動workflowを本番実行する

GitHub Actionsの`Add activity`を手動実行し、実在する活動を1件入力する。

確認項目:

- workflowが成功する
- default branchに`content: add activity` commitが1件作成される
- 変更ファイルが`_data/activities.yml`だけである
- `deploy.yml`が起動してJekyll buildが成功する
- `/activities/`とAboutページの最近の活動に入力内容が表示される

### Step 6: 最終確認を行う

Dockerが利用できる環境では、既存手順に従って次を実行する。

```bash
docker compose up --build
```

ブラウザで`http://localhost:8080/publications/`、`http://localhost:8080/activities/`、トップページを確認し、既存のナビゲーション、外部リンク、ライト・ダーク表示が壊れていないことを確認する。

---

## Plan Self-Review

- 仕様書の必須目標はTask 1〜5でカバーしている。
- 認証方式は`SITE_UPDATE_TOKEN`と権限範囲を固定している。
- 入力値はworkflowの`env`経由で渡し、shell injectionを避ける構成にしている。
- YAML全体の再ダンプを避ける実装方針をTask 1に含めている。
- 重複、日付、URL、YAML破損、同時実行、誤登録の検証・復旧をカバーしている。
- BibTeX統合と独自管理画面は仕様書どおりスコープ外にしている。
- 既存のdeploy workflowを変更せず、通常のpushトリガーを利用する。
