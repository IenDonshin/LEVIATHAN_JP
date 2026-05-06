from otree.api import *

from .models import Constants as C, Subsession, Group, Player  # type: ignore
from .pages import (
    InvestmentInstruction,
    InvestmentQuiz,
    PunishmentInstruction,
    PunishmentQuiz,
    PowerRuleInstruction,
    PowerRuleQuiz,
)  # type: ignore


doc = """
Pre-game rule instructions and comprehension checks.
"""


page_sequence = [
    InvestmentInstruction,
    InvestmentQuiz,
    PunishmentInstruction,
    PunishmentQuiz,
    PowerRuleInstruction,
    PowerRuleQuiz,
]
