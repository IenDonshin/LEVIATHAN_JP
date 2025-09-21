# game/pages.py

from ._builtin import Page, WaitPage # type: ignore
from .models import Constants
from otree.api import Currency as c # 确保 Currency 被导入

# =============================================================================
# CLASS: Contribution
# =============================================================================
class Contribution(Page):
    form_model = 'player'
    form_fields = ['contribution']

    def vars_for_template(self):
        # 为了 _HistoryModal.html 中的 player.in_all_rounds 迭代器能正确获取到 id_range
        # otree 5.x 以后，get_attribute 可能需要 id_range 辅助
        id_range = list(range(1, Constants.players_per_group + 1))
        return dict(
            history=self.player.in_previous_rounds(),
            id_range=id_range # 传递 id_range 到模板
        )

# =============================================================================
# CLASS: ContributionWaitPage
# =============================================================================
class ContributionWaitPage(WaitPage):
    after_all_players_arrive = 'set_group_contribution'

# =============================================================================
# CLASS: ContributionResult
# =============================================================================
class ContributionResult(Page):
    def vars_for_template(self):
        return dict(
            kept=c(self.session.config['endowment']) - self.player.contribution,
            share=self.group.individual_share
        )

# =============================================================================
# CLASS: Punishment
# =============================================================================
class Punishment(Page):
    form_model = 'player'
    
    def get_form_fields(self):
        # 根据小组人数动态生成表单字段
        return [f'punish_p{i}' for i in range(1, Constants.players_per_group + 1)]

    def is_displayed(self):
        return self.round_number > 1

    def vars_for_template(self):
        # 传递 id_range 到模板
        id_range = list(range(1, Constants.players_per_group + 1))
        return dict(
            players_contribution=self.group.get_players(),
            deduction_points=self.session.config['deduction_points'],
            id_range=id_range # 传递 id_range 到模板
        )
    
    def error_message(self, values):
        total_punishment = 0
        for i in range(1, Constants.players_per_group + 1):
            field_name = f'punish_p{i}'
            if field_name in values and values[field_name] is not None:
                total_punishment += values[field_name]
        
        if total_punishment > self.session.config['deduction_points']:
            return f"您送出的总惩罚点数不能超过 {self.session.config['deduction_points']}。"

# =============================================================================
# CLASS: PunishmentWaitPage
# =============================================================================
class PunishmentWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number > 1

    after_all_players_arrive = 'set_payoff'

# =============================================================================
# CLASS: PunishmentResult
# =============================================================================
class PunishmentResult(Page):
    def is_displayed(self):
        return self.round_number > 1
        
    def vars_for_template(self):
        id_range = list(range(1, Constants.players_per_group + 1))
        cumulative_payoff = self.player.participant.vars.get('cumulative_payoff', c(0))
        
        # 贡献阶段的利得 = E - c_i + (m/n)Σc_j
        payoff_from_contribution = c(self.session.config['endowment']) - self.player.contribution + self.group.individual_share
        
        return dict(
            payoff_from_contribution=payoff_from_contribution,
            cumulative_payoff=cumulative_payoff,
            id_range=id_range # 传递 id_range 到模板
        )

# =============================================================================
# CLASS: FinalResult (在 game App 中)
# =============================================================================
class FinalResult(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds # 确保只在最后一轮显示

    def vars_for_template(self):
        # 这里的 self.group.get_players() 是指当前（最后一轮）组的玩家
        # 他们的 participant.payoff 已经包含了累计总收益
        final_payoff_jpy = self.participant.payoff_plus_participation_fee()
        
        return {
            'players': sorted(self.group.get_players(), key=lambda p: p.id_in_group),
            'final_payoff_jpy': final_payoff_jpy
        }


# =============================================================================
# 页面顺序
# =============================================================================
page_sequence = [
    Contribution,
    ContributionWaitPage,
    ContributionResult,
    Punishment,
    PunishmentWaitPage,
    PunishmentResult,
    FinalResult, # <--- 最终结果页放在游戏 App 的最后
]