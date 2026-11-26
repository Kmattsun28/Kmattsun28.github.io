# 日英ナビとトップページの整理 設計

## 目的

研究者、共同研究の相手、企業の人が、今読んでいる言語のまま研究・論文・活動へたどり着けるようにする。

今のサイトには次の問題がある。

- ナビに日本語と英語のページが混ざって並ぶ（「自己紹介 / PUBLICATIONS / 研究 (JP) / 活動 / RESEARCH / ABOUT」）。
- 日英のトップで中身がそろっていない。英語版には「最近の活動」がなく、日本語版には冒頭の自己紹介文がない。英語の活動ページもない。
- `<html lang>` が日本語のページでも `en` になっている。
- トップから論文と研究紹介へのリンクがない。

10/20 の `2026-10-20-interactive-homepage-design.md` は白紙に戻した。本設計はそれを引き継がない。

## URL とページの対応

日本語は `/` の下、英語は `/en/` の下に置く。

| 内容   | 日本語           | 英語                | `ref`          |
| ------ | ---------------- | ------------------- | -------------- |
| トップ | `/`              | `/en/`              | `home`         |
| 研究   | `/research/`     | `/en/research/`     | `research`     |
| 論文   | `/publications/` | `/en/publications/` | `publications` |
| 活動   | `/activities/`   | `/en/activities/`   | `activities`   |

- 各ページの front matter に `lang`（`ja` か `en`）と `ref` を書く。同じ `ref` を持つ日英の2ページを対として扱う。
- 今の `/research/`（英語）は日本語の研究ページになり、英語の研究ページは `/en/research/` へ移る。
- 古い `/research-ja/` には、al-folio の `default.liquid` が持つ `redirect:` を使い、`/research/` へ転送するページを置く。ナビには出さない。

## ナビと言語切り替え

`_includes/header.liquid` を次のように変える。

- 今のページの言語を `page.lang` で決める。`lang` を持たないページ（404 など）は `ja` として扱う。
- ナビには `nav: true` で、`lang` が今のページと同じページだけを `nav_order` の順に出す。
  - 日本語: 研究 / 論文 / 活動
  - 英語: Research / Publications / Activities
- トップのページ（`ref: home`）は `nav` を外し、ナビに出さない。左上の名前をその言語のトップへのリンクにし、トップを含む全ページで表示する。名前は日本語のページでは「松本亘平」、英語のページでは「Kohei Matsumoto」とする。
- ダークモードの切り替えの左に、言語の切り替えのリンクを置く。
  - 日本語のページでは「EN」、英語のページでは「日本語」と表示する。
  - リンク先は、`ref` が同じで `lang` が逆のページ。見つからなければ、もう一方の言語のトップ（`/` か `/en/`）。
  - リンクに `hreflang` と `lang` を付ける。
- `_layouts/default.liquid` の `<html lang>` は `page.lang` を使い、なければ `site.lang` を使う。

## トップページ

`/` と `/en/` は今の `about` レイアウトのまま、本文の並びを次にそろえる。

1. 名前、所属、写真（今のまま）
2. 自己紹介の1文。日本語版には英語版の文に対応する文を足す。
3. 研究内容の3項目と「研究紹介を見る →」（英語版は「View research →」）
4. 論文: 新しい順に3件。タイトルと掲載先だけを出し、最後に「すべての論文（N件）→」を置く。
5. 最近の活動: 新しい順に3件と「すべての活動 →」
6. 学歴
7. 趣味
8. 連絡先のアイコン（今のまま）

- 論文と活動の節は、`_pages/about-ja.md` と `_pages/about.md` の本文の中から include で呼ぶ。
- `about.liquid` にある `recent_activities` の節（日本語の見出しが固定されたもの）は使わなくなるので消す。

## 一覧の部品と文言

### 文言の対応表

新しく `_data/i18n.yml` を作り、言語ごとに次を持つ。

- 見出しとリンクの文言（「論文」「最近の活動」「すべての論文」など）
- 活動の種別の英語名（シンポジウム → Symposium、国内学会発表 → Domestic Conference、国際学会発表 → International Conference、イベント → Event、受賞 → Award、展示 → Exhibition、その他 → Other。「Add activity」ワークフローの選択肢をすべて）

対応表にない種別は、日本語のまま表示する。

### 活動の一覧（`_includes/activities_list.html`）

- 引数に `lang` を足す（省略時は `ja`）。
- 英語では `title_en`、`description_en` を使い、空なら `title`、`description` を出す。
- 日付は日本語で「2026年03月」、英語で「Mar 2026」と表示する。
- 今ある `limit` の引数はそのまま使う。

### 論文の一覧

