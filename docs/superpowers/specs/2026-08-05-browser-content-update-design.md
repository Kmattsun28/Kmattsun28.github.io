# 研究実績・活動のブラウザ更新運用 設計書

**作成日:** 2026-08-05  
**目的:** ローカルエディタと手動のGit操作なしで、研究実績・活動を安全に更新できる運用を作る

---

## 1. 背景と現状

このサイトはJekyllで生成する静的サイトで、GitHub PagesへGitHub Actions経由でデプロイしている。

現在の主なデータ配置は次の通り。

- `_data/publications.yml`: `/publications/` に表示する論文情報
- `_data/activities.yml`: `/activities/` に表示する活動情報
- `_pages/publications.md` と `_pages/activities-ja.md`: 各データをLiquidテンプレートで表示
- `_bibliography/papers.bib`: Jekyll Scholarが利用するBibTeX
- `.github/workflows/deploy.yml`: `main` または `master` への変更をビルドして公開

現在は、情報を追加するたびにローカルでファイルを開き、編集し、commitしてpushする必要がある。利用者が自分一人で更新する場合、この手順はコンテンツ追加に対して重い。

## 2. 目標

### 必須目標

- GitHubのWeb画面だけで研究実績を追加できる
- GitHubのWeb画面だけで活動を追加できる
- ローカルエディタを開かない
- 利用者が手動でGitコマンドを実行しない
- 入力ミスや重複を登録前に検出する
- 登録内容をGitの履歴で確認・復元できる
- 既存の表示ページとデプロイ方式を大きく変更しない

### 非目標

- 第1段階でサイトに独自ログイン画面を作る
- GitHub Pages上にデータベースを導入する
- 第1段階でサイト全体のデザインを変更する
- 研究実績・活動以外のすべてのサイト更新をブラウザフォーム化する

## 3. 採用する方式

GitHub Actionsの手動実行フォームを利用する。

### 更新フロー

```text
GitHubのActions画面
        ↓ 入力
入力検証スクリプト
        ↓ 正常時
_data/publications.yml または _data/activities.yml を更新
        ↓
GitHub Actionsが自動commit・push
        ↓
既存のdeploy workflowがJekyll build・GitHub Pages公開
```

研究実績と活動は入力項目が異なるため、Actions workflowも分ける。

- `add-publication.yml`: 研究実績の追加
- `add-activity.yml`: 活動の追加

利用者はリポジトリへの書き込み権限を持つ本人だけなので、公開サイトに管理画面を追加せず、GitHubの認証をそのまま利用する。

## 4. 構成要素

### 4.1 GitHub Actions workflow

各workflowは`workflow_dispatch`で起動し、入力欄を提供する。

#### 研究実績の入力項目

- `title`: 論文タイトル。必須
- `authors`: 著者名。必須
- `venue`: 学会名・雑誌名。必須
- `year`: 出版年。必須。4桁の整数
- `url`: 論文、DOI、プロジェクトページなどのURL。任意

#### 活動の入力項目

- `title`: 活動名。必須
- `date`: 日付または期間。必須。既存データとの互換性を保つため、単日または`YYYY-MM-DD〜YYYY-MM-DD`を許可
- `type`: 活動種別。必須
- `venue`: 開催場所・媒体名。任意
- `description`: 補足説明。任意
- `url`: 関連ページのURL。任意

### 4.2 共通更新スクリプト

workflow内に更新ロジックを直接書かず、Pythonスクリプトに集約する。

- `bin/add_site_entry.py`
- 標準入力またはコマンドライン引数からworkflowの入力を受け取る
- YAMLを読み込む
- 入力を検証する
- 重複を確認する
- 既存ファイルの形式を保って末尾に追加する
- 更新内容を標準出力に表示する

既存の`requirements.txt`に`pyyaml`が含まれているため、新しいYAMLライブラリは追加しない。

### 4.3 自動commit

入力と検証が成功した場合のみ、workflowが対象ファイルをcommitする。

- 変更対象を追加したデータファイルに限定する
- commit messageは自動生成する
- 変更がなければcommitしない
- workflow summaryに追加した内容を出力する

GitHub Actionsからのcommitが既存のデプロイworkflowを起動できるよう、認証方式を確認する。現在の引用数更新workflowにも、後続workflowを起動する場合はPATが必要になる旨の記載があるため、必要に応じてActions用のPATをRepository Secretとして設定する。

