# 日英ナビとトップページの整理 実装計画

> **For agentic workers:** Implement this plan task-by-task, either with a fresh subagent per task plus a reviewer (recommended) or inline in one session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ナビを今の言語のページだけにして言語の切り替えを置き、日英のトップに研究・論文・活動への導線をそろえる。

**Architecture:** 各ページの front matter に `lang` と `ref` を持たせ、`header.liquid` がそれを見てナビと切り替え先を決める。文言と活動の種別の英語名は `_data/i18n.yml` にまとめ、一覧の include は `lang` の引数で日英を出し分ける。ページ構成の決まりは Python のテストで固定し、Liquid の表示は Docker のビルド結果を `curl` で確かめる。

**Tech Stack:** Jekyll（al-folio v0.16.3）、Liquid、Python 3 の unittest と PyYAML、Docker、Prettier。

**Spec:** `docs/superpowers/specs/2026-11-26-bilingual-navigation-design.md`

## Global Constraints

- `_config.yml` の `url: "https://Kmattsun28.github.io"` と空の `baseurl` は変えない。
- URL は日本語を `/` の下、英語を `/en/` の下に置く。対は `ref` が同じ日英の2ページ。
- 既存の活動・論文の項目は変えず、任意の項目（`title_en`、`description_en`）だけを足す。
- 「Add activity」ワークフローと `bin/add_site_entry.py` は変えない。
- `_site/` は読まない、編集しない。
- 無関係な `.claude/*`、`AGENTS.md`、`.github/copilot-instructions.md` のローカル変更をコミットしない。`git add` はファイルを名指しする。
- コミットの形式は `<type>: <description>`。末尾に `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` を付ける。
- このマシンのシステムの `python3` は Xcode のライセンスで止まる。テストは `uv run --with pyyaml python -m unittest discover -s tests -p 'test_*.py'` で動かす。
- 開発サーバーはコンテナ `hp-dev`（http://localhost:8080）で動いている。止まっていたら次で起動する。

  ```bash
  docker rm -f hp-dev 2>/dev/null; docker compose run -d --service-ports --name hp-dev --entrypoint bash jekyll -c "git config --global --add safe.directory '*'; bundle install --quiet && bundle exec jekyll serve --watch --port=8080 --host=0.0.0.0 --livereload --force_polling"
  ```

  `_config.yml` を変えたときは `docker restart hp-dev` で読み直す。

## Review Focus

- `lang` を持たないページ（404 など）: ナビは日本語のページで出し、言語の切り替えは英語のトップへ向く。Task 2 の確認で `/404.html` を見る。
- 対応表にない活動の種別: 英語版でも日本語の種別をそのまま出す。Task 1 のテストで、ワークフローの選択肢すべてに英語名があることを固定する。
- 期間の日付（`2025-11-27〜2025-11-28`）: 英語版でも開始の年月が「Nov 2025」と出る。Task 3 の確認で見る。
- `title_en` が空文字や未記入の活動: 日本語のタイトルを出す。Task 3 の確認で、英語の項目を入れない1件を残して見る。
- 古い `/research-ja/` を開いた人: `/research/` へ移る。Task 1 のテストで転送ページの front matter を、Task 6 でブラウザの動きを確かめる。

---

### Task 1: ページ構成を日英の対にそろえる

**Files:**

- Create: `tests/test_page_pairs.py`
- Create: `_data/i18n.yml`
- Create: `_pages/research-en.md`、`_pages/publications-en.md`、`_pages/activities-en.md`
- Modify: `_pages/research.md`（英語 → 日本語）、`_pages/research-ja.md`（転送だけのページ）、`_pages/publications.md`、`_pages/activities-ja.md`、`_pages/about.md`、`_pages/about-ja.md`（front matter だけ）

**Interfaces:**

- Produces: 全ページの front matter の `lang`（`ja`/`en`）と `ref`（`home`/`research`/`publications`/`activities`）。`nav_order` は研究 1、論文 2、活動 3。
- Produces: `_data/i18n.yml` のキー。`ja` と `en` の下に `site_name`、`home_url`、`lang_label`、`see_research`、`publications`、`all_publications`、`count_suffix`、`recent_activities`、`all_activities`、`date_format`。最上位に `activity_types_en`（日本語の種別 → 英語名）。

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_page_pairs.py`:

```python
import re
import unittest
from collections import Counter
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = REPO_ROOT / "_pages"
I18N_PATH = REPO_ROOT / "_data" / "i18n.yml"
ACTIVITY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "add-activity.yml"
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def load_front_matter(path: Path) -> dict:
    match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
    if match is None:
        raise AssertionError(f"{path.name} has no front matter")
    return yaml.safe_load(match.group(1)) or {}


