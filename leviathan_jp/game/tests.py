from otree.api import Bot, Submission

from . import pages
from .models import Constants


def punishment_form(player, points):
    data = {}
    for i in range(1, Constants.players_per_group + 1):
        if i == player.id_in_group:
            continue
        data[f'punish_p{i}'] = points
    return data


def power_transfer_form(player, amount):
    data = {}
    for i in range(1, Constants.players_per_group + 1):
        if i == player.id_in_group:
            continue
        data[f'power_transfer_p{i}'] = amount
    return data


def intro_quiz_form(player):
    round_number = player.round_number
    if round_number == 1:
        return dict(
            intro1_q1=2,
            intro1_q2=2,
            intro1_q3=3,
            intro1_q4=3,
        )
    if round_number == 2:
        return dict(
            intro2_q1=3,
            intro2_q2=3,
            intro2_q3=3,
        )
    if round_number == 3:
        if player.session.config.get('power_transfer_allowed'):
            q1_answer = 3 if player.session.config.get('costly_punishment_transfer') else 1
            return dict(
                intro3_transfer_q1=q1_answer,
                intro3_transfer_q2=2,
                intro3_transfer_q3=2,
            )
        return dict(intro3_fixed_q1=1)
    return {}


class PlayerBot(Bot):
    def play_round(self):
        if self.session.config.get('use_browser_bots') and self.player.round_number > 2:
            return

        treatment = self.session.config.get('treatment_name', 'fixed')

        bot_rules = {
            'fixed': dict(contribution=0, punishment=0, power_transfer=0.0),
            'transfer_free': dict(contribution=10, punishment=1, power_transfer=0.1),
            'transfer_cost': dict(contribution=10, punishment=1, power_transfer=0.1),
        }

        rules = bot_rules.get(treatment, bot_rules['fixed'])

        if pages.RoundInstruction.is_displayed(self.player):
            yield pages.RoundInstruction
        if pages.RoundQuiz.is_displayed(self.player):
            yield Submission(
                pages.RoundQuiz,
                intro_quiz_form(self.player),
                check_html=False,
            )

        power_transfer_allowed = self.session.config.get('power_transfer_allowed')
        if power_transfer_allowed and self.player.round_number >= 3:
            transfer_amount = rules.get('power_transfer', 0.0) or 0.0
            yield Submission(
                pages.PowerTransfer,
                power_transfer_form(self.player, transfer_amount),
                check_html=False,
            )
            yield pages.PowerTransferResult

        contribution_amount = rules.get('contribution', 0) or 0
        yield Submission(
            pages.Contribution,
            {'contribution': contribution_amount},
            check_html=False,
        )
        yield pages.ContributionResult

        if self.player.round_number > 1:
            punishment_points = rules.get('punishment', 0) or 0
            yield Submission(
                pages.Punishment,
                punishment_form(self.player, punishment_points),
                check_html=False,
            )
            yield pages.RoundResult

        if self.player.round_number == Constants.num_rounds:
            yield pages.FinalResult
