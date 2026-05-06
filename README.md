# Build the Leviathan (Power Transfer Game) in Japan

## Project Overview

This is an oTree project for a public goods game with punishment. There are three treatments:

1. `fixed`: Participants' power to punish is fixed.
2. `transfer_free`: Participants can transfer their power to punish to others at no cost.
3. `transfer_cost`: Participants must pay a cost to transfer their power to punish to others.

## Quick Start

1. Clone the repository to the PC you will use as the server.
2. Run the server:

```bash
otree devserver 0.0.0.0:8000
```

3. Open the room link in a browser and create a session.

Make sure the participants' devices are on the same LAN as the server.

## Configuration

All configuration lives in `leviathan_jp/settings.py`.

### Timeout & Dropout Behavior

- If a participant does not submit before the countdown ends, the page is auto-submitted.
- If three consecutive pages are auto-submitted, the participant is treated as a dropout and switched to auto-decisions.
- Confirmed dropouts are counted for early-stop decisions.

### Session Profiles

The experiment defines three session profiles in `SESSION_CONFIGS`.

- `pggp_fixed` -> treatment `fixed`
- `pggp_transfer_free` -> treatment `transfer_free`
- `pggp_transfer_cost` -> treatment `transfer_cost`

The session flow now starts with `introduction` for rule instructions and comprehension checks, then enters `game` (`app_sequence=['introduction', 'game', 'survey']`).
At the first wait page in `game`, participants who completed the rules are grouped by arrival time in groups of 5.

### Power Transfer Mechanics

The power-transfer stage follows the status-quo mechanism described in the reference paper.

- The power-transfer stage is shown from round 3 when `power_transfer_allowed=True`.
- From round 4 onward, each participant's transfer inputs are prefilled with their own decisions from the previous round.
- Each input represents the current round's final transfer amount to that target, not an additional increment.
- Keeping a prefilled value unchanged maintains the previous round's transfer.
- Increasing a value increases the transfer to that target for the current round.
- Setting a value to `0.0` withdraws the previous transfer to that target.

Allowed transfer inputs are restricted to the configured transfer unit. With the default `punishment_transfer_unit=0.1`, valid values are `0.0`, `0.1`, `0.2`, ..., up to the current round's maximum transfer amount. Invalid values such as `2`, `-0.1`, or `0.15` are rejected on the page and are also checked again by the server.

After all players submit, each player's punishment power is recalculated as:

```text
final punishment power = 1.0 - total transferred out + total transferred in
```

In `transfer_cost`, transfer cost is calculated from the total transferred amount and `power_transfer_cost_rate`. In `transfer_free`, transfer has no cost.

### SESSION_CONFIG_DEFAULTS

These defaults apply to all session profiles unless overridden.

| Key | Default | Usage |
| --- | --- | --- |
| `real_world_currency_per_point` | `2` | Conversion rate from points to real-world currency. |
| `participation_fee` | `500` | Participation fee (real-world currency). |
| `num_demo_participants` | `5` | Default demo participant count. |
| `enable_timeout_autoplay` | `True` | Auto-advance on timeouts for pages. |
| `per_target_dp_limit` | `10` | Per-target DP cap in punishment. If not set, `deduction_points` is used. |
| `decision_timeout_seconds` | `30` | Timeout for decision pages. |
| `dropout_timeout_pages` | `3` | Number of consecutive timeout pages to flag a participant as a suspected dropout (sets the dropout warning flag). |
| `early_stop_min_rounds` | `14` | Minimum rounds before early stop can trigger. |
| `early_stop_dropout_count` | `1` | Number of suspected dropouts required to trigger early stop once the minimum rounds condition is met. |
| `non_decision_timeout_seconds` | `60` | Timeout for non-decision pages. |
| `group_by_arrival_time` | `True` | Group participants by arrival time at the start of `game` after they complete `introduction`. |

### Per-Session Keys