def load_pages() -> dict:
    return {path.name: load_front_matter(path) for path in sorted(PAGES_DIR.glob("*.md"))}


class PagePairTests(unittest.TestCase):
    def setUp(self):
        self.pages = load_pages()

    def test_every_ref_has_exactly_one_page_per_language(self):
        refs = {}
        for name, fm in self.pages.items():
            if "ref" in fm:
                refs.setdefault(fm["ref"], []).append((fm.get("lang"), name))
        self.assertEqual({"home", "research", "publications", "activities"}, set(refs))
        for ref, entries in refs.items():
            langs = sorted(lang for lang, _ in entries)
            self.assertEqual(["en", "ja"], langs, f"ref {ref}: {entries}")

    def test_permalinks_are_unique(self):
        permalinks = Counter(fm.get("permalink") for fm in self.pages.values())
        duplicates = [link for link, count in permalinks.items() if link and count > 1]
        self.assertEqual([], duplicates)

    def test_english_pages_live_under_en(self):
        for name, fm in self.pages.items():
            permalink = fm.get("permalink", "")
            if fm.get("lang") == "en":
                self.assertTrue(permalink.startswith("/en/"), name)
            if fm.get("lang") == "ja":
                self.assertFalse(permalink.startswith("/en/"), name)

    def test_nav_pages_have_language_and_order(self):
        for name, fm in self.pages.items():
            if fm.get("nav"):
                self.assertIn(fm.get("lang"), ("ja", "en"), name)
                self.assertNotEqual("home", fm.get("ref"), name)
                self.assertIsInstance(fm.get("nav_order"), int, name)

    def test_old_japanese_research_url_redirects(self):
        fm = self.pages["research-ja.md"]
        self.assertEqual("/research-ja/", fm["permalink"])
        self.assertEqual("/research/", fm["redirect"])
        self.assertNotIn("ref", fm)
        self.assertFalse(fm.get("nav", False))


class I18nTests(unittest.TestCase):
    def setUp(self):
        self.i18n = yaml.safe_load(I18N_PATH.read_text(encoding="utf-8"))

    def test_both_languages_define_the_same_keys(self):
        self.assertEqual(set(self.i18n["ja"]), set(self.i18n["en"]))
        self.assertEqual("/", self.i18n["ja"]["home_url"])
        self.assertEqual("/en/", self.i18n["en"]["home_url"])

    def test_every_workflow_activity_type_has_english_name(self):
        workflow = yaml.safe_load(ACTIVITY_WORKFLOW.read_text(encoding="utf-8"))
        on_block = workflow.get("on", workflow.get(True))
        options = on_block["workflow_dispatch"]["inputs"]["type"]["options"]
        missing = [option for option in options if option not in self.i18n["activity_types_en"]]
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
```

（PyYAML は YAML の `on:` キーを真偽値の `True` として読むため、`workflow.get(True)` も見る。）

- [ ] **Step 2: テストが失敗することを確かめる**

Run: `uv run --with pyyaml python -m unittest tests.test_page_pairs -v`
Expected: FAIL（`ref` がない、`research-ja.md` に `redirect` がない、`_data/i18n.yml` がない）

- [ ] **Step 3: `_data/i18n.yml` を作る**

```yaml
# サイトの短い文言と、活動の種別の英語名。
# 活動の種別を増やしたときは activity_types_en にも足す（tests/test_page_pairs.py が確かめる）。
ja:
  site_name: "松本亘平"
  home_url: "/"
  lang_label: "日本語"
  see_research: "研究紹介を見る"
  publications: "論文"
  all_publications: "すべての論文"
  count_suffix: "件"
  recent_activities: "最近の活動"
  all_activities: "すべての活動"
  date_format: "%Y年%m月"
en:
  site_name: "Kohei Matsumoto"
  home_url: "/en/"
  lang_label: "EN"
  see_research: "See research"
  publications: "Publications"
  all_publications: "All publications"
  count_suffix: ""
  recent_activities: "Recent Activities"
  all_activities: "All activities"
  date_format: "%b %Y"
