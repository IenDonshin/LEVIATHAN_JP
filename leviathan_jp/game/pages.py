# game/pages.py

from otree.api import Page, WaitPage

from .models import Constants
from otree.api import Currency as c # 确保 Currency 被导入


def build_history_rounds(player):
    """Collect per-round history data for templates."""
    session = player.session
    endowment = session.config.get('endowment', 0)
    endowment_currency = c(endowment)
    rounds = []

    for prev in player.in_previous_rounds():
        group = prev.group
        members = group.get_players()

        player_entries = []
        for member in members:
            total_sent = 0
            for other in members:
                if other.id_in_group == member.id_in_group:
                    continue
                field_name = f'punish_p{other.id_in_group}'
                total_sent += getattr(member, field_name, 0) or 0

            player_entries.append(
                dict(
                    id_in_group=member.id_in_group,
                    contribution=member.contribution,
                    endowment=endowment_currency,
                    punishment_sent_total=total_sent,
                )
            )

        matrix_rows = []
        for victim in members:
            cells = []
            for giver in members:
                is_self = giver.id_in_group == victim.id_in_group
                amount = None
                if not is_self:
                    field_name = f'punish_p{victim.id_in_group}'
                    amount = getattr(giver, field_name, 0) or 0
                cells.append(dict(is_self=is_self, amount=amount))
            matrix_rows.append(dict(victim_id=victim.id_in_group, cells=cells))

        rounds.append(
            dict(
                round_number=prev.round_number,
                players=player_entries,
                matrix_rows=matrix_rows,
                has_punishment=prev.round_number > 1,
            )
        )

    return rounds

# =============================================================================
# CLASS: Contribution
# =============================================================================
class Contribution(Page):
    form_model = 'player'
    form_fields = ['contribution']

    @staticmethod
    def vars_for_template(player):
        # 为了 _HistoryModal.html 中的 player.in_all_rounds 迭代器能正确获取到 id_range
        id_range = list(range(1, Constants.players_per_group + 1))
        return dict(
            history=player.in_previous_rounds(),
            id_range=id_range,
            C=Constants,
            history_rounds=build_history_rounds(player),
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
        session = player.session
        endowment = session.config['endowment']
        endowment_currency = c(endowment)
        share = player.group.individual_share

        players_data = []
        for member in player.group.get_players():
            contribution = member.contribution
            received_from_public = share
            kept_amount = endowment_currency - contribution
            current_total = kept_amount + share

            players_data.append(
                dict(
                    player=member,
                    contribution=contribution,
                    received_from_public=received_from_public,
                    current_total=current_total,
                )
            )

        return dict(
            players_data=players_data,
            endowment=endowment_currency,
            share=share,
        )

# =============================================================================
# CLASS: Punishment
# =============================================================================
class Punishment(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        return [
            f'punish_p{i}'
            for i in range(1, Constants.players_per_group + 1)
            if i != player.id_in_group
        ]

    @staticmethod
    def is_displayed(player):
        return player.round_number > 1

    @staticmethod
    def vars_for_template(player):
        id_range = list(range(1, Constants.players_per_group + 1))
        return dict(
            players_contribution=player.group.get_players(),
            deduction_points=player.session.config['deduction_points'],
            id_range=id_range,
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
        id_range = list(range(1, Constants.players_per_group + 1))
        session = player.session
        endowment = session.config['endowment']
        endowment_currency = c(endowment)
        share = player.group.individual_share

        cumulative_payoff = player.participant.vars.get('cumulative_payoff', c(0))
        payoff_from_contribution = endowment_currency - player.contribution + share

        players = player.group.get_players()

        players_summary = []
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

        matrix_rows = []
        for victim in players:
            cells = []
            for giver in players:
                is_self = giver.id_in_group == victim.id_in_group
                amount = None
                if not is_self:
                    field_name = f'punish_p{victim.id_in_group}'
                    amount = getattr(giver, field_name, 0) or 0
                cells.append(dict(is_self=is_self, amount=amount))
            matrix_rows.append(dict(victim_id=victim.id_in_group, cells=cells))

        return dict(
            payoff_from_contribution=payoff_from_contribution,
            cumulative_payoff=cumulative_payoff,
            id_range=id_range,
            players_summary=players_summary,
            matrix_rows=matrix_rows,
            matrix_headers=[member.id_in_group for member in players],
        )

# =============================================================================
# CLASS: FinalResult (在 game App 中)
# =============================================================================
class FinalResult(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == Constants.num_rounds

    @staticmethod
    def vars_for_template(player):
        final_payoff_jpy = player.participant.payoff_plus_participation_fee()

        return {
            'players': sorted(player.group.get_players(), key=lambda p: p.id_in_group),
            'final_payoff_jpy': final_payoff_jpy,
            'C': Constants,
            'Constants': Constants,
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