- 日本語の論文で自分の名前が太字にならない原因は2つある。`_config.yml` の `author_names` が「松本 亘平」（空白あり）で、データの「松本亘平」と一致しないこと。DICOMO の論文は著者の区切りが全角の「，」であること。
- `author_names` に「松本亘平」を足し、`_includes/publications_list.html` は著者名を分ける前に全角の「，」を「, 」に置き換える。
- トップ用に、新しい順の上位N件をタイトルと掲載先だけで出す部品 `_includes/publications_recent.html` を作る。`year` の降順に並べ、同じ年の中ではデータの並び順を保つ。

### データ

- `_data/activities.yml` に任意の項目 `title_en`、`description_en` を足す。既存の5件の英訳は下書きを作り、本人が確かめてから入れる。
- 先頭のコメントに、2つの項目の説明を足す。
- 既存の項目は変えない。英語の項目がない活動も、そのまま表示できること。

## ファイル

| ファイル                                                      | 変更                                                               |
| ------------------------------------------------------------- | ------------------------------------------------------------------ |
| `_includes/header.liquid`                                     | 言語で絞ったナビ、全ページの名前リンク、言語の切り替え             |
| `_layouts/default.liquid`                                     | `<html lang>`                                                      |
| `_layouts/about.liquid`                                       | 日本語固定の「最近の活動」の節を消す。見出しの名前は今のまま       |
| `_includes/activities_list.html`                              | `lang` の引数、英語の項目、日付の形式                              |
| `_includes/publications_list.html`                            | 全角の区切りの扱い                                                 |
| `_config.yml`                                                 | `author_names` に「松本亘平」を足す                                |
| `_includes/publications_recent.html`                          | 新規。トップ用の論文の上位N件                                      |
| `_data/i18n.yml`                                              | 新規。文言と活動の種別の対応                                       |
| `_data/activities.yml`                                        | 英語の項目を足す                                                   |
| `_pages/about-ja.md`、`_pages/about.md`                       | `ref`、本文の並び、自己紹介の1文、include の呼び出し。`nav` を外す |
| `_pages/research.md` → 日本語、`_pages/research-en.md` を新規 | 研究ページの日英の入れ替え                                         |
| `_pages/research-ja.md`                                       | `/research-ja/` から `/research/` への転送だけのページにする       |
| `_pages/publications.md`、`_pages/publications-en.md`（新規） | 日英の論文ページ                                                   |
| `_pages/activities-ja.md`、`_pages/activities-en.md`（新規）  | 日英の活動ページ                                                   |
| `tests/test_page_pairs.py`                                    | 新規。日英の対のテスト                                             |
| `docs/content-update.md`                                      | 活動の英語の項目の書き方                                           |

## エラー処理

- `ref` の対がないページ: 言語の切り替えは、もう一方の言語のトップへリンクする。ビルドは止めない。
- 活動の英語の項目がない: 日本語の値を出す。
- 種別の英語名がない: 日本語の種別を出す。

## テスト

- `tests/test_page_pairs.py`（`unittest`、追加の依存なし）: `_pages/*.md` の front matter を読み、次を確かめる。
  - `ref` を持つページは、同じ `ref` で `lang` が逆のページがちょうど1つある。
  - 同じ `lang` と `ref` の組が重複しない。
  - `permalink` が重複しない。
  - `lang: en` のページの `permalink` は `/en/` で始まり、`lang: ja` のページは `/en/` で始まらない。
- テストを先に書き、今のページで失敗することを確かめてから実装する。

## エンドツーエンドの確認

1. `python3 -m unittest discover -s tests -p 'test_*.py'` が通る。
2. Docker でビルドし、日英の4ページずつを 1440px 幅と 390px 幅で開く。
3. 各ページでナビに今の言語のページだけが出ること、左上の名前がその言語のトップへ移ること、言語の切り替えが対のページへ移ることを確かめる。
4. 各ページの `<html lang>` がページの言語と合うことを確かめる。
5. `/research-ja/` を開くと `/research/` へ移ることを確かめる。
6. 英語のトップと活動ページで、活動が英語で出ること、英語の項目がない活動は日本語で出ることを確かめる。
7. 論文ページで、日本語の論文2件の「松本亘平」が太字になることを確かめる。
8. ダークモードとライトモードの両方で、言語の切り替えが読めることを確かめる。
9. 変更したファイルに `npx prettier --check` をかける。
10. 実装のあと、Codex に差分のレビューを頼む。

## 対象外

- 「Add activity」ワークフローと `bin/add_site_entry.py` への英語の入力欄の追加。
- プロフィール写真の大きさ、活動の重複した書き方、研究の図、ダークモードの文字色とフッター、連絡先アイコン。これらは別の作業として順に扱う。
- 論文ページの種類の区別や PDF・DOI のボタン。
- `_bibliography/papers.bib` の扱い。