activity_types_en:
  シンポジウム: "Symposium"
  国内学会発表: "Domestic Conference"
  国際学会発表: "International Conference"
  受賞: "Award"
  展示: "Exhibition"
  イベント: "Event"
  その他: "Other"
```

`lang_label` は、そのページへ切り替えるリンクに出す文字。日本語のページには `en.lang_label`（EN）、英語のページには `ja.lang_label`（日本語）が出る。

- [ ] **Step 4: 研究ページを入れ替える**

```bash
git mv _pages/research.md _pages/research-en.md
cp _pages/research-ja.md _pages/research.md
```

`_pages/research-en.md` の front matter を次にし、本文の関連論文のリンク先 `/publications/` を2か所とも `/en/publications/` に変える。

```yaml
---
layout: page
title: Research
permalink: /en/research/
description:
nav: true
nav_order: 1
lang: en
ref: research
---
```

`_pages/research.md`（日本語の本文）の front matter を次にする。本文はそのまま。

```yaml
---
layout: page
title: 研究
permalink: /research/
description:
nav: true
nav_order: 1
lang: ja
ref: research
---
```

`_pages/research-ja.md` の中身全体を次に置き換える（本文なし）。

```yaml
---
layout: page
title: 研究
permalink: /research-ja/
redirect: /research/
lang: ja
---
```

- [ ] **Step 5: 論文と活動のページを日英にする**

`_pages/publications.md`:

```markdown
---
layout: page
title: 論文
permalink: /publications/
description:
nav: true
nav_order: 2
lang: ja
ref: publications
---

{% include publications_list.html publications=site.data.publications %}
```

`_pages/publications-en.md`:

```markdown
---
layout: page
title: Publications
permalink: /en/publications/
description:
nav: true
nav_order: 2
lang: en
ref: publications
---

{% include publications_list.html publications=site.data.publications %}
```

`_pages/activities-ja.md` の front matter に `ref: activities` を足し、`nav_order` を 3 にする。

`_pages/activities-en.md`（`lang="en"` の引数は Task 3 で効くようになる。それまでは日本語で出る）:

```markdown
---
layout: page
title: Activities
permalink: /en/activities/
description:
nav: true
nav_order: 3
lang: en
ref: activities
---

{% include activities_list.html lang="en" %}
```

- [ ] **Step 6: トップの front matter を直す**

`_pages/about-ja.md` と `_pages/about.md` から `nav: true` と `nav_order` の行を消し、`ref: home` を足す。`about-ja.md` の `recent_activities: true` は Task 5 で消すので、ここでは残す。

- [ ] **Step 7: テストが通ることを確かめる**

Run: `uv run --with pyyaml python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: すべて PASS

- [ ] **Step 8: 整形してコミットする**

```bash
npx prettier --write _data/i18n.yml _pages/research.md _pages/research-en.md _pages/research-ja.md _pages/publications.md _pages/publications-en.md _pages/activities-ja.md _pages/activities-en.md _pages/about.md _pages/about-ja.md
git add _data/i18n.yml tests/test_page_pairs.py _pages/research.md _pages/research-en.md _pages/research-ja.md _pages/publications.md _pages/publications-en.md _pages/activities-ja.md _pages/activities-en.md _pages/about.md _pages/about-ja.md
git commit -m "feat: pair Japanese and English pages"
```

（`.py` は Prettier の対象外なので渡さない。）

---

### Task 2: ナビ、名前のリンク、言語の切り替え、`<html lang>`

**Files:**

- Modify: `_includes/header.liquid:4-24`（名前のリンク）、`:46-48`（ページの絞り込み）、`:105` の直前（言語の切り替え）
- Modify: `_layouts/default.liquid:2`
- Modify: `_sass/` のうち、ナビの色を定義しているファイル（Step 4 で探す）

**Interfaces:**

- Consumes: Task 1 の `lang`、`ref`、`site.data.i18n`
- Produces: `<li class="nav-item lang-switch">` の中の `<a class="nav-link" hreflang=… lang=…>`

- [ ] **Step 1: 名前のリンクを全ページに出す**

`_includes/header.liquid` の `<div class="container">` の直後から、`{% elsif site.enable_navbar_social %}…{% endif %}` の終わりまで（4〜24行目）を次に置き換える。

