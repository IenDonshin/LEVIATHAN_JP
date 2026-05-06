# survey/pages.py

from otree.api import *


def _survey_vars(player, title, description):
    return dict(
        treatment_name=player.session.config["treatment_name"],
        questionnaire_title=title,
        questionnaire_description=description,
    )


class BaseSurveyPage(Page):
    template_name = "survey/Questionnaire.html"
    form_model = "player"


class CommonQuestionnaire(BaseSurveyPage):
    form_fields = ["common_satisfaction"]

    @staticmethod
    def vars_for_template(player):
        return _survey_vars(player, "共通アンケート", "すべての参加者に共通する質問です。")


class FixedQuestionnaire(BaseSurveyPage):
    form_fields = ["fixed_satisfaction"]

    @staticmethod
    def is_displayed(player):
        return player.session.config["treatment_name"] == "fixed"

    @staticmethod
    def vars_for_template(player):
        return _survey_vars(player, "固定条件アンケート", "固定条件に関する質問です。")


class TransferFreeQuestionnaire(BaseSurveyPage):
    form_fields = ["transfer_free_satisfaction"]

    @staticmethod
    def is_displayed(player):
        return player.session.config["treatment_name"] == "transfer_free"

    @staticmethod
    def vars_for_template(player):
        return _survey_vars(
            player,
            "無コスト移譲条件アンケート",
            "無コスト移譲条件に関する質問です。",
        )


class TransferCostQuestionnaire(BaseSurveyPage):
    form_fields = ["transfer_cost_satisfaction"]

    @staticmethod
    def is_displayed(player):
        return player.session.config["treatment_name"] == "transfer_cost"

    @staticmethod
    def vars_for_template(player):
        return _survey_vars(
            player,
            "コストあり移譲条件アンケート",
            "コストあり移譲条件に関する質問です。",
        )


page_sequence = [
    CommonQuestionnaire,
    FixedQuestionnaire,
    TransferFreeQuestionnaire,
    TransferCostQuestionnaire,
]
