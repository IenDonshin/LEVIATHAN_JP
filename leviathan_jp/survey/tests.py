from otree.api import Bot

from . import pages


class PlayerBot(Bot):
    def play_round(self):
        treatment = self.session.config.get('treatment_name')
        if treatment != 'fixed':
            raise NotImplementedError('Bot is only implemented for the fixed treatment demo session.')
        yield pages.Questionnaire