```liquid
{% assign current_lang = page.lang | default: 'ja' %}
{% if current_lang == 'en' %}
  {% assign other_lang = 'ja' %}
{% else %}
  {% assign other_lang = 'en' %}
{% endif %}
{% assign t = site.data.i18n[current_lang] %}
<a class="navbar-brand title font-weight-lighter" href="{{ t.home_url | relative_url }}">
  {{- t.site_name -}}
</a>
```

- [ ] **Step 2: ナビを今の言語のページに絞る**

`{% if p.nav and p.autogen == null %}` を次に変える。

```liquid
            {% if p.nav and p.autogen == null and p.lang == current_lang %}
```

- [ ] **Step 3: 言語の切り替えを置く**

`{% if site.search_enabled %}` の直前に入れる。

```liquid
<!-- Language switch -->
{% assign switch_url = site.data.i18n[other_lang].home_url %}
{% if page.ref %}
  {% for p in site.pages %}
    {% if p.ref == page.ref and p.lang == other_lang %}
      {% assign switch_url = p.url %}
    {% endif %}
  {% endfor %}
{% endif %}
<li class="nav-item lang-switch">
  <a class="nav-link" href="{{ switch_url | relative_url }}" hreflang="{{ other_lang }}" lang="{{ other_lang }}">
    {{- site.data.i18n[other_lang].lang_label -}}
  </a>
</li>
```

`_layouts/default.liquid` の2行目を次にする。

```liquid
<html lang="{{ page.lang | default: site.lang }}">
```

- [ ] **Step 4: 日本語の名前がナビの書体で崩れないか見る**

`grep -rn "navbar-brand" _sass/` で、名前の書体と大文字化（`text-transform`）の指定を探す。ブラウザで `/` を開き、「松本亘平」が読めるかを見る。崩れていなければ何もしない。崩れていれば、見つけたファイルの `.navbar-brand` の規則の後ろに次を足す。

```scss
html[lang="ja"] .navbar-brand.title {
  text-transform: none;
  letter-spacing: normal;
}
```

- [ ] **Step 5: ビルド結果を確かめる**

サーバーが再生成を終えるのを待ってから実行する（`docker logs hp-dev --tail 3` に `done in` が出る）。

```bash
for u in / /en/ /research/ /en/research/ /publications/ /en/publications/ /activities/ /en/activities/ /404.html; do
  h=$(curl -s "http://localhost:8080$u")
  echo "== $u"
  echo "$h" | grep -o '<html lang="[a-z]*"'
  echo "$h" | grep -oE 'class="nav-link" href="[^"]*"( hreflang="[a-z]+")?' | sed 's/class="nav-link" //'
  echo "$h" | grep -oE 'navbar-brand[^>]*href="[^"]*"' | grep -oE 'href="[^"]*"'
done
```

Expected:

- `/`、`/research/`、`/publications/`、`/activities/`、`/404.html` は `lang="ja"`。ナビは `/research/`、`/publications/`、`/activities/` の3つで、切り替えは対の英語ページ（`/404.html` は `/en/`）。名前のリンクは `/`。
- `/en/…` の4ページは `lang="en"`。ナビは `/en/research/`、`/en/publications/`、`/en/activities/`。切り替えは対の日本語ページ。名前のリンクは `/en/`。
- どのページにも `/research-ja/` へのリンクがない。

- [ ] **Step 6: 画面で確かめる**

```bash
B=$(ls -d ~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell | tail -1)
S=/private/tmp/claude-501/-Users-kmattsun-Documents-01-Workspace-Kmattsun28-github-io/5880965b-1327-41cb-bce7-22a36cad5a80/scratchpad/shots
for p in "/:t2-ja" "/en/research/:t2-en"; do u=${p%%:*}; n=${p##*:}
  "$B" --disable-gpu --hide-scrollbars --window-size=1440,600 --screenshot=$S/$n-pc.png "http://localhost:8080$u"
  "$B" --disable-gpu --hide-scrollbars --window-size=390,800 --screenshot=$S/$n-sp.png "http://localhost:8080$u"
done
```

Read で画像を見る。PC 幅でナビが1行に収まり、名前と切り替えが読めること。390px 幅でハンバーガーが右にあり、名前が折り返さないこと。

