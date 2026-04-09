# GitHub Pages 個人サイト 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** al-folioをベースにした日英バイリンガルのアカデミックポートフォリオサイト（About / Publications / Research）をGitHub Pagesで公開する

**Architecture:** al-folioテンプレートをベースに、BibTeXの代わりにYAMLで論文管理するカスタムPublicationsテンプレートを実装する。日英切り替えは別ページファイル＋ナビゲーションリンクで対応する。著者名のボールドは`_config.yml`に設定した名前とLiquidテンプレートで自動処理する。

**Tech Stack:** Jekyll (al-folio), GitHub Pages, GitHub Actions, Liquid templates, YAML

---

## ファイル構成

```
_config.yml                        # サイト設定（名前・所属・SNS・著者名）
_data/
  publications.yml                 # 論文データ（YAMLで管理）
_pages/
  about.md                         # About（EN、トップページ）
  about-ja.md                      # About（JP）
  publications.md                  # Publications（EN/JP共通）
  research.md                      # Research（EN）
  research-ja.md                   # Research（JP）
_includes/
  publications_list.html           # YAMLベース論文リストのカスタムinclude
assets/
  img/
    prof_pic.jpg                   # プロフィール写真（差し替え用）
  pdf/
    cv.pdf                         # CV（差し替え用）
docs/
  superpowers/
    specs/2026-04-09-github-pages-design.md
    plans/2026-04-09-github-pages-site.md
```

---

## Task 1: al-folioテンプレートの取り込み

**Files:**
- Create: リポジトリルート以下（al-folioの全ファイル）

- [ ] **Step 1: al-folioをクローンしてファイルをコピー**

```bash
cd /tmp
git clone --depth 1 https://github.com/alshedivat/al-folio.git al-folio-template
cd /home/mattsun/workspace/github.io
# al-folioのファイルをコピー（docsディレクトリは保持）
cp -r /tmp/al-folio-template/. .
# 念のため確認
ls
```

Expected: `_config.yml`, `_pages/`, `_includes/`, `_layouts/` 等が存在する

- [ ] **Step 2: 不要なサンプルデータを削除**

```bash
# al-folioのサンプル論文（BibTeX）は後で独自YAMLに置き換えるが、まずはそのまま残す
# サンプルニュース記事は削除
rm -rf _news/
# サンプルブログ記事は削除
rm -rf _posts/
```

- [ ] **Step 3: コミット**

```bash
git add .
git commit -m "feat: add al-folio template as base"
```

---

## Task 2: `_config.yml` の基本設定

**Files:**
- Modify: `_config.yml`

- [ ] **Step 1: `_config.yml` を開いて基本情報を確認**

```bash
head -80 _config.yml
```

- [ ] **Step 2: 基本情報を設定**

`_config.yml` の以下の項目を実際の情報に書き換える（`# EDIT:` のある行）:

```yaml
# ----------------------------
# SITE SETTINGS
# ----------------------------
title: "Your Name"                   # EDIT: 自分の名前（英語）
first_name: "Your"                   # EDIT: 名
last_name: "Name"                    # EDIT: 姓
email: you@example.com               # EDIT: メールアドレス
description: "Researcher in ..."     # EDIT: 一行の研究紹介（英語）
footer_text: ""

# カスタム設定：著者名ボールド用（姓名どちらか一意に識別できる文字列）
author_name: "Your Name"             # EDIT: 論文著者リストでボールドにする自分の名前

# ----------------------------
# SOCIAL
# ----------------------------
github_username: your-github         # EDIT: GitHubユーザー名
scholar_userid: your-scholar-id      # EDIT: Google Scholar ID（プロフィールURLのuserパラメータ）
linkedin_username: ""                # EDIT: LinkedIn（任意）
twitter_username: ""                 # EDIT: Twitter/X（任意）

# ----------------------------
# BUILD
# ----------------------------
url: "https://username.github.io"    # EDIT: GitHubユーザー名に合わせて変更
baseurl: ""
```

- [ ] **Step 3: コミット**

```bash
git add _config.yml
git commit -m "config: set site title, author info, and social links"
```

---

## Task 3: Aboutページのカスタマイズ（EN）

**Files:**
- Modify: `_pages/about.md`

- [ ] **Step 1: 既存のabout.mdを確認**

```bash
cat _pages/about.md
```

- [ ] **Step 2: about.md を書き換え**

`_pages/about.md` の内容を以下に置き換える（プロフィール写真＋名前・所属・リンクのみ、自己紹介文なし）:

```markdown
---
layout: about
title: about
permalink: /
subtitle: <a href="#">Affiliation Name</a>. Department, University.

profile:
  align: right
  image: prof_pic.jpg
  image_circular: false

news: false
latest_posts: false
selected_papers: false
social: true
---
```

- [ ] **Step 3: ローカルビルドして確認**

```bash
bundle install
bundle exec jekyll serve --livereload
```

ブラウザで `http://localhost:4000` を開き、About ページが表示されることを確認する。
自己紹介文が表示されないこと、プロフィール写真エリアが表示されることを確認する。

- [ ] **Step 4: コミット**

```bash
git add _pages/about.md
git commit -m "feat: simplify about page (remove bio text)"
```

---

## Task 4: Aboutページ（JP版）の作成

**Files:**
- Create: `_pages/about-ja.md`

- [ ] **Step 1: `_pages/about-ja.md` を作成**

```markdown
---
layout: about
title: about
permalink: /ja/
subtitle: <a href="#">所属名</a>. 学科, 大学名.

profile:
  align: right
  image: prof_pic.jpg
  image_circular: false

news: false
latest_posts: false
selected_papers: false
social: true
---
```

- [ ] **Step 2: about-ja.md のフロントマターにナビゲーション設定を追加**

al-folioでは各ページの `nav: true` と `nav_order` がナビに自動反映される。
`_pages/about.md` のフロントマターも合わせて確認・修正する：

`_pages/about.md` の frontmatter に追加（なければ）：
```yaml
nav: true
nav_order: 1
```

`_pages/about-ja.md` の frontmatter：
```yaml
---
layout: about
title: "自己紹介 (JP)"
permalink: /ja/
subtitle: <a href="#">所属名</a>. 学科, 大学名.

profile:
  align: right
  image: prof_pic.jpg
  image_circular: false

news: false
latest_posts: false
selected_papers: false
social: true
nav: true
nav_order: 2
---
```

- [ ] **Step 3: ビルドして日本語ページのURLが有効か確認**

```bash
bundle exec jekyll serve
```

`http://localhost:4000/ja/` にアクセスして表示されることを確認。

- [ ] **Step 4: コミット**

```bash
git add _pages/about-ja.md _config.yml
git commit -m "feat: add Japanese about page and language nav links"
```

---

## Task 5: YAMLベースの論文管理システムを実装

**Files:**
- Create: `_data/publications.yml`
- Create: `_includes/publications_list.html`
- Modify: `_pages/publications.md`

- [ ] **Step 1: `_data/publications.yml` を作成（サンプルデータ入り）**

```yaml
# 論文データ
# - title: 論文タイトル（必須）
# - authors: 著者リスト、カンマ区切り（必須）
# - venue: 発表誌・会議名（必須）
# - year: 発表年（必須）
# - url: 論文URL（任意 - arXiv / DOI / プロジェクトページなど）

- title: "Sample Paper Title on Some Research Topic"
  authors: "Your Name, Co-Author One, Co-Author Two"
  venue: "Conference on Example Research (EXAMPLE), 2024"
  year: 2024
  url: "https://arxiv.org/abs/0000.00000"

- title: "Another Paper Without a URL"
  authors: "Co-Author One, Your Name, Co-Author Three"
  venue: "Journal of Sample Research, Vol. 1, 2023"
  year: 2023
```

- [ ] **Step 2: `_includes/publications_list.html` を作成**

```html
{% raw %}
{% assign pubs_sorted = include.publications | sort: "year" | reverse %}
{% assign current_year = "" %}

{% for pub in pubs_sorted %}
  {% if pub.year != current_year %}
    {% unless forloop.first %}</ul>{% endunless %}
    <h3 class="year">{{ pub.year }}</h3>
    <ul class="pub-list">
    {% assign current_year = pub.year %}
  {% endif %}

  <li class="pub-item">
    <div class="pub-title">
      {% if pub.url %}
        <a href="{{ pub.url }}" target="_blank" rel="noopener noreferrer">{{ pub.title }}</a>
      {% else %}
        {{ pub.title }}
      {% endif %}
    </div>
    <div class="pub-authors">
      {% assign authors = pub.authors | split: ", " %}
      {% for author in authors %}
        {% if author == site.author_name %}
          <strong>{{ author }}</strong>
        {% else %}
          {{ author }}
        {% endif %}
        {% unless forloop.last %}, {% endunless %}
      {% endfor %}
    </div>
    <div class="pub-venue"><em>{{ pub.venue }}</em></div>
  </li>

{% endfor %}
{% if pubs_sorted.size > 0 %}</ul>{% endif %}
{% endraw %}
```

- [ ] **Step 3: `_pages/publications.md` を書き換え**

