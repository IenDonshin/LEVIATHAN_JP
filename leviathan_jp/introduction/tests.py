from otree.api import Bot, Submission

from . import pages


class PlayerBot(Bot):
    def play_round(self):
        treatment = self.session.config.get('treatment_name')
        yield pages.Introduction

        if treatment != 'fixed':
            raise NotImplementedError('Bot is only implemented for the fixed treatment demo session.')

        endowment = self.session.config['endowment']
        multiplier = self.session.config['contribution_multiplier']

        yield Submission(
            pages.Test,
            dict(q1_fixed=endowment, q2_fixed=multiplier),
            check_html=False,
        )