- [ ] **Step 7: 整形してコミットする**

```bash
npx prettier --write _includes/header.liquid _layouts/default.liquid
git add _includes/header.liquid _layouts/default.liquid
git commit -m "feat: show navigation and language switch per language"
```

Step 4 で `_sass/` を変えたときは、そのファイルも名指しで `git add` に加える。

---

### Task 3: 活動の一覧を日英で出す

**Files:**

- Modify: `_includes/activities_list.html`
- Modify: `_data/activities.yml`
- Modify: `docs/content-update.md`

**Interfaces:**

- Consumes: `site.data.i18n[lang].date_format`、`site.data.i18n.activity_types_en`
- Produces: `{% include activities_list.html lang="en" limit=3 %}`。`lang` の省略時は `ja`、`limit` の省略時は全件。

- [ ] **Step 1: include を書き換える**

`_includes/activities_list.html` の全体を次にする（見た目の指定は今のまま。直すのは別の作業）。

```liquid
{% assign lang = include.lang | default: 'ja' %}
{% assign t = site.data.i18n[lang] %}
{% assign sorted = site.data.activities | sort: 'date' | reverse %}
{% if include.limit %}
  {% assign display = sorted | slice: 0, include.limit %}
{% else %}
  {% assign display = sorted %}
{% endif %}

<ul class="activities-list" style="list-style: none; padding: 0">
  {% for act in display %}
    {% assign title = act.title %}
    {% assign description = act.description %}
    {% assign type_label = act.type %}
    {% if lang == 'en' %}
      {% if act.title_en and act.title_en != '' %}{% assign title = act.title_en %}{% endif %}
      {% if act.description_en and act.description_en != '' %}{% assign description = act.description_en %}{% endif %}
      {% assign type_label = site.data.i18n.activity_types_en[act.type] | default: act.type %}
    {% endif %}
    <li style="margin-bottom: 1em">
      <span style="color: #888; font-size: 0.85em; margin-right: 0.5em">{{ act.date | date: t.date_format }}</span>
      <span
        class="badge"
        style="background-color: #4a90d9; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.78em; margin-right: 0.5em"
      >
        {{- type_label -}}
      </span>
      {% if act.url and act.url != '' %}
        <a href="{{ act.url }}" target="_blank" rel="noopener noreferrer">{{ title }}</a>
      {% else %}
        {{ title }}
      {% endif %}
      {% if act.venue and act.venue != '' %}
        <span style="color: #666; font-style: italic">&mdash; {{ act.venue }}</span>
      {% endif %}
      {% if description and description != '' %}
        <div style="color: #555; font-size: 0.9em; margin-top: 0.2em">{{ description }}</div>
      {% endif %}
    </li>
  {% endfor %}
</ul>
```

- [ ] **Step 2: 英語の項目を足す**

`_data/activities.yml` の先頭のコメントに2行足す。

```yaml
#   title_en:       英語のタイトル (optional。空なら英語版でも title を出す)
#   description_en: 英語の補足説明 (optional。空なら英語版でも description を出す)
```

既存の5件のうち4件に、次の下書きを `description:` の次の行として足す。英訳は本人に確かめてもらう（Task 6 の Step 4）。「東山動植物園 リアリティ・オブ・ケニア」には足さず、日本語に戻る動きを確かめる1件として残す。

```yaml
# JST CREST Internet of Realities 第3回シンポジウム
title_en: "JST CREST Internet of Realities 3rd Symposium"
description_en: "Presented a poster at the 3rd JST CREST Internet of Realities Symposium."
# MBL/ITS研究会 WiP奨励賞
title_en: "WiP Encouragement Award, IPSJ MBL/ITS Joint Meeting"
description_en: "Received the WiP Encouragement Award at the joint meeting of the IPSJ SIG-MBL and SIG-ITS."
# IEEE MetaCom2025
title_en: "IEEE MetaCom 2025"
description_en: "Presented at IEEE MetaCom 2025."
# JST CREST Internet of Realities 第2回シンポジウム
title_en: "JST CREST Internet of Realities 2nd Symposium"
description_en: "Presented a poster at the 2nd JST CREST Internet of Realities Symposium."
```

（`#` の行は、どの項目に足すかを示すための見出しで、ファイルには書かない。）

- [ ] **Step 3: 手順書に書き足す**