```markdown
---
layout: page
title: Publications
permalink: /publications/
description:
nav: true
nav_order: 2
---

{% raw %}
{% include publications_list.html publications=site.data.publications %}
{% endraw %}
```

- [ ] **Step 4: ビルドして Publications ページを確認**

```bash
bundle exec jekyll serve
```

`http://localhost:4000/publications/` を開いて以下を確認：
- 論文が年度降順で表示される
- `_config.yml` の `author_name` と一致する著者名がボールドになっている
- URLがある論文はタイトルがリンクになっている

- [ ] **Step 5: コミット**

```bash
git add _data/publications.yml _includes/publications_list.html _pages/publications.md
git commit -m "feat: implement YAML-based publications with author bolding"
```

---

## Task 6: Researchページの作成（EN）

**Files:**
- Create: `_pages/research.md`

- [ ] **Step 1: `_pages/research.md` を作成**

```markdown
---
layout: page
title: Research
permalink: /research/
description:
nav: true
nav_order: 3
---

## Research Theme 1

Write 2-3 paragraphs describing your first research theme here.
This section is written in Markdown — just edit this file to update.

**Related publications:**
- [Paper Title 1](/publications/)

---

## Research Theme 2

Write 2-3 paragraphs describing your second research theme here.

**Related publications:**
- [Paper Title 2](/publications/)
```

- [ ] **Step 2: ビルドして Research ページを確認**

```bash
bundle exec jekyll serve
```

`http://localhost:4000/research/` が表示されることを確認。

- [ ] **Step 3: コミット**

```bash
git add _pages/research.md
git commit -m "feat: add research page (EN)"
```

---

## Task 7: Researchページ（JP版）の作成

**Files:**
- Create: `_pages/research-ja.md`

- [ ] **Step 1: `_pages/research-ja.md` を作成**

```markdown
---
layout: page
title: 研究
permalink: /research-ja/
description:
nav: false
---

## 研究テーマ 1

研究テーマ1の説明をここに書く（2〜3段落）。

**関連論文:**
- [論文タイトル 1](/publications/)

---

## 研究テーマ 2

研究テーマ2の説明をここに書く（2〜3段落）。
```

- [ ] **Step 2: `_pages/research-ja.md` のフロントマターにナビ設定を追加**

```markdown
---
layout: page
title: "研究 (JP)"
permalink: /research-ja/
nav: true
nav_order: 5
---
```

合わせて `_pages/research.md` の frontmatter も確認し、`nav: true` / `nav_order: 4` があることを確認する。

- [ ] **Step 3: ビルドして確認**

```bash
bundle exec jekyll serve
```

`http://localhost:4000/research-ja/` が表示されることを確認。

- [ ] **Step 4: コミット**

```bash
git add _pages/research-ja.md _config.yml
git commit -m "feat: add research page (JP) and update nav"
```

---

## Task 8: GitHub Pages デプロイ設定の確認と公開

**Files:**
- Confirm: `.github/workflows/deploy.yml`（al-folioに含まれる）

- [ ] **Step 1: GitHub Actionsワークフローを確認**

```bash
cat .github/workflows/deploy.yml
```

al-folioには `deploy.yml` が含まれている。`on: push: branches: [main]` になっていることを確認する。

- [ ] **Step 2: GitHubリポジトリの設定を確認（手動操作）**

ブラウザで `https://github.com/Kmattsun28/Kmattsun28.github.io/settings/pages` を開く：
- Source: **GitHub Actions** を選択（Deploy from a branch ではなく）
- 保存する

- [ ] **Step 3: 最終プッシュ**

```bash
git push origin main
```

- [ ] **Step 4: デプロイの確認**

```bash
# GitHub Actionsの状況を確認
gh run list --limit 5
```

または `https://github.com/Kmattsun28/Kmattsun28.github.io/actions` でビルドのステータスを確認。
緑になったら `https://Kmattsun28.github.io` でサイトが公開されていることをブラウザで確認する。

- [ ] **Step 5: コミット（設定ファイルを変更した場合）**

```bash
git add .
git commit -m "chore: finalize deploy config"
git push origin main
```

---

## 将来の拡張パターン

新しいページを追加するときは `_pages/` にMarkdownファイルを1つ置くだけ：

```markdown
---
layout: page
title: Talks
permalink: /talks/
nav: true
nav_order: 4
---
（内容）
```

論文を追加するときは `_data/publications.yml` に以下を追記：

```yaml
- title: "新しい論文タイトル"
  authors: "Your Name, Co-Author"
  venue: "会議名, 2025"
  year: 2025
  url: "https://arxiv.org/..."
```
