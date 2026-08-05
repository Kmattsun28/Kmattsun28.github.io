# ブラウザから研究実績・活動を追加する

このリポジトリでは、GitHub Actionsの入力フォームから研究実績や活動を追加できます。通常の更新では、ローカルのエディタやターミナルを開く必要はなく、手動で `git push` を実行する必要もありません。

## この仕組みでできること

- 研究実績を `_data/publications.yml` に追加する
- 活動を `_data/activities.yml` に追加する
- 入力を検証してから自動でcommitし、default branchへ反映する
- 反映後、既存のデプロイworkflowがサイトをビルドして公開する

入力エラーや重複がある場合はworkflowが失敗し、対象のYAMLファイルは変更されません。

## 初回だけ行う設定

GitHub Actionsがリポジトリへcommit・pushするため、対象リポジトリだけに使えるfine-grained personal access token（PAT）をRepository Secretとして登録します。PATはGitHub APIを操作するための認証情報です。

### 1. `SITE_UPDATE_TOKEN`を作成する

1. GitHubで、プロフィール画像 → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** を開きます。
2. **Generate new token** を選びます。
3. 有効期限を設定し、**Repository access** は対象のこのリポジトリだけに限定します。
4. **Repository permissions** の **Contents** を **Read and write** にします。
5. 他の権限は追加せず、トークンを作成します。

作成したトークンの値は、この後の登録時に一度だけ使います。値をチャット、ソースコード、Issue、ログなどへ貼り付けたり、文書へ記録したりしないでください。

### 2. Repository Secretへ登録する

1. 対象リポジトリで **Settings** → **Secrets and variables** → **Actions** を開きます。
2. **New repository secret** を選びます。
3. **Name** に `SITE_UPDATE_TOKEN` と入力します。
4. **Secret** に、作成したPATの値を入力して保存します。

Secret名はworkflowで固定されているため、`SITE_UPDATE_TOKEN`と正確に入力してください。PATの値は保存後に表示できないため、紛失した場合は新しいトークンを作成してSecretを更新します。

## 研究実績を追加する

1. 対象リポジトリで **Actions** → **Add publication** → **Run workflow** を開きます。
2. 次の項目を入力します。

   - **title**: 論文タイトル（必須）
   - **authors**: 著者名（必須）
   - **venue**: 学会名・雑誌名（必須）
   - **year**: 4桁の出版年（必須）
   - **url**: 論文、DOI、プロジェクトページなどのURL（任意）

3. **Run workflow** を実行します。

`year`は4桁の数値で入力してください。URLを入力する場合は `http://` または `https://` から始まるURLを使います。

## 活動を追加する

1. 対象リポジトリで **Actions** → **Add activity** → **Run workflow** を開きます。
2. 次の項目を入力します。

   - **title**: 活動名（必須）
   - **date**: 日付または期間（必須）。`YYYY-MM-DD` または `YYYY-MM-DD〜YYYY-MM-DD` 形式
   - **type**: 活動種別（必須）
   - **venue**: 開催場所・媒体名（任意）
   - **description**: 補足説明（任意）
   - **url**: 関連ページのURL（任意）

3. **Run workflow** を実行します。

日付は実在する日付を入力し、期間の場合は開始日が終了日を超えないようにしてください。URLを入力する場合は `http://` または `https://` から始まるURLを使います。

## 入力エラーが出た場合

workflowが失敗した場合は、Actionsの実行ログでエラー内容を確認し、入力を修正してもう一度実行します。よくある原因は次のとおりです。

- 必須項目が空になっている
- 研究実績の `year` が4桁の数値ではない
- 活動の `date` が指定形式ではない、または存在しない日付になっている
- URLが `http://` または `https://` で始まっていない
- 同じタイトルと年の研究実績、または同じタイトルと日付の活動がすでに登録されている
- `SITE_UPDATE_TOKEN` が未登録、期限切れ、または対象リポジトリへのContents権限を持っていない

入力検証に失敗した場合、commit・pushは行われず、対象のYAMLファイルも変更されません。Secretの問題が疑われる場合も、トークンの値をログへ出力せず、権限や有効期限だけを確認してください。

## 誤登録を戻す方法

成功後に内容を間違えていたことに気づいた場合は、GitHub上で対象のYAMLを直接修正します。Actionsの実行履歴、またはcommit履歴から誤登録のcommitを確認し、変更されたファイル（`_data/publications.yml` または `_data/activities.yml`）を開いて **Edit this file**（鉛筆アイコン）を選びます。誤ったエントリのブロックだけを削除し、他のエントリは変更せず、**Preview changes** で差分を確認してください。

default branchへの直接commitが許可されている場合は、そのまま修正commitを作成します。保護されたbranchの場合は、**Commit changes** で新しいbranchを作成してPull Requestを開き、レビュー後にdefault branchへmergeします。どちらの場合も、ローカルのエディタやターミナル、手動の `git push` は必要ありません。

取り消し後に正しい内容を登録する場合は、該当するActions workflowを再実行します。誤登録のcommitを特定できない場合は、Actionsの実行履歴とcommitメッセージ（`content: add publication` または `content: add activity`）を手掛かりにします。

## BibTeXについて

第1段階では、ブラウザからの追加によって `_data/publications.yml` だけが更新されます。`_bibliography/papers.bib` のBibTeXは自動更新されません。BibTeXにも同じ論文を追加・修正する必要がある場合は、別途これまでの管理手順で対応してください。