`docs/content-update.md` の「## 活動を追加する」の節の最後（「日付は実在する日付を入力し、…」の段落のあと）に次を足す。

```markdown
英語版のページ（`/en/` と `/en/activities/`）に英語で出したいときは、登録したあとに `_data/activities.yml` の該当する項目を直接編集し、`title_en` と `description_en` を足します。書かなければ、英語版にも日本語のタイトルと説明が出ます。種別は自動で英語になります。
```

- [ ] **Step 4: ビルド結果を確かめる**

```bash
curl -s http://localhost:8080/en/activities/ | grep -oE '>(Mar|Nov|Aug|Jan) 20[0-9]{2}<|class="badge"[^>]*>[^<]*|noopener noreferrer">[^<]*' | sed 's/.*>//'
curl -s http://localhost:8080/activities/ | grep -oE '>20[0-9]{2}年[0-9]{2}月<' | head -5
```

Expected:

- 英語版の日付が「Mar 2026」「Nov 2025」「Aug 2025」「Mar 2025」「Jan 2025」。
- 英語版の種別が Symposium、Domestic Conference、International Conference、Symposium、Event。
- 英語版のタイトルが Step 2 の英語で、東山動植物園の1件だけ日本語のまま。
- 日本語版は今と同じ「2026年03月」などの表示。

- [ ] **Step 5: テストを流して、整形してコミットする**

```bash
uv run --with pyyaml python -m unittest discover -s tests -p 'test_*.py'
npx prettier --write _includes/activities_list.html _data/activities.yml docs/content-update.md
git add _includes/activities_list.html _data/activities.yml docs/content-update.md
git commit -m "feat: show activities in English on English pages"
```

---

### Task 4: 論文の名前の太字とトップ用の一覧

**Files:**

- Modify: `_config.yml:10-12`
- Modify: `_includes/publications_list.html`（著者名を分ける行）
- Create: `_includes/publications_recent.html`

**Interfaces:**

- Produces: `{% include publications_recent.html limit=3 %}`。`year` の降順で上位 `limit` 件（省略時は3件）を、タイトルと掲載先だけの `<ul class="pub-recent">` で出す。

- [ ] **Step 1: 自分の名前の表記を足す**

`_config.yml` の `author_names` に1行足す。

```yaml
author_names: # used for author bolding in publications (add as many as needed)
  - "Kohei Matsumoto" # English name
  - "松本 亘平" # Japanese name
  - "松本亘平" # Japanese name without space (used in _data/publications.yml)
```

- [ ] **Step 2: 全角の区切りを扱う**

`_includes/publications_list.html` の `{% assign authors = pub.authors | split: ", " %}` を次に変える。

```liquid
{% assign authors = pub.authors | replace: '，', ', ' | split: ', ' %}
```

- [ ] **Step 3: トップ用の一覧を作る**

`_includes/publications_recent.html`:

```liquid
{% assign limit = include.limit | default: 3 %}
{% assign groups = site.data.publications | group_by: 'year' | sort: 'name' | reverse %}
{% assign shown = 0 %}
<ul class="pub-recent">
  {% for group in groups %}
    {% for pub in group.items %}
      {% if shown < limit %}
        <li>
          {% if pub.url %}
            <a href="{{ pub.url }}" target="_blank" rel="noopener noreferrer">{{ pub.title }}</a>
          {% else %}
            {{ pub.title }}
          {% endif %}
          <div class="pub-venue" style="font-style: italic">{{ pub.venue }}</div>
        </li>
        {% assign shown = shown | plus: 1 %}
      {% endif %}
    {% endfor %}
  {% endfor %}
</ul>
```

（Liquid の `sort` は同じ年の中の順を保つとは限らない。`group_by` で年ごとにまとめれば、年の中はデータの並びのまま出る。）

- [ ] **Step 4: ビルド結果を確かめる**

`_config.yml` を変えたので `docker restart hp-dev` をして、再生成を待つ。

```bash
curl -s http://localhost:8080/publications/ | grep -o '<strong>[^<]*</strong>'
```

Expected: `<strong>Kohei Matsumoto</strong>` が2つ、`<strong>松本亘平</strong>` が2つ。

`publications_recent.html` はまだどこからも呼ばれていない。表示は Task 5 で確かめる。

- [ ] **Step 5: テストを流して、整形してコミットする**

