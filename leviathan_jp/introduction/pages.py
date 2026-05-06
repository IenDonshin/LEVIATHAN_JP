from otree.api import Page


def _base_vars(player, intro_stage):
    session = player.session
    return dict(
        intro_stage=intro_stage,
        treatment_name=session.config.get("treatment_name", "fixed"),
        power_transfer_allowed=bool(session.config.get("power_transfer_allowed")),
        costly_punishment_transfer=bool(session.config.get("costly_punishment_transfer")),
        contribution_multiplier=session.config.get("contribution_multiplier", 1.5),
        players_per_group=session.config.get("players_per_group", 5),
        endowment=session.config.get("endowment", 20),
    )


class InvestmentInstruction(Page):
    template_name = "introduction/RuleInstruction.html"

    @staticmethod
    def vars_for_template(player):
        return _base_vars(player, "round1")


class InvestmentQuiz(Page):
    template_name = "introduction/RuleQuiz.html"
    form_model = "player"
    form_fields = ["intro1_q1", "intro1_q2", "intro1_q3", "intro1_q4"]

    @staticmethod
    def vars_for_template(player):
        return _base_vars(player, "round1")

    @staticmethod
    def error_message(player, values):
        expected = dict(intro1_q1=2, intro1_q2=2, intro1_q3=3, intro1_q4=3)
        if any(values.get(k) != v for k, v in expected.items()):
            return "投資ルールの解答が正しくありません。説明を確認して再回答してください。"


class PunishmentInstruction(Page):
    template_name = "introduction/RuleInstruction.html"

    @staticmethod
    def vars_for_template(player):
        return _base_vars(player, "round2")


class PunishmentQuiz(Page):
    template_name = "introduction/RuleQuiz.html"
    form_model = "player"
    form_fields = ["intro2_q1", "intro2_q2", "intro2_q3"]

    @staticmethod
    def vars_for_template(player):
        return _base_vars(player, "round2")

    @staticmethod
    def error_message(player, values):
        expected = dict(intro2_q1=3, intro2_q2=3, intro2_q3=3)
        if any(values.get(k) != v for k, v in expected.items()):
            return "減点ルールの解答が正しくありません。説明を確認して再回答してください。"


class PowerRuleInstruction(Page):
    template_name = "introduction/RuleInstruction.html"

    @staticmethod
    def vars_for_template(player):
        return _base_vars(player, "round3")


class PowerRuleQuiz(Page):
    template_name = "introduction/RuleQuiz.html"
    form_model = "player"

    @staticmethod
    def get_form_fields(player):
        if player.session.config.get("power_transfer_allowed"):
            return ["intro3_transfer_q1", "intro3_transfer_q2", "intro3_transfer_q3"]
        return ["intro3_fixed_q1"]

    @staticmethod
    def vars_for_template(player):
        return _base_vars(player, "round3")

    @staticmethod
    def error_message(player, values):
        if player.session.config.get("power_transfer_allowed"):
            expected_q1 = 3 if player.session.config.get("costly_punishment_transfer") else 1
            expected = dict(
                intro3_transfer_q1=expected_q1,
                intro3_transfer_q2=2,
                intro3_transfer_q3=2,
            )
            if any(values.get(k) != v for k, v in expected.items()):
                return "減点効果移譲ルールの解答が正しくありません。説明を確認して再回答してください。"
        elif values.get("intro3_fixed_q1") != 1:
            return "固定条件の進行ルールの解答が正しくありません。説明を確認して再回答してください。"

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.vars["rules_completed"] = True


page_sequence = [
    InvestmentInstruction,
    InvestmentQuiz,
    PunishmentInstruction,
    PunishmentQuiz,
    PowerRuleInstruction,
    PowerRuleQuiz,
]
