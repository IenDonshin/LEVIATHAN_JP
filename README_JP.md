# Build the Leviathan（日本版：減点効果移譲ゲーム）

## プロジェクト概要

本プロジェクトは、罰付き公共財ゲームの oTree 実装です。条件は3種類あります。

1. `fixed`: 減点効果が固定。
2. `transfer_free`: 減点効果の移譲はコストなし。
3. `transfer_cost`: 減点効果の移譲にコストあり。

## 起動方法（開発）

1. リポジトリをサーバーPCにクローンします。
2. サーバーを起動します。

```bash
otree devserver 0.0.0.0:8000
```

3. ルームのリンクからセッションを作成します。

参加者の端末がサーバーと同一LANにあることを確認してください。

## 設定パラメータ

設定はすべて `leviathan_jp/settings.py` にあります。

### タイムアウトと疑似退出の挙動

- カウントダウン終了までに送信されない場合、ページは自動送信されます。
- 自動送信が3ページ連続すると途中退出として判定され、自動決定に切り替わります。
- 途中退出判定後は、早期終了判定の対象になります。

### セッションプロファイル

`SESSION_CONFIGS` に3つのプロファイルが定義されています。

- `pggp_fixed` -> treatment `fixed`
- `pggp_transfer_free` -> treatment `transfer_free`
- `pggp_transfer_cost` -> treatment `transfer_cost`

現在のセッションフローは `introduction` でルール説明と理解度チェックを完了した後、`game` に入ります（`app_sequence=['introduction', 'game', 'survey']`）。
`game` の最初の待機ページでは、ルール説明を完了して到着した順に5人ずつグループを作成します。

### 減点効果移譲の仕組み

減点効果移譲フェーズは、参照論文の status quo の仕組みに合わせています。

- `power_transfer_allowed=True` の条件では、第3ラウンドから減点効果移譲フェーズが表示されます。
- 第4ラウンド以降、各参加者の移譲入力欄には、その参加者が前ラウンドに入力した移譲決定が初期値として表示されます。
- 各入力欄の値は「このラウンドでその相手に最終的に移譲する量」を表します。追加分だけを入力する形式ではありません。
- 初期値を変更しない場合、前ラウンドの移譲を維持します。
- 初期値より大きくした場合、このラウンドでその相手への移譲量を増やします。
- `0.0` に戻した場合、その相手への前ラウンドの移譲を取り消します。

移譲入力は、設定された移譲単位に制限されます。既定値 `punishment_transfer_unit=0.1` では、入力可能な値は `0.0`, `0.1`, `0.2`, ... から、このラウンドで許される最大移譲量までです。`2`, `-0.1`, `0.15` のような値はページ上で拒否され、サーバー側でも再度検証されます。

全員が送信した後、各参加者の減点効果は次の式で再計算されます。

```text
最終的な減点効果 = 1.0 - 自分が移譲した合計 + 他者から受け取った合計
```

`transfer_cost` 条件では、移譲合計と `power_transfer_cost_rate` に基づいて移譲コストが計算されます。`transfer_free` 条件では移譲コストは発生しません。

### SESSION_CONFIG_DEFAULTS

以下は全セッションに共通のデフォルト値です（セッションごとに上書き可能）。

| キー | 既定値 | 用途 |
| --- | --- | --- |
| `real_world_currency_per_point` | `2` | ポイントから実貨幣への換算率。 |
| `participation_fee` | `500` | 参加報酬（実貨幣）。 |
| `num_demo_participants` | `5` | デモ参加者数。 |
| `enable_timeout_autoplay` | `True` | タイムアウト時の自動進行。 |
| `per_target_dp_limit` | `10` | 減点フェーズの各対象減点上限。未設定なら `deduction_points` を使用。 |
| `decision_timeout_seconds` | `30` | 意思決定ページの制限時間。 |
| `dropout_timeout_pages` | `3` | タイムアウトが連続した回数の閾値。到達すると「途中退出の疑い」として警告フラグが立つ。 |
| `early_stop_min_rounds` | `14` | 早期終了が可能になる最小ラウンド数。 |
| `early_stop_dropout_count` | `1` | 上記フラグが立った参加者数がこの値以上になった場合、最小ラウンド条件を満たしていれば早期終了を発動。 |
| `non_decision_timeout_seconds` | `60` | 非意思決定ページの制限時間。 |
| `group_by_arrival_time` | `True` | ルール説明を完了した参加者から順に、`game` 開始時にグループ化する。 |

### セッション個別パラメータ

