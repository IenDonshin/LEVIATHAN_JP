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
- 自動送信が3ページ連続すると「途中退出の疑い」として警告モーダルが表示されます。
- 警告モーダルを閉じると疑似退出フラグは解除されます。

### セッションプロファイル

`SESSION_CONFIGS` に3つのプロファイルが定義されています。

- `pggp_fixed` -> treatment `fixed`
- `pggp_transfer_free` -> treatment `transfer_free`
- `pggp_transfer_cost` -> treatment `transfer_cost`

現在のセッションフローは `game` から直接開始します（`app_sequence=['game', 'survey']`）。
旧 `introduction` アプリは使用していません。

### SESSION_CONFIG_DEFAULTS

以下は全セッションに共通のデフォルト値です（セッションごとに上書き可能）。

| キー | 既定値 | 用途 |
| --- | --- | --- |
| `real_world_currency_per_point` | `2` | ポイントから実貨幣への換算率。 |
| `participation_fee` | `500` | 参加報酬（実貨幣）。 |
| `num_demo_participants` | `5` | デモ参加者数。 |
| `enable_timeout_autoplay` | `True` | タイムアウト時の自動進行。 |
| `per_target_dp_limit` | `10` | 減点フェーズの各対象減点上限。未設定なら `deduction_points` を使用。 |
| `decision_timeout_seconds` | `60` | 意思決定ページの制限時間。 |
| `dropout_timeout_pages` | `3` | タイムアウトが連続した回数の閾値。到達すると「途中退出の疑い」として警告フラグが立つ。 |
| `early_stop_min_rounds` | `14` | 早期終了が可能になる最小ラウンド数。 |
| `early_stop_dropout_count` | `1` | 上記フラグが立った参加者数がこの値以上になった場合、最小ラウンド条件を満たしていれば早期終了を発動。 |
| `non_decision_timeout_seconds` | `60` | 非意思決定ページの制限時間。 |

### セッション個別パラメータ

以下は `SESSION_CONFIGS` 内でセッションごとに指定します。

| キー | 用途 |
| --- | --- |
| `name` | oTree セッション名。 |
| `display_name` | 管理画面の表示名。 |
| `app_sequence` | アプリ実行順（`['game', 'survey']`）。 |
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
| `browser_bot_stop_round` | ボット停止ラウンド。 |

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

## 特定ラウンドへ直接移動

管理画面の `Sessions` で `Create new session` を選択し、`Configure session` で `use_browser_bots` を有効化します。既定ではラウンド3にジャンプしますが変更可能です。セッション作成後、各参加者ページが自動で該当ラウンドへ進行します。
`use_browser_bots` が有効な場合、browser bot ではラウンド開始前の説明ページと理解度チェックページを自動でスキップします。