```bash
uv run --with pyyaml python -m unittest discover -s tests -p 'test_*.py'
npx prettier --write _config.yml _includes/publications_list.html _includes/publications_recent.html
git add _config.yml _includes/publications_list.html _includes/publications_recent.html
git commit -m "feat: bold Japanese author name and add recent publications include"
```

---

### Task 5: 日英のトップの並びをそろえる

**Files:**

- Modify: `_pages/about-ja.md`（本文と `recent_activities`）
- Modify: `_pages/about.md`（本文）
- Modify: `_layouts/about.liquid:69-75`（日本語固定の「最近の活動」の節を消す）

**Interfaces:**

- Consumes: `publications_recent.html`（Task 4）、`activities_list.html lang=…`（Task 3）

- [ ] **Step 1: レイアウトの日本語固定の節を消す**

`_layouts/about.liquid` の次のブロックを消す。

```liquid
<!-- Recent activities -->
{% if page.recent_activities %}
  <h2>
    <a href="{{ '/activities/' | relative_url }}" style="color: inherit">最近の活動</a>
  </h2>
  {% include activities_list.html limit=3 %}
{% endif %}
```

`_pages/about-ja.md` の front matter から `recent_activities: true` を消す。

- [ ] **Step 2: 日本語のトップの本文を書き換える**

`_pages/about-ja.md` の front matter のあとの本文全体を次にする。

```markdown
名古屋大学大学院 工学研究科 情報・通信工学専攻の博士前期課程1年です。

## 研究内容

- ヒューマンコンピュータインタラクション（HCI）
- 推薦システム
- 異文化コミュニケーション

[{{ site.data.i18n.ja.see_research }} →](/research/)

## {{ site.data.i18n.ja.publications }}

{% include publications_recent.html limit=3 %}

[{{ site.data.i18n.ja.all_publications }}（{{ site.data.publications | size }}{{ site.data.i18n.ja.count_suffix }}）→](/publications/)

## {{ site.data.i18n.ja.recent_activities }}

{% include activities_list.html limit=3 lang="ja" %}

[{{ site.data.i18n.ja.all_activities }} →](/activities/)

## 学歴

2026年4月~ 名古屋大学大学院工学研究科情報・通信工学専攻 博士前期課程

2022年4月~2026年3月 名古屋大学工学部電気電子情報工学科

2019年4月~2022年3月 愛知県立豊田西高等学校

## 趣味

- サッカー
- スキー
- 海外旅行
```

- [ ] **Step 3: 英語のトップの本文を書き換える**

`_pages/about.md` の本文全体を次にする。

```markdown
I am a first-year Master's student in the Department of Information and Communication Engineering at the Graduate School of Engineering, Nagoya University.

## Research Interests

- Human-Computer Interaction (HCI)
- Recommender Systems
- Intercultural Communication

[{{ site.data.i18n.en.see_research }} →](/en/research/)

## {{ site.data.i18n.en.publications }}

{% include publications_recent.html limit=3 %}

[{{ site.data.i18n.en.all_publications }} ({{ site.data.publications | size }}) →](/en/publications/)

## {{ site.data.i18n.en.recent_activities }}

{% include activities_list.html limit=3 lang="en" %}

[{{ site.data.i18n.en.all_activities }} →](/en/activities/)

## Education

2026 Apr. - Present: Master's Program in Information and Communication Engineering, Graduate School of Engineering, Nagoya University

2022 Apr. - 2026 Mar.: Bachelor of Engineering in Electrical, Electronics and Information Engineering, School of Engineering, Nagoya University

2019 Apr. - 2022 Mar.: Aichi Prefectural Toyotanishi High School

## Hobbies

- Soccer
- Skiing
- Traveling abroad
```

- [ ] **Step 4: ビルド結果を確かめる**

```bash
for u in / /en/; do echo "== $u"; curl -s "http://localhost:8080$u" | grep -oE '<h2[^>]*>[^<]*|href="(/en)?/(research|publications|activities)/"' ; done
```

Expected:

- `/` の見出しが 研究内容 → 論文 → 最近の活動 → 学歴 → 趣味 の順。
- `/en/` の見出しが Research Interests → Publications → Recent Activities → Education → Hobbies の順。
- 各トップに、同じ言語の研究、論文、活動へのリンクがある。
- `/` の「すべての論文（4件）」、`/en/` の「All publications (4)」。

