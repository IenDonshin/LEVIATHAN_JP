# game/pages.py

from otree.api import Page, WaitPage

from .models import Constants
from otree.api import Currency as c # 确保 Currency 被导入


def build_history_rounds(player):
    """Assemble per-round history data for the modal."""
    endowment = player.session.config['endowment']
    endowment_currency = c(endowment)
    history_rounds = []

    for prev_round in player.in_previous_rounds():
        prev_group = prev_round.group
        players = prev_group.get_players()

        player_entries = []
        matrix_rows = []

        for member in players:
            contribution = member.contribution
            kept_amount = endowment_currency - contribution
            total_received = kept_amount + prev_group.individual_share

            punishment_sent_total = 0
            for target in players:
                if target.id_in_group == member.id_in_group:
                    continue
                field_name = f'punish_p{target.id_in_group}'
                punishment_sent_total += getattr(member, field_name, 0) or 0

            player_entries.append(
                dict(
                    id_in_group=member.id_in_group,
                    contribution=contribution,
                    endowment=endowment_currency,
                    share=prev_group.individual_share,
                    current_total=total_received,
                    punishment_sent_total=punishment_sent_total,
                )
            )

        for victim in players:
            row_cells = []
            for giver in players:
                is_self = giver.id_in_group == victim.id_in_group
                amount = None
                if not is_self:
                    field_name = f'punish_p{victim.id_in_group}'
                    amount = getattr(giver, field_name, 0) or 0
                row_cells.append(
                    dict(
                        giver_id=giver.id_in_group,
                        amount=amount,
                        is_self=is_self,
                    )
                )

            matrix_rows.append(
                dict(
                    victim_id=victim.id_in_group,
                    cells=row_cells,
                )
            )

        history_rounds.append(
            dict(
                round_number=prev_round.round_number,
                players=player_entries,
                matrix_rows=matrix_rows,
                has_punishment=prev_round.round_number > 1,
            )
        )

    return history_rounds

# =============================================================================
# CLASS: Contribution
# =============================================================================
class Contribution(Page):
    form_model = 'player'
    form_fields = ['contribution']

    @staticmethod
    def vars_for_template(player):
        id_range = list(range(1, Constants.players_per_group + 1))
        history_rounds = build_history_rounds(player)

        return dict(
            id_range=id_range,
            history_rounds=history_rounds,
            C=Constants,
        )

# =============================================================================
# CLASS: ContributionWaitPage
# =============================================================================
class ContributionWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group):
        group.set_group_contribution()

# =============================================================================
# CLASS: ContributionResult
# =============================================================================
class ContributionResult(Page):
    @staticmethod
    def vars_for_template(player):
        endowment = player.session.config['endowment']
        share = player.group.individual_share
        players_data = []

        for member in player.group.get_players():
            contribution = member.contribution
            kept_amount = c(endowment) - contribution
            payoff_contribution_phase = kept_amount + share
            players_data.append(
                dict(
                    player=member,
                    contribution=contribution,
                    received_from_public=share,
                    current_total=payoff_contribution_phase,
                )
            )

        return dict(
            players_data=players_data,
            endowment=c(endowment),
            share=share,
        )

# =============================================================================
# CLASS: Punishment
# =============================================================================
class Punishment(Page):
    form_model = 'player'
    
    @staticmethod
    def get_form_fields(player):
        # 根据小组人数动态生成表单字段
        fields = []
        for i in range(1, Constants.players_per_group + 1):
            if i == player.id_in_group:
                continue
            fields.append(f'punish_p{i}')
        return fields

    @staticmethod
    def is_displayed(player):
        return player.round_number > 1

    @staticmethod
    def vars_for_template(player):
        # 传递 id_range 到模板
        id_range = list(range(1, Constants.players_per_group + 1))
        return dict(
            players_contribution=player.group.get_players(),
            deduction_points=player.session.config['deduction_points'],
            id_range=id_range, # 传递 id_range 到模板
            history_rounds=build_history_rounds(player),
        )
    
    @staticmethod
    def error_message(player, values):
        total_punishment = 0
        for i in range(1, Constants.players_per_group + 1):
            field_name = f'punish_p{i}'
            if field_name in values and values[field_name] is not None:
                total_punishment += values[field_name]
        
        if total_punishment > player.session.config['deduction_points']:
            return f"您送出的总惩罚点数不能超过 {player.session.config['deduction_points']}。"

# =============================================================================
# CLASS: PunishmentWaitPage
# =============================================================================
class PunishmentWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player):
        return player.round_number > 1

    @staticmethod
    def after_all_players_arrive(group):
        group.set_payoff()

# =============================================================================
# CLASS: PunishmentResult
# =============================================================================
class PunishmentResult(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number > 1
        
    @staticmethod
    def vars_for_template(player):
        endowment = player.session.config['endowment']
        endowment_currency = c(endowment)
        players = player.group.get_players()
        share = player.group.individual_share

        players_summary = []
        matrix_rows = []

        for member in players:
            total_sent = 0
            for other in players:
                if other.id_in_group == member.id_in_group:
                    continue
                field_name = f'punish_p{other.id_in_group}'
                total_sent += getattr(member, field_name, 0) or 0

            players_summary.append(
                dict(
                    id_in_group=member.id_in_group,
                    contribution=member.contribution,
                    endowment=endowment_currency,
                    punishment_sent_total=total_sent,
                )
            )

        for victim in players:
            row_cells = []
            for giver in players:
                is_self = giver.id_in_group == victim.id_in_group
                amount = None
                if not is_self:
                    field_name = f'punish_p{victim.id_in_group}'
                    amount = getattr(giver, field_name, 0) or 0
                row_cells.append(
                    dict(
                        giver_id=giver.id_in_group,
                        amount=amount,
                        is_self=is_self,
                    )
                )

            matrix_rows.append(
                dict(
                    victim_id=victim.id_in_group,
                    cells=row_cells,
                )
            )

        cumulative_payoff = player.participant.vars.get('cumulative_payoff', c(0))
        
        # 贡献阶段的利得 = E - c_i + (m/n)Σc_j
        payoff_from_contribution = endowment_currency - player.contribution + share

        return dict(
            payoff_from_contribution=payoff_from_contribution,
            cumulative_payoff=cumulative_payoff,
            players_summary=players_summary,
            matrix_rows=matrix_rows,
            matrix_headers=[p.id_in_group for p in players],
        )

# =============================================================================
# CLASS: FinalResult (在 game App 中)
# =============================================================================
class FinalResult(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == Constants.num_rounds # 确保只在最后一轮显示

    @staticmethod
    def vars_for_template(player):
        # 这里的 self.group.get_players() 是指当前（最后一轮）组的玩家
        # 他们的 participant.payoff 已经包含了累计总收益
        final_payoff_jpy = player.participant.payoff_plus_participation_fee()
        
        return {
            'players': sorted(player.group.get_players(), key=lambda p: p.id_in_group),
            'final_payoff_jpy': final_payoff_jpy,
            'C': Constants,
            'Constants': Constants
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