以下は `SESSION_CONFIGS` 内でセッションごとに指定します。

| キー | 用途 |
| --- | --- |
| `name` | oTree セッション名。 |
| `display_name` | 管理画面の表示名。 |
| `app_sequence` | アプリ実行順（`['introduction', 'game', 'survey']`）。 |
| `num_demo_participants` | このセッションのデモ人数。 |
| `players_per_group` | グループ人数。 |
| `num_rounds` | ラウンド数。 |
| `endowment` | ラウンド初期資源（MU）。 |
| `contribution_multiplier` | 公共財の乗数。 |
| `deduction_points` | `per_target_dp_limit` 未設定時の減点上限。 |
| `power_effectiveness` | 減点効果の効果係数。 |
| `punishment_cost` | 減点1ポイントあたりのコスト。 |
| `power_transfer_allowed` | 減点効果移譲フェーズの有効化。 |
| `costly_punishment_transfer` | 移譲にコストがあるか。 |
| `power_transfer_cost_rate` | 移譲単位あたりコスト。 |
| `punishment_transfer_unit` | 移譲の単位（例：`0.1`）。 |
| `practice_rounds` | 練習ラウンド数（現在は `0`）。 |
| `treatment_name` | 分岐や表示に使用する識別名。 |
| `use_browser_bots` | ブラウザボット自動進行。 |
| `browser_bot_stop_stage` | 手動操作に切り替える段階。`introduction` / `game` / `survey`。 |
| `browser_bot_stop_round` | `browser_bot_stop_stage='game'` のときに停止するゲームラウンド。 |

### グローバル設定

`settings.py` の oTree 全体設定です。

| キー | 用途 |
| --- | --- |
| `LANGUAGE_CODE` | UIの言語。 |
| `REAL_WORLD_CURRENCY_CODE` | 実貨幣の通貨コード。 |
| `USE_POINTS` | ポイント使用の有無。 |
| `POINTS_CUSTOM_NAME` | ポイント名称（例：`MU`）。 |
| `POINTS_DECIMAL_PLACES` | 小数点以下の桁数。 |
| `TIME_ZONE` | サーバーのタイムゾーン。 |

## 自動テスト

以下のコマンドで自動テストできます。

```bash
otree test pggp_fixed
```

```bash
otree test pggp_transfer_free
```

```bash
otree test pggp_transfer_cost
```

これらのテストは固定値（投資・減点・移譲）を送信します。コード修正後にフローが正常に完了するか確認してください。

コマンドラインの bot テストでは、以下も自動検出します。

- introduction の理解度チェックを完了した後に `game` に入ること。
- `group_by_arrival_time=True` の場合、introduction 完了後の到着順でグループ化されること。
- 各ゲームグループが `players_per_group` 人になること。
- ラウンドをまたいでもグループ構成と `id_in_group` が変わらないこと。
- 条件ごとに期待されるゲームページ順で完了すること。

20人で、ルール説明の完了タイミングをbotごとにランダムにずらして、5人ずつ到着順でグループ化されることを確認する場合は以下を実行します。

```bash
otree test pggp_transfer_free 20
```

成功時には、詳細なページ送信ログではなく、簡潔なステージ表を出力します。

- Stage 1: introduction 完了タイミングと到着順グループ化。
- Stage 2: ラウンドごとのゲームページ完了状況。

検出に失敗した場合は、失敗したラウンド、ページ、botラベル、期待値、実際の値が出力されます。

## Browser Bot の手動切り替え

管理画面の `Sessions` で `Create new session` を選択し、`Configure session` で `use_browser_bots` を有効化して、`browser_bot_stop_stage` を選択します。

この仕組みは、ブラウザ上の手動確認で実験内の特定箇所まで直接進めるために使います。

- `browser_bot_stop_stage='introduction'`: browser bot は introduction app を完了せずに停止します。参加者はルール説明ページから手動操作を開始します。
- `browser_bot_stop_stage='game'`: browser bot は introduction を完了して `game` に入り、`browser_bot_stop_round` まで自動進行した後、そのゲームラウンドでブラウザ参加者に操作を戻します。
- `browser_bot_stop_stage='survey'`: browser bot は introduction と全ゲームラウンドを完了し、survey app でブラウザ参加者に操作を戻します。

`game` で停止する場合、`browser_bot_stop_round` は有効なラウンド範囲に丸められます。既定値は第3ラウンドです。これにより、減点効果移譲、減点、ラウンド結果、履歴モーダルなどの後半ページを、毎回最初から手動で進めずに確認できます。
