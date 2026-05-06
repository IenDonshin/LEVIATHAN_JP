from otree.api import *

from .pages import (  # type: ignore
    CommonQuestionnaire,
    FixedQuestionnaire,
    TransferCostQuestionnaire,
    TransferFreeQuestionnaire,
)


doc = """
Survey module for Leviathan project
"""


class C(BaseConstants):
    NAME_IN_URL = 'survey'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    common_satisfaction = models.IntegerField(
        label="この実験全体にどの程度満足しましたか？",
        choices=[
            [1, "非常に不満"],
            [2, "やや不満"],
            [3, "どちらともいえない"],
            [4, "やや満足"],
            [5, "非常に満足"],
        ],
        widget=widgets.RadioSelect,
    )
    fixed_satisfaction = models.IntegerField(
        label="固定条件の実験内容にどの程度満足しましたか？",
        choices=[
            [1, "非常に不満"],
            [2, "やや不満"],
            [3, "どちらともいえない"],
            [4, "やや満足"],
            [5, "非常に満足"],
        ],
        widget=widgets.RadioSelect,
    )
    transfer_free_satisfaction = models.IntegerField(
        label="無コスト移譲条件の実験内容にどの程度満足しましたか？",
        choices=[
            [1, "非常に不満"],
            [2, "やや不満"],
            [3, "どちらともいえない"],
            [4, "やや満足"],
            [5, "非常に満足"],
        ],
        widget=widgets.RadioSelect,
    )
    transfer_cost_satisfaction = models.IntegerField(
        label="コストあり移譲条件の実験内容にどの程度満足しましたか？",
        choices=[
            [1, "非常に不満"],
            [2, "やや不満"],
            [3, "どちらともいえない"],
            [4, "やや満足"],
            [5, "非常に満足"],
        ],
        widget=widgets.RadioSelect,
    )


page_sequence = [
    CommonQuestionnaire,
    FixedQuestionnaire,
    TransferFreeQuestionnaire,
    TransferCostQuestionnaire,
]