認証情報はworkflowのソースコードに書かず、GitHub Secretsから参照する。

## 5. データ管理方針

### 第1段階

既存の表示を壊さないことを優先し、現在のファイルをそのまま更新対象にする。

- 研究実績: `_data/publications.yml`
- 活動: `_data/activities.yml`

この段階では、表示テンプレートやURL構造を変更しない。

### BibTeXの二重管理

`_data/publications.yml`と`_bibliography/papers.bib`には重複する論文情報がある。ただし、両者は現在異なる表示経路で使われているため、ブラウザ更新機能の第1段階で無理に統合しない。

第1段階の運用が安定した後、次のどちらかを別タスクとして決める。

1. `_data/publications.yml`を正本にして、BibTeXを自動生成する
2. `_bibliography/papers.bib`を正本にして、PublicationsページをBibTeXから表示する

この判断には、Jekyll Scholarの表示を今後どの程度使うかを確認してから進む。

## 6. 入力検証

### 研究実績

- 必須項目が空でないこと
- `year`が4桁の数値であること
- URLが入力された場合、`http://`または`https://`で始まること
- 同じタイトルと年の組み合わせが既存データにないこと
- YAMLとして安全に保存できる文字列であること

### 活動

- 必須項目が空でないこと
- `date`が単日または既存形式の期間であること
- URLが入力された場合、`http://`または`https://`で始まること
- 同じタイトルと日付の組み合わせが既存データにないこと
- YAMLとして安全に保存できる文字列であること

検証に失敗した場合はデータファイルを変更せず、失敗理由をworkflow summaryとログに表示する。

## 7. エラー処理と復旧

- 入力検証エラー: ファイルを変更せずworkflowを失敗させる
- YAML読み込みエラー: ファイルを変更せずworkflowを失敗させる
- GitHub Pagesビルドエラー: 既存のdeploy workflowの結果で検知する
- 誤登録: Gitのcommit履歴から対象commitを確認し、revertまたは修正フォームで対応する
- 同時実行: 同じworkflowの同時実行を制限し、データの追記競合を防ぐ

自動commit前に対象ファイルの変更差分を確認できるよう、workflow summaryに変更内容を出す。

## 8. テスト方針

### スクリプトテスト

- 正常な研究実績を追加できる
- 正常な活動を追加できる
- 必須項目欠落を拒否する
- 年・日付の不正形式を拒否する
- 不正URLを拒否する
- 重複登録を拒否する
- 既存の日本語・英語・URLを壊さない
- 既存YAMLの順序と表示に意図しない変更がない

### workflowテスト

- GitHub Actionsの手動実行で入力を渡せる
- 成功時に対象ファイルだけがcommitされる
- 検証失敗時にcommitされない
- commit後にサイトのデプロイが実行される

### サイト確認

- `/publications/`に新しい研究実績が表示される
- `/activities/`に新しい活動が表示される
- Aboutページの最近の活動表示にも影響が反映される
- ダークモード・既存ナビゲーション・外部リンクが壊れていない

## 9. 段階的な導入順

1. `bin/add_site_entry.py`の入力検証とYAML更新を実装する
2. スクリプトの単体テストを追加する
3. `add-publication.yml`を追加する
4. `add-activity.yml`を追加する
5. GitHub Actionsの認証と自動commitを設定する
6. テスト用データでworkflowを実行する
7. 本番データを追加してデプロイまで確認する
8. 運用手順をREADMEまたは専用ドキュメントに記録する

BibTeXの正本化・自動同期は、この導入が完了してから別の設計・実装として扱う。

## 10. 成功条件

次の操作が、ローカル環境を使わずに完了できること。

1. GitHubのActions画面を開く
2. 研究実績または活動のフォームに入力する
3. workflowを実行する
4. 自動commit後、公開サイトに反映されることを確認する

利用者が通常の更新で、エディタ・ターミナル・`git add`・`git commit`・`git push`を使わないことを成功条件とする。

## スコープ外

- 独自のWeb管理画面とログイン機能
- GoogleフォームやAirtableなど外部サービスとの連携
- 既存の論文データのBibTeX完全統合
- 既存ページの見た目の大幅な変更
- 画像・PDFのブラウザアップロード

