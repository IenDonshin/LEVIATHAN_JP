import logging
import sys

from otree.api import Bot, Submission
from otree.database import db

from . import pages
from .models import Constants


logging.getLogger("otree.bots").setLevel(logging.WARNING)


LOG_STATE_KEY = "_staggered_bot_test_log"
STAGE1_BORDER = "+-------+--------------+-------+-------------+"
STAGE2_BORDER = "+-------+---------------------+--------------------+"
PAGE_ORDER = [
    "PowerTransfer",
    "PowerTransferResult",
    "Contribution",
    "ContributionResult",
    "Punishment",
    "RoundResult",
    "FinalResult",
]
PAGE_LABELS = {
    "PowerTransfer": "PowerTransfer",
    "PowerTransferResult": "PowerTransferResult",
    "Contribution": "Contribution",
    "ContributionResult": "ContributionResult",
    "Punishment": "Punishment",
    "RoundResult": "RoundResult",
    "FinalResult": "FinalResult",
}


def _session_log_state(session):
    log_state = session.vars.get(LOG_STATE_KEY) or {}
    defaults = dict(
        schedule={},
        arrivals=[],
        stage1_printed=False,
        stage2_started=False,
        page_completions={},
        page_completion_records={},
        page_printed=[],
        stage3_printed=False,
        survey_seen=[],
        final_printed=False,
    )
    for key, value in defaults.items():
        log_state.setdefault(key, value)
    session.vars[LOG_STATE_KEY] = log_state
    return log_state


def _save_session_log_state(session, log_state):
    session.vars[LOG_STATE_KEY] = log_state
    db.commit()


def _participant_label(participant):
    return participant.label or f"BOT{participant.id_in_session:02d}"


def _browser_bot_stop_stage(session):
    return session.config.get("browser_bot_stop_stage", "game")


def _browser_bot_stop_round(session):
    stop_round = session.config.get("browser_bot_stop_round")
    if stop_round is None:
        return 3
    try:
        stop_round = int(stop_round)
    except (TypeError, ValueError):
        stop_round = 3
    return max(1, min(stop_round, Constants.num_rounds))


def _disable_browser_bot(participant):
    participant.is_browser_bot = False
    participant._is_bot = False
    participant.vars["auto_play"] = False
    participant.vars["consecutive_timeouts"] = 0
    participant.vars["dropout_warning_active"] = False
    participant.vars["dropout_confirmed"] = False


def _print_table_title(title, border):
    inner_width = len(border) - 2
    print(border)
    print(f"| {title:<{inner_width - 2}} |")
    print(border)


def _print_stage1_once(player, log_state):
    if log_state.get("stage1_printed"):
        return
    arrivals = log_state["arrivals"]
    if len(arrivals) < player.session.num_participants:
        return

    _print_table_title("Stage 1: Introduction and arrival grouping", STAGE1_BORDER)
    print("| bot   | completion_s | group | id_in_group |")
    print(STAGE1_BORDER)
    actual_assignments = {}
    round1_players = player.in_round(1).subsession.get_players()
    groups = {}
    for member in round1_players:
        groups.setdefault(member.group_id, []).append(member)
    for group_number, group_id in enumerate(sorted(groups), start=1):
        for member in groups[group_id]:
            actual_assignments[member.participant.id_in_session] = dict(
                group_number=group_number,
                id_in_group=member.id_in_group,
            )

    for row in sorted(
        arrivals,
        key=lambda item: item["id_in_session"],
    ):
        assignment = actual_assignments.get(row["id_in_session"], {})
        print(
            f"| {row['label']:<5} "
            f"| {row['completion_seconds']:>12} "
            f"| {assignment.get('group_number', row['group_number']):>5} "
            f"| {assignment.get('id_in_group', row['id_in_group']):>11} |"
        )
    _print_table_title("Stage 2: Game pages", STAGE2_BORDER)
    print("| round | page                | status             |")
    print(STAGE2_BORDER)
    sys.stdout.flush()

    log_state["stage1_printed"] = True
    log_state["stage2_started"] = True
    _print_ready_page_logs(log_state)


