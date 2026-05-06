import logging
import random

from otree.api import Bot, Submission, SubmissionMustFail
from otree.database import db

from . import pages


logging.getLogger("otree.bots").setLevel(logging.WARNING)


LOG_STATE_KEY = "_staggered_bot_test_log"
RANDOM_COMPLETION_SEED = 20260428
MAX_RULE_COMPLETION_SECONDS = 5
SECONDS_PER_DELAY_ATTEMPT = 1


def _session_log_state(session):
    log_state = session.vars.get(LOG_STATE_KEY) or {}
    if not log_state:
        log_state = dict(schedule={})
        session.vars[LOG_STATE_KEY] = log_state
    log_state.setdefault("schedule", {})
    return log_state


def _setup_bot_identity(player_bot):
    participant = player_bot.participant
    bot_number = participant.id_in_session
    if participant.vars.get("bot_number"):
        return
    rng = random.Random(RANDOM_COMPLETION_SEED + bot_number)
    completion_seconds = rng.randint(0, MAX_RULE_COMPLETION_SECONDS)
    participant.label = f"BOT{bot_number:02d}"
    participant.vars["bot_number"] = bot_number
    participant.vars["rule_completion_seconds"] = completion_seconds
    participant.vars["rule_delay_attempts"] = (
        completion_seconds // SECONDS_PER_DELAY_ATTEMPT
    )
    log_state = _session_log_state(player_bot.session)
    log_state["schedule"][participant.id_in_session] = dict(
        label=participant.label,
        completion_seconds=completion_seconds,
        delay_attempts=participant.vars["rule_delay_attempts"],
    )
    player_bot.session.vars[LOG_STATE_KEY] = log_state
    db.commit()


def _wrong_power_rule_form(player):
    if player.session.config.get('power_transfer_allowed'):
        return dict(
            intro3_transfer_q1=2,
            intro3_transfer_q2=1,
            intro3_transfer_q3=1,
        )
    return dict(intro3_fixed_q1=2)


def _browser_bot_stop_stage(session):
    return session.config.get("browser_bot_stop_stage", "game")


def _disable_browser_bot(participant):
    participant.is_browser_bot = False
    participant._is_bot = False
    participant.vars["auto_play"] = False
    participant.vars["consecutive_timeouts"] = 0
    participant.vars["dropout_warning_active"] = False
    participant.vars["dropout_confirmed"] = False


class PlayerBot(Bot):
    def play_round(self):
        _setup_bot_identity(self)
        if (
            self.session.config.get("use_browser_bots")
            and _browser_bot_stop_stage(self.session) == "introduction"
        ):
            _disable_browser_bot(self.participant)
            return

        yield pages.InvestmentInstruction
        yield Submission(
            pages.InvestmentQuiz,
            dict(intro1_q1=2, intro1_q2=2, intro1_q3=3, intro1_q4=3),
            check_html=False,
        )
        yield pages.PunishmentInstruction
        yield Submission(
            pages.PunishmentQuiz,
            dict(intro2_q1=3, intro2_q2=3, intro2_q3=3),
            check_html=False,
        )
        yield pages.PowerRuleInstruction

        for _ in range(self.participant.vars.get("rule_delay_attempts", 0)):
            yield SubmissionMustFail(
                pages.PowerRuleQuiz,
                _wrong_power_rule_form(self.player),
                check_html=False,
            )

        if self.session.config.get('power_transfer_allowed'):
            q1_answer = 3 if self.session.config.get('costly_punishment_transfer') else 1
            yield Submission(
                pages.PowerRuleQuiz,
                dict(
                    intro3_transfer_q1=q1_answer,
                    intro3_transfer_q2=2,
                    intro3_transfer_q3=2,
                ),
                check_html=False,
            )
        else:
            yield Submission(
                pages.PowerRuleQuiz,
                dict(intro3_fixed_q1=1),
                check_html=False,
            )