Markdown の中の `<ul>` が `<p>` で包まれたり、`{% include %}` がそのまま文字で出たりしていないかも、`curl -s http://localhost:8080/ | grep -n "include\|pub-recent"` で見る。

- [ ] **Step 5: 画面で確かめる**

```bash
B=$(ls -d ~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell | tail -1)
S=/private/tmp/claude-501/-Users-kmattsun-Documents-01-Workspace-Kmattsun28-github-io/5880965b-1327-41cb-bce7-22a36cad5a80/scratchpad/shots
for p in "/:t5-ja" "/en/:t5-en"; do u=${p%%:*}; n=${p##*:}
  "$B" --disable-gpu --hide-scrollbars --window-size=1440,2400 --screenshot=$S/$n-pc.png "http://localhost:8080$u"
  "$B" --disable-gpu --hide-scrollbars --window-size=390,3200 --screenshot=$S/$n-sp.png "http://localhost:8080$u"
done
```

Read で4枚を見る。写真の回り込みで見出しが崩れていないこと、論文と活動の3件が読めること。

- [ ] **Step 6: テストを流して、整形してコミットする**

```bash
uv run --with pyyaml python -m unittest discover -s tests -p 'test_*.py'
npx prettier --write _pages/about-ja.md _pages/about.md _layouts/about.liquid
git add _pages/about-ja.md _pages/about.md _layouts/about.liquid
git commit -m "feat: align Japanese and English homepages"
```

---

### Task 6: 全体の確認と別系統のレビュー

**Files:** なし（直すところが見つかったときだけ、そのファイル）

- [ ] **Step 1: テストと整形**

```bash
uv run --with pyyaml python -m unittest discover -s tests -p 'test_*.py'
npx prettier --check $(git diff --name-only main...HEAD | grep -E '\.(md|ya?ml|liquid|html|scss)$')
```

Expected: すべて PASS、整形の警告なし。

- [ ] **Step 2: 転送とダークモード**

```bash
curl -s http://localhost:8080/research-ja/ | grep -oE 'http-equiv="refresh"[^>]*'
```

Expected: `url=/research/` を含む `refresh` の meta がある。

ダークモードのスクリーンショットを撮り、言語の切り替えと名前が読めることを確かめる。

```bash
B=$(ls -d ~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell | tail -1)
S=/private/tmp/claude-501/-Users-kmattsun-Documents-01-Workspace-Kmattsun28-github-io/5880965b-1327-41cb-bce7-22a36cad5a80/scratchpad/shots
"$B" --disable-gpu --hide-scrollbars --force-dark-mode --blink-settings=preferredColorScheme=0 --window-size=1440,700 --screenshot=$S/t6-dark.png http://localhost:8080/en/
```

- [ ] **Step 3: Codex にレビューを頼む**

```bash
git diff main...HEAD > /private/tmp/claude-501/-Users-kmattsun-Documents-01-Workspace-Kmattsun28-github-io/5880965b-1327-41cb-bce7-22a36cad5a80/scratchpad/branch.diff
codex exec -s read-only --skip-git-repo-check -C "$(pwd)" "Jekyll（al-folio）サイトの日英ナビ整理の差分をレビューしてください。差分は /private/tmp/claude-501/-Users-kmattsun-Documents-01-Workspace-Kmattsun28-github-io/5880965b-1327-41cb-bce7-22a36cad5a80/scratchpad/branch.diff、仕様は docs/superpowers/specs/2026-11-26-bilingual-navigation-design.md です。Liquid の誤り、仕様との食い違い、日英どちらかで壊れるページ、アクセシビリティの問題を、重要な順に挙げてください。不確かな点と、作業を止めている問題を必ず挙げてください。ファイルは編集しないでください。"
```

指摘を1つずつ確かめ、正しいものだけを直す。直したら Step 1 と、該当する Task の確認をもう一度流し、`fix:` でコミットする。

- [ ] **Step 4: 本人に確かめてもらう**

次を利用者に見せて確認をもらう。

- Task 3 の英訳の下書き4件
- 日本語のトップに足した自己紹介の1文
- 日英のトップの PC 幅とスマホ幅のスクリーンショット

直しがあれば反映してコミットする。PR を作るかどうかは、ここで利用者に聞く。