These keys appear in the session profiles inside `SESSION_CONFIGS`.

| Key | Usage |
| --- | --- |
| `name` | Session name used by oTree. |
| `display_name` | Label shown in the admin UI. |
| `app_sequence` | App order for the session (`['introduction', 'game', 'survey']`). |
| `num_demo_participants` | Demo participant count for this session. |
| `players_per_group` | Group size. |
| `num_rounds` | Number of rounds. |
| `endowment` | Initial endowment per round (MU). |
| `contribution_multiplier` | Public good multiplier. |
| `deduction_points` | Default DP cap if `per_target_dp_limit` is not set. |
| `power_effectiveness` | Punishment effectiveness multiplier. |
| `punishment_cost` | Cost per DP. |
| `power_transfer_allowed` | Enable/disable power transfer stage. |
| `costly_punishment_transfer` | Whether transfer has a cost. |
| `power_transfer_cost_rate` | Cost per transfer unit. |
| `punishment_transfer_unit` | Transfer unit size (e.g. `0.1`). |
| `practice_rounds` | Practice rounds (currently `0`). |
| `treatment_name` | Used to branch logic and labels. |
| `use_browser_bots` | Auto-play for testing. |
| `browser_bot_stop_stage` | Manual handoff stage: `introduction`, `game`, or `survey`. |
| `browser_bot_stop_round` | Game round where bots stop when `browser_bot_stop_stage='game'`. |

### Global Settings

These are oTree global settings in `settings.py`.

| Key | Usage |
| --- | --- |
| `LANGUAGE_CODE` | Language for the UI. |
| `REAL_WORLD_CURRENCY_CODE` | Currency code for payouts. |
| `USE_POINTS` | Whether to use points. |
| `POINTS_CUSTOM_NAME` | Point label (e.g. `MU`). |
| `POINTS_DECIMAL_PLACES` | Point precision. |
| `TIME_ZONE` | Time zone for the server. |

## How to Test the Project Automatically

Run tests from the command line:

```bash
otree test pggp_fixed
```

```bash
otree test pggp_transfer_free
```

```bash
otree test pggp_transfer_cost
```

These tests submit fixed values (contribution, punishment, power transfer). After modifying the code, use these commands to verify the flow completes.

The command-line bot tests also perform automatic checks:

- Introduction quizzes must be completed before participants enter `game`.
- With `group_by_arrival_time=True`, bots are grouped by arrival order after the introduction app.
- Each game group must contain `players_per_group` participants.
- Group membership and `id_in_group` must remain stable across rounds.
- Game pages must complete in the expected order for the selected treatment.

To test 20 bots with randomized rule-instruction completion delays and arrival-time grouping into 5-person groups, run:

```bash
otree test pggp_transfer_free 20
```

On success, the bot test prints compact stage tables instead of verbose per-page submit logs:

- Stage 1: introduction completion timing and arrival-order grouping.
- Stage 2: game page completion by round and page.

If an assertion fails, the test output includes the failed round, page, bot label, expected value, and actual value.

## Browser Bot Manual Handoff

Open `Sessions` in the admin UI, then `Create new session`. In `Configure session`, enable `use_browser_bots` and choose `browser_bot_stop_stage`.

This mechanism is used to jump directly to a target part of the experiment for browser-based manual checking:

- `browser_bot_stop_stage='introduction'`: browser bots stop before completing the introduction app. Participants start manual operation from the rule-instruction pages.
- `browser_bot_stop_stage='game'`: browser bots complete introduction, enter `game`, auto-play until `browser_bot_stop_round`, then hand control back to the browser participant at that game round.
- `browser_bot_stop_stage='survey'`: browser bots complete introduction and all game rounds, then hand control back at the survey app.

When stopping in `game`, `browser_bot_stop_round` is clamped to the valid round range. The default is round 3. This is useful for checking later pages such as power transfer, punishment, round results, and history modals without manually completing every earlier page.