def _record_arrival(player):
    if player.round_number != 1:
        return
    participant = player.participant
    if participant.vars.get("arrival_recorded"):
        return

    log_state = _session_log_state(player.session)
    arrivals = log_state["arrivals"]
    schedule = log_state["schedule"].get(participant.id_in_session, {})
    group_number = (len(arrivals) // Constants.players_per_group) + 1

    arrivals.append(
        dict(
            label=_participant_label(participant),
            id_in_session=participant.id_in_session,
            completion_seconds=schedule.get(
                "completion_seconds",
                participant.vars.get("rule_completion_seconds"),
            ),
            group_number=group_number,
            id_in_group=player.id_in_group,
        )
    )
    participant.vars["arrival_recorded"] = True
    participant.vars["initial_game_group_number"] = group_number

    _print_stage1_once(player, log_state)
    _save_session_log_state(player.session, log_state)


def _page_sort_key(item):
    _key, record = item
    return (
        record["round_number"],
        PAGE_ORDER.index(record["page_key"]),
    )


def _print_ready_page_logs(log_state):
    if not log_state.get("stage2_started"):
        return

    records = log_state["page_completion_records"]
    printed = log_state["page_printed"]
    for key, record in sorted(records.items(), key=_page_sort_key):
        if key in printed:
            continue
        printed.append(key)
        print(
            f"| {record['round_number']:>5} "
            f"| {record['page_label']:<19} "
            "| all bots completed |"
        )
    sys.stdout.flush()


def _record_page_completion(player, page_key):
    log_state = _session_log_state(player.session)
    key = f"{player.round_number}:{page_key}"
    completed = log_state["page_completions"].setdefault(key, [])
    label = _participant_label(player.participant)
    if label not in completed:
        completed.append(label)

    if (
        len(completed) == player.session.num_participants
        and key not in log_state["page_completion_records"]
    ):
        log_state["page_completion_records"][key] = dict(
            round_number=player.round_number,
            page_key=page_key,
            page_label=PAGE_LABELS[page_key],
        )

    _print_ready_page_logs(log_state)
    _save_session_log_state(player.session, log_state)


def punishment_form(player, points):
    data = {}
    for i in range(1, Constants.players_per_group + 1):
        if i == player.id_in_group:
            continue
        data[f"punish_p{i}"] = points
    return data


def power_transfer_form(player, amount):
    data = {}
    for i in range(1, Constants.players_per_group + 1):
        if i == player.id_in_group:
            continue
        data[f"power_transfer_p{i}"] = amount
    return data


def assert_grouping(player, page_name="GroupingCheck"):
    group_players = player.group.get_players()
    _record_arrival(player)
    expected_size = Constants.players_per_group
    actual_size = len(group_players)
    assert actual_size == expected_size, (
        f"Grouping failed: round={player.round_number} page={page_name} "
        f"bot={_participant_label(player.participant)} "
        f"expected_group_size={expected_size} actual_group_size={actual_size}"
    )

    participant = player.participant
    group_member_numbers = sorted(
        member.participant.id_in_session for member in group_players
    )
    if player.round_number == 1:
        participant.vars["initial_game_group_members"] = group_member_numbers
        participant.vars["initial_id_in_group"] = player.id_in_group
        return

    assert participant.vars.get("initial_game_group_members") == group_member_numbers, (
        f"Group membership changed: round={player.round_number} page={page_name} "
        f"bot={_participant_label(participant)} "
        f"initial={participant.vars.get('initial_game_group_members')} "
        f"current={group_member_numbers}"
    )
    assert participant.vars.get("initial_id_in_group") == player.id_in_group, (
        f"id_in_group changed: round={player.round_number} page={page_name} "
        f"bot={_participant_label(participant)} "
        f"initial={participant.vars.get('initial_id_in_group')} "
        f"current={player.id_in_group}"
    )


class PlayerBot(Bot):
    def play_round(self):
        if (
            self.session.config.get("use_browser_bots")
            and _browser_bot_stop_stage(self.session) == "game"
            and self.player.round_number >= _browser_bot_stop_round(self.session)
        ):
            _disable_browser_bot(self.participant)
            return

        assert_grouping(self.player)

        treatment = self.session.config.get("treatment_name", "fixed")
        bot_rules = {
            "fixed": dict(contribution=0, punishment=0, power_transfer=0.0),
            "transfer_free": dict(contribution=10, punishment=1, power_transfer=0.1),
            "transfer_cost": dict(contribution=10, punishment=1, power_transfer=0.1),
        }
        rules = bot_rules.get(treatment, bot_rules["fixed"])

        power_transfer_allowed = self.session.config.get("power_transfer_allowed")
        if power_transfer_allowed and self.player.round_number >= 3:
            transfer_amount = rules.get("power_transfer", 0.0) or 0.0
            yield Submission(
                pages.PowerTransfer,
                power_transfer_form(self.player, transfer_amount),
                check_html=False,
            )
            _record_page_completion(self.player, "PowerTransfer")
            yield pages.PowerTransferResult
            _record_page_completion(self.player, "PowerTransferResult")

        contribution_amount = rules.get("contribution", 0) or 0
        yield Submission(
            pages.Contribution,
            {"contribution": contribution_amount},
            check_html=False,
        )
        _record_page_completion(self.player, "Contribution")
        yield pages.ContributionResult
        _record_page_completion(self.player, "ContributionResult")

        if self.player.round_number > 1:
            punishment_points = rules.get("punishment", 0) or 0
            yield Submission(
                pages.Punishment,
                punishment_form(self.player, punishment_points),
                check_html=False,
            )
            _record_page_completion(self.player, "Punishment")
            yield pages.RoundResult
            _record_page_completion(self.player, "RoundResult")

        if self.player.round_number == Constants.num_rounds:
            yield pages.FinalResult
            _record_page_completion(self.player, "FinalResult")
