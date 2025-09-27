from otree.api import Bot, Submission

from . import pages
from .models import Constants


def zero_punishments(player):
    form_data = {}
    for i in range(1, Constants.players_per_group + 1):
        if i == player.id_in_group:
            continue
        form_data[f'punish_p{i}'] = 0
    return form_data


class PlayerBot(Bot):
    def play_round(self):
        if self.session.config.get('treatment_name') != 'fixed':
            raise NotImplementedError('Bot is only implemented for the fixed treatment demo session.')

        yield Submission(pages.Contribution, {'contribution': 0}, check_html=False)
        yield pages.ContributionResult

        if self.player.round_number > 1:
            yield Submission(pages.Punishment, zero_punishments(self.player), check_html=False)
            yield pages.PunishmentResult

        if self.player.round_number == Constants.num_rounds:
            yield pages.FinalResult
