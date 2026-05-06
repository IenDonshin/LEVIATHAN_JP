import logging
import sys

from otree.api import Bot, Submission
from otree.database import db

from . import pages


logging.getLogger("otree.bots").setLevel(logging.WARNING)


LOG_STATE_KEY = "_staggered_bot_test_log"
SURVEY_BORDER = "+---------------------------+--------------------+"
RESULT_BORDER = "+------+---------------------+"


def _print_table_title(title, border):
    inner_width = len(border) - 2
    print(border)
    print(f"| {title:<{inner_width - 2}} |")
    print(border)


def _session_log_state(session):
    log_state = session.vars.get(LOG_STATE_KEY) or {}
    log_state.setdefault("survey_page_seen", {})
    log_state.setdefault("survey_page_records", {})
    log_state.setdefault("survey_page_printed", [])
    log_state.setdefault("stage3_started", False)
    log_state.setdefault("final_printed", False)
    session.vars[LOG_STATE_KEY] = log_state
    return log_state


def _save_session_log_state(session, log_state):
    session.vars[LOG_STATE_KEY] = log_state
    db.commit()


def _participant_label(participant):
    return participant.label or f"BOT{participant.id_in_session:02d}"


def _browser_bot_stop_stage(session):
    return session.config.get("browser_bot_stop_stage", "game")


def _disable_browser_bot(participant):
    participant.is_browser_bot = False
    participant._is_bot = False
    participant.vars["auto_play"] = False
    participant.vars["consecutive_timeouts"] = 0
    participant.vars["dropout_warning_active"] = False
    participant.vars["dropout_confirmed"] = False


def _treatment_page_key(session):
    treatment_name = session.config["treatment_name"]
    return {
        "fixed": "FixedQuestionnaire",
        "transfer_free": "TransferFreeQuestionnaire",
        "transfer_cost": "TransferCostQuestionnaire",
    }[treatment_name]


def _expected_survey_pages(session):
    return ["CommonQuestionnaire", _treatment_page_key(session)]


def _print_ready_survey_logs(player, log_state):
    expected_pages = _expected_survey_pages(player.session)
    records = log_state["survey_page_records"]
    printed = log_state["survey_page_printed"]

    if records and not log_state.get("stage3_started"):
        _print_table_title("Stage 3: Survey", SURVEY_BORDER)
        print("| page                      | status             |")
        print(SURVEY_BORDER)
        log_state["stage3_started"] = True

    for page_key in expected_pages:
        if page_key not in records or page_key in printed:
            continue
        printed.append(page_key)
        print(f"| {page_key:<25} | all bots completed |")

    if (
        all(page_key in printed for page_key in expected_pages)
        and not log_state.get("final_printed")
    ):
        _print_table_title("Test result", RESULT_BORDER)
        print("| bots | status              |")
        print(RESULT_BORDER)
        print(
            f"| {player.session.num_participants:>4} "
            "| full flow completed |"
        )
        log_state["final_printed"] = True

    sys.stdout.flush()


def _record_survey_completion(player, page_key):
    log_state = _session_log_state(player.session)
    page_seen = log_state["survey_page_seen"].setdefault(page_key, [])
    label = _participant_label(player.participant)
    if label not in page_seen:
        page_seen.append(label)

    if (
        len(page_seen) == player.session.num_participants
        and page_key not in log_state["survey_page_records"]
    ):
        log_state["survey_page_records"][page_key] = dict(page_key=page_key)

    _print_ready_survey_logs(player, log_state)
    _save_session_log_state(player.session, log_state)


class PlayerBot(Bot):
    def play_round(self):
        if (
            self.session.config.get("use_browser_bots")
            and _browser_bot_stop_stage(self.session) == "survey"
        ):
            _disable_browser_bot(self.participant)
            return

        yield Submission(
            pages.CommonQuestionnaire,
            {"common_satisfaction": 3},
            check_html=False,
        )
        _record_survey_completion(self.player, "CommonQuestionnaire")

        treatment_name = self.session.config["treatment_name"]
        if treatment_name == "fixed":
            yield Submission(
                pages.FixedQuestionnaire,
                {"fixed_satisfaction": 3},
                check_html=False,
            )
            _record_survey_completion(self.player, "FixedQuestionnaire")
        elif treatment_name == "transfer_free":
            yield Submission(
                pages.TransferFreeQuestionnaire,
                {"transfer_free_satisfaction": 3},
                check_html=False,
            )
            _record_survey_completion(self.player, "TransferFreeQuestionnaire")
        elif treatment_name == "transfer_cost":
            yield Submission(
                pages.TransferCostQuestionnaire,
                {"transfer_cost_satisfaction": 3},
                check_html=False,
            )
            _record_survey_completion(self.player, "TransferCostQuestionnaire")
