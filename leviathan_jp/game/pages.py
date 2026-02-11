# game/pages.py

from otree.api import Page, WaitPage

from .models import Constants
from otree.api import Currency as c # Currency をインポートするための別名


def _int_display(value):
    """Format numeric-like values as integer strings for UI bars."""
    try:
        return str(int(round(float(value or 0))))
    except (TypeError, ValueError):
        return "0"


def build_history_rounds(player):
    """Collect per-round history data for templates."""
    session = player.session
    endowment = session.config.get('endowment', 0)
    endowment_currency = c(endowment)
    rounds = []

    for prev in player.in_previous_rounds():
        group = prev.group
        members = group.get_players()
        per_target_dp_limit = session.config.get(
            'per_target_dp_limit',
            session.config.get('deduction_points', 0),
        )
        max_total_dp = float(per_target_dp_limit) * max(len(members) - 1, 0)
        dp_cost_denom = max_total_dp if max_total_dp > 0 else 1.0

        player_entries = []
        has_power_transfer = (
            session.config.get('power_transfer_allowed')
            and prev.round_number >= 3
        )

        for member in members:
            total_sent = 0
            for other in members:
                if other.id_in_group == member.id_in_group:
                    continue
                field_name = f'punish_p{other.id_in_group}'
                total_sent += getattr(member, field_name, 0) or 0

            effective_sent_points = getattr(member, 'punishment_points_given_actual', None)
            if effective_sent_points is None:
                effective_sent_points = total_sent
            effective_sent_points_int = int(round(float(effective_sent_points or 0)))
            dp_fill_percent = max(
                0.0,
                min(100.0, (float(effective_sent_points_int) / dp_cost_denom) * 100.0),
            )

            player_entries.append(
                dict(
                    id_in_group=member.id_in_group,
                    contribution=member.contribution,
                    contribution_display=_int_display(member.contribution),
                    endowment=endowment_currency,
                    endowment_display=_int_display(endowment),
                    available_endowment=member.available_endowment,
                    punishment_sent_total=effective_sent_points,
                    punishment_sent_total_display=effective_sent_points_int,
                    punishment_sent_fill_percent=f"{dp_fill_percent:.2f}",
                    punishment_received_total=member.punishment_received,
                    power_before=member.punishment_power_before,
                    power_after=member.punishment_power_after,
                    power_after_display=f"{member.punishment_power_after:.1f}",
                    power_transfer_out=member.power_transfer_out_total,
                    power_transfer_out_display=f"{member.power_transfer_out_total:.1f}",
                    power_transfer_in=member.power_transfer_in_total,
                    power_transfer_in_display=f"{member.power_transfer_in_total:.1f}",
                    power_transfer_cost=member.power_transfer_cost,
                )
            )

        effectiveness_base = session.config.get('power_effectiveness', Constants.power_effectiveness)
        matrix_rows = []
        for victim in members:
            actual_loss = float(victim.punishment_received or 0)
            if actual_loss <= 0:
                victim_before = float(victim.available_before_punishment or victim.available_endowment or 0)
                victim_after = float(victim.available_endowment or 0)
                diff = victim_before - victim_after
                if diff > actual_loss:
                    actual_loss = max(0.0, diff)

            attempted_points = {}
            effective_power_map = {}
            for giver in members:
                if giver.id_in_group == victim.id_in_group:
                    continue
                points = getattr(giver, f'punish_p{victim.id_in_group}', 0) or 0
                attempted_points[giver.id_in_group] = points
                effective_power = (
                    giver.punishment_power_after
                    or giver.participant.vars.get('punishment_power', 1.0)
                )
                effective_power_map[giver.id_in_group] = effective_power
            cells = []
            total_received = 0.0
            for giver in members:
                is_self = giver.id_in_group == victim.id_in_group
                if is_self:
                    cells.append(dict(is_self=True, amount=None, amount_display=None))
                else:
                    points_attempted = attempted_points.get(giver.id_in_group, 0)
                    points_used = points_attempted
                    effective_power = effective_power_map.get(
                        giver.id_in_group,
                        giver.punishment_power_after
                        or giver.participant.vars.get('punishment_power', 1.0),
                    )
                    actual_loss_value = points_used * effectiveness_base * effective_power
                    total_received += actual_loss_value
                    loss_display = c(actual_loss_value)
                    cells.append(
                        dict(
                            is_self=False,
                            amount=loss_display,
                            amount_display=f"{actual_loss_value:.1f}",
                        )
                    )

            if victim.punishment_received is not None:
                summary_loss = victim.punishment_received
            else:
                summary_loss = c(total_received)

            for entry in player_entries:
                if entry['id_in_group'] == victim.id_in_group:
                    entry['punishment_received_total'] = summary_loss
                    break

            matrix_rows.append(dict(victim_id=victim.id_in_group, cells=cells))

        result_matrix_rows = []
        fill_denom = float(per_target_dp_limit) if float(per_target_dp_limit) > 0 else 1.0
        for giver in members:
            giver_power = float(
                giver.punishment_power_after
                or giver.participant.vars.get('punishment_power', 1.0)
            )
            row_cells = []
            for victim in members:
                if giver.id_in_group == victim.id_in_group:
                    row_cells.append(dict(is_self=True))
                    continue
                points_raw = getattr(giver, f'punish_p{victim.id_in_group}', 0) or 0
                points_value = int(round(float(points_raw)))
                effect_value = points_value * float(effectiveness_base) * giver_power
                fill_percent = max(
                    0.0,
                    min(100.0, (float(points_value) / fill_denom) * 100.0),
                )
                row_cells.append(
                    dict(
                        is_self=False,
                        points_display=str(points_value),
                        effect_display=f"{effect_value:.1f}",
                        fill_percent=f"{fill_percent:.2f}",
                    )
                )
            result_matrix_rows.append(
                dict(
                    giver_id=giver.id_in_group,
                    is_self=giver.id_in_group == player.id_in_group,
                    power_display=f"{giver_power:.1f}",
                    cells=row_cells,
                )
            )

        transfer_rows = []
        if has_power_transfer:
            for giver in members:
                cells = []
                for receiver in members:
                    is_self = giver.id_in_group == receiver.id_in_group
                    amount = None
                    if not is_self:
                        field_name = f'power_transfer_p{receiver.id_in_group}'
                        amount = getattr(giver, field_name, 0) or 0
                    cells.append(
                        dict(
                            is_self=is_self,
                            amount=amount,
                            amount_display=(f"{amount:.1f}" if amount is not None else None),
                        )
                    )
                transfer_rows.append(dict(giver_id=giver.id_in_group, cells=cells))

        rounds.append(
            dict(
                round_number=prev.round_number,
                players=player_entries,
                matrix_rows=matrix_rows,
                result_matrix_rows=result_matrix_rows,
                transfer_rows=transfer_rows,
                has_punishment=prev.round_number > 1,
                has_power_transfer=has_power_transfer,
                max_total_dp_display=f"{int(max_total_dp)}",
                per_target_dp_limit=int(per_target_dp_limit),
            )
        )

    return rounds


class BasePage(Page):
    @staticmethod
    def js_vars(player):
        return dict(
            dropout_warning_active=bool(
                player.participant.vars.get('dropout_warning_active')
            )
        )

    @staticmethod
    def live_method(player, data):
        if not isinstance(data, dict):
            return
        if data.get('dismiss_dropout_warning'):
            player.participant.vars['dropout_warning_active'] = False
            player.participant.vars['auto_play'] = False
            player.participant.vars['consecutive_timeouts'] = 0

# =============================================================================
# CLASS: Contribution
# =============================================================================
class Contribution(BasePage):
    form_model = 'player'
    form_fields = ['contribution']

    @staticmethod
    def get_timeout_seconds(player):
        if not player.session.config.get('enable_timeout_autoplay', True):
            return None
        return player.session.config.get('decision_timeout_seconds', 60)

    @staticmethod
    def _update_timeout_streak(player, timeout_happened):
        if not player.session.config.get('enable_timeout_autoplay', True):
            player.participant.vars['consecutive_timeouts'] = 0
            player.participant.vars['auto_play'] = False
            player.participant.vars['dropout_warning_active'] = False
            return
        threshold = player.session.config.get('dropout_timeout_pages', 3)
        if threshold is None or threshold <= 0:
            if not timeout_happened:
                player.participant.vars['consecutive_timeouts'] = 0
            player.participant.vars['auto_play'] = False
            player.participant.vars['dropout_warning_active'] = False
            return
        if timeout_happened:
            streak = player.participant.vars.get('consecutive_timeouts', 0) + 1
            player.participant.vars['consecutive_timeouts'] = streak
            if streak >= threshold:
                player.participant.vars['auto_play'] = True
                player.participant.vars['dropout_warning_active'] = True
        else:
            player.participant.vars['consecutive_timeouts'] = 0
            player.participant.vars['auto_play'] = False
            player.participant.vars['dropout_warning_active'] = False

    @staticmethod
    def vars_for_template(player):
        # _HistoryModal.html の player.in_all_rounds イテレータが正しい id_range を得られるようにする
        id_range = list(range(1, Constants.players_per_group + 1))
        player_count = len(player.group.get_players())
        history_allow_vertical_scroll = player_count > 5 and (player_count % 5 == 0)
        available = (
            player.available_endowment
            if player.available_endowment is not None
            else player.session.config.get('endowment', Constants.endowment)
        )
        initial_contribution = 0
        if player.round_number > 1:
            prev_contribution = player.in_round(player.round_number - 1).contribution
            prev_value = float(prev_contribution or 0)
            initial_contribution = int(max(0, prev_value))
        return dict(
            history=player.in_previous_rounds(),
            id_range=id_range,
            C=Constants,
            history_rounds=build_history_rounds(player),
            available_endowment=player.available_endowment,
            available_endowment_display=_int_display(available),
            contribution_limit_display=_int_display(available),
            initial_contribution=initial_contribution,
            show_power_info=True,
            timeout_seconds=Contribution.get_timeout_seconds(player),
            history_allow_vertical_scroll=history_allow_vertical_scroll,
        )

    @staticmethod
    def error_message(player, values):
        contribution = values.get('contribution')
        if contribution is None:
            return '貢献額を入力してください。'
        endowment = player.session.config.get('endowment', Constants.endowment)
        amount = float(contribution)
        available = float(player.available_endowment or endowment)
        if amount < 0 or amount > available:
            limit = int(available)
            return f'貢献額は0から{limit}までの範囲で入力してください。'
        if not amount.is_integer():
            return '貢献額は整数で入力してください。'
        return None

    @staticmethod
    def before_next_page(player, timeout_happened):
        Contribution._update_timeout_streak(player, timeout_happened)
        endowment = player.session.config.get('endowment', Constants.endowment)
        available = player.available_endowment if player.available_endowment is not None else c(endowment)
        if timeout_happened:
            auto_contribution = int(float(available))
            if auto_contribution < 0:
                auto_contribution = 0
            player.contribution = auto_contribution
        player.available_before_contribution = available
        remaining = available - player.contribution
        player.available_endowment = remaining
        player.available_before_punishment = remaining
        player.participant.vars['contribution_submitted_round'] = player.round_number

# =============================================================================
# CLASS: ContributionWaitPage
# =============================================================================
class ContributionWaitPage(WaitPage):
    template_name = "game/ContributionWait.html"

    @staticmethod
    def after_all_players_arrive(group):
        group.set_group_contribution()
        if group.round_number == 1:
            for player in group.get_players():
                player.set_payoff()

    @staticmethod
    def vars_for_template(player):
        players = player.group.get_players()
        current_round = player.round_number
        submitted = sum(
            1
            for p in players
            if p.participant.vars.get('contribution_submitted_round') == current_round
        )
        total = len(players)
        return dict(waiting_progress=submitted, waiting_total=total)

# =============================================================================
# CLASS: ContributionResult
# =============================================================================
class ContributionResult(BasePage):
    @staticmethod
    def get_timeout_seconds(player):
        if not player.session.config.get('enable_timeout_autoplay', True):
            return None
        return player.session.config.get('non_decision_timeout_seconds', 10)

    @staticmethod
    def before_next_page(player, timeout_happened):
        Contribution._update_timeout_streak(player, timeout_happened)

    @staticmethod
    def vars_for_template(player):
        session = player.session
        endowment = session.config['endowment']
        multiplier = float(session.config.get('contribution_multiplier', Constants.multiplier))
        share = player.group.individual_share
        group_players = sorted(player.group.get_players(), key=lambda p: p.id_in_group)

        def _compact_decimal(value):
            value_f = float(value or 0)
            if abs(value_f - round(value_f)) < 1e-9:
                return str(int(round(value_f)))
            return f"{value_f:.1f}"

        players_data = []
        for member in group_players:
            contribution = member.contribution
            remaining = member.available_endowment or c(0)
            available_before = member.available_before_contribution or remaining + contribution
            current_total = remaining + share
            contribution_value = float(contribution or 0)
            available_before_value = float(available_before or 0)
            current_total_value = float(current_total or 0)

            players_data.append(
                dict(
                    player=member,
                    contribution=contribution,
                    contribution_value=contribution_value,
                    contribution_display=_int_display(contribution_value),
                    current_total=current_total,
                    current_total_display=f"{current_total_value:.1f}",
                    available_endowment=remaining,
                    available_before_contribution=available_before,
                    available_before_display=_int_display(available_before_value),
                )
            )

        group_size = len(group_players) or 1
        total_contribution_value = float(player.group.total_contribution or 0)
        project_outcome_value = total_contribution_value * multiplier
        project_outcome_max_value = float(endowment) * group_size * multiplier
        if project_outcome_max_value > 0:
            project_outcome_fill_percent = max(
                0.0,
                min(100.0, (project_outcome_value / project_outcome_max_value) * 100.0),
            )
        else:
            project_outcome_fill_percent = 0.0

        return dict(
            players_data=players_data,
            endowment=endowment,
            share=share,
            project_outcome_value=project_outcome_value,
            project_outcome_max_value=project_outcome_max_value,
            project_outcome_fill_percent=f"{project_outcome_fill_percent:.2f}",
            project_outcome_value_display=_compact_decimal(project_outcome_value),
            project_outcome_max_display=_compact_decimal(project_outcome_max_value),
        )


class PowerTransfer(BasePage):
    form_model = "player"

    @staticmethod
    def get_timeout_seconds(player):
        if not player.session.config.get('enable_timeout_autoplay', True):
            return None
        return player.session.config.get('decision_timeout_seconds', 60)

    @staticmethod
    def is_displayed(player):
        session = player.session
        return session.config.get("power_transfer_allowed") and player.round_number >= 3

    @staticmethod
    def get_form_fields(player):
        return [
            f"power_transfer_p{i}"
            for i in range(1, Constants.players_per_group + 1)
            if i != player.id_in_group
        ]

    @staticmethod
    def vars_for_template(player):
        session = player.session
        transfer_unit = session.config.get("punishment_transfer_unit", 0.1)
        cost_per_unit = session.config.get("power_transfer_cost_rate", 0)
        others_data = []
        for other in player.get_others_in_group():
            others_data.append(
                dict(
                    id_in_group=other.id_in_group,
                    player_code=f"player {other.id_in_group}",
                    contribution=other.contribution,
                    current_power=other.punishment_power_before,
                )
            )

        # Precompute power values for template (otree templates lack round filter)
        members_data = []
        for member in player.group.get_players():
            power_value = member.punishment_power_before
            if power_value is None:
                power_value = member.participant.vars.get('punishment_power', 1.0)
            try:
                power_value = float(power_value)
            except (TypeError, ValueError):
                power_value = 0.0
            members_data.append(
                dict(
                    id_in_group=member.id_in_group,
                    is_self=member.id_in_group == player.id_in_group,
                    power_before_value=power_value,
                    power_before_display=f"{power_value:.1f}",
                )
            )

        is_costly = session.config.get("costly_punishment_transfer", False)

        return dict(
            current_power=player.punishment_power_before,
            current_power_display=f"{player.punishment_power_before:.1f}",
            transfer_unit=transfer_unit,
            transfer_unit_display=f"{transfer_unit:.1f}",
            others_data=others_data,
            members_data=members_data,
            max_transfer=player.punishment_power_before,
            is_costly=is_costly,
            transfer_cost_rate=cost_per_unit,
            transfer_cost_per_unit=cost_per_unit,
            cost_per_unit=cost_per_unit,
            cost_per_unit_display=f"{cost_per_unit:.1f}",
            currency_label=session.config.get('real_world_currency_code', 'MU'),
            players_status=[],
            timeout_seconds=PowerTransfer.get_timeout_seconds(player),
            power_max=Constants.players_per_group,
        )

    @staticmethod
    def error_message(player, values):
        transfer_unit = player.session.config.get("punishment_transfer_unit", 0.1)
        tolerance = 1e-6
        total = 0
        for value in values.values():
            if value is None:
                continue
            if value < -tolerance:
                return "譲渡量は0以上で入力してください。"
            total += value
            if transfer_unit > 0:
                multiples = value / transfer_unit
                if abs(multiples - round(multiples)) > 1e-6:
                    return f"譲渡量は {transfer_unit} の倍数で入力してください。"

        if total - player.punishment_power_before > tolerance:
            return "譲渡量の合計が保有する罰威力を超えています。"

    @staticmethod
    def before_next_page(player, timeout_happened):
        Contribution._update_timeout_streak(player, timeout_happened)
        session = player.session
        transfer_fields = [
            f"power_transfer_p{i}"
            for i in range(1, Constants.players_per_group + 1)
            if i != player.id_in_group
        ]
        if timeout_happened:
            for field in transfer_fields:
                setattr(player, field, 0)
        total_out = 0
        for field in transfer_fields:
            value = player.field_maybe_none(field)
            if value is None:
                value = 0
                setattr(player, field, value)
            total_out += value
        player.power_transfer_out_total = round(total_out, 3)

        unit = session.config.get("punishment_transfer_unit", 0.1)
        rate = session.config.get("power_transfer_cost_rate", 0)
        if session.config.get("costly_punishment_transfer") and unit > 0:
            units = total_out / unit
            cost_value = units * rate
            player.power_transfer_cost = c(cost_value)
        else:
            player.power_transfer_cost = c(0)

        player.punishment_power_after = max(
            0,
            player.punishment_power_before - player.power_transfer_out_total,
        )
        player.participant.vars['power_transfer_submitted_round'] = player.round_number


class PowerTransferWait(WaitPage):
    template_name = "game/PowerTransferWait.html"

    @staticmethod
    def is_displayed(player):
        session = player.session
        return session.config.get("power_transfer_allowed") and player.round_number >= 3

    @staticmethod
    def after_all_players_arrive(group):
        players = group.get_players()
        for player in players:
            total_in = 0
            for other in players:
                if other.id_in_group == player.id_in_group:
                    continue
                field_name = f"power_transfer_p{player.id_in_group}"
                total_in += getattr(other, field_name, 0) or 0
            player.power_transfer_in_total = round(total_in, 3)
            player.punishment_power_after = max(
                0,
                round(
                    player.punishment_power_before
                    - player.power_transfer_out_total
                    + player.power_transfer_in_total,
                    3,
                ),
            )
            player.participant.vars["punishment_power"] = player.punishment_power_after

            # Carry over the updated punishment power to the next round so that
            # the transfer results persist. creating_session runs before the
            # experiment starts, meaning the defaults written there (1.0) need
            # to be replaced once we know the actual outcome of this round.
            if player.round_number < Constants.num_rounds:
                next_player = player.in_round(player.round_number + 1)
                next_player.punishment_power_before = player.punishment_power_after
                next_player.punishment_power_after = player.punishment_power_after
                next_player.participant.vars["punishment_power"] = player.punishment_power_after

            endowment = player.session.config.get('endowment', Constants.endowment)
            cost_value = float(player.power_transfer_cost or 0)
            remaining = max(0, endowment - cost_value)
            player.available_endowment = c(remaining)

    @staticmethod
    def vars_for_template(player):
        players = player.group.get_players()
        current_round = player.round_number
        submitted = sum(
            1
            for p in players
            if p.participant.vars.get('power_transfer_submitted_round') == current_round
        )
        total = len(players)
        return dict(waiting_progress=submitted, waiting_total=total)


class PowerTransferResult(BasePage):
    @staticmethod
    def get_timeout_seconds(player):
        if not player.session.config.get('enable_timeout_autoplay', True):
            return None
        return player.session.config.get('non_decision_timeout_seconds', 10)

    @staticmethod
    def before_next_page(player, timeout_happened):
        Contribution._update_timeout_streak(player, timeout_happened)

    @staticmethod
    def is_displayed(player):
        session = player.session
        return session.config.get("power_transfer_allowed") and player.round_number >= 3

    @staticmethod
    def vars_for_template(player):
        session = player.session
        group_players = sorted(
            player.group.get_players(), key=lambda p: p.id_in_group
        )

        columns = []
        for member in group_players:
            transfer_cost_value = member.power_transfer_cost
            if transfer_cost_value is None:
                transfer_cost_display = "0.0"
            else:
                transfer_cost_display = f"{float(transfer_cost_value):.1f}"
            final_power_value = float(member.punishment_power_after or 0)
            columns.append(
                dict(
                    id_in_group=member.id_in_group,
                    is_self=member.id_in_group == player.id_in_group,
                    header=f"プレイヤー {member.id_in_group}",
                    base_power_value=float(member.punishment_power_before or 0),
                    final_power_display=f"{member.punishment_power_after:.1f}",
                    final_power_value=final_power_value,
                    net_transfer_display=f"- {member.power_transfer_out_total:.1f} / + {member.power_transfer_in_total:.1f}",
                    transfer_cost_display=transfer_cost_display,
                    current_balance_display="-",
                )
            )

        transfer_matrix = []
        for giver in group_players:
            row_cells = []
            for receiver in group_players:
                if giver.id_in_group == receiver.id_in_group:
                    row_cells.append(dict(is_self=True, highlight=False, display="-"))
                else:
                    field_name = f"power_transfer_p{receiver.id_in_group}"
                    amount = getattr(giver, field_name, 0) or 0
                    row_cells.append(
                        dict(
                            is_self=False,
                            highlight=receiver.id_in_group == player.id_in_group,
                            display=f"{amount:.1f}",
                        )
                    )
            transfer_matrix.append(
                dict(
                    row_label=f"プレイヤー {giver.id_in_group}",
                    is_self=giver.id_in_group == player.id_in_group,
                    cells=row_cells,
                )
            )

        headers = [
            "あなたへの転移" if p.id_in_group == player.id_in_group else f"プレイヤー {p.id_in_group} への転移"
            for p in group_players
        ]
        columns_length = len(columns)

        return dict(
            columns=columns,
            columns_length=columns_length,
            columns_length_plus_one=columns_length + 1,
            transfer_matrix=transfer_matrix,
            transfer_headers=headers,
            round_number=player.round_number,
            is_costly=session.config.get("costly_punishment_transfer", False),
            power_max=Constants.players_per_group,
        )



# =============================================================================
# CLASS: Punishment
# =============================================================================
class Punishment(BasePage):
    form_model = 'player'

    @staticmethod
    def get_timeout_seconds(player):
        if not player.session.config.get('enable_timeout_autoplay', True):
            return None
        return player.session.config.get('decision_timeout_seconds', 60)

    @staticmethod
    def get_form_fields(player):
        fields = []
        group = player.group
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
        id_range = list(range(1, Constants.players_per_group + 1))
        session = player.session
        endowment = session.config['endowment']
        contribution = player.contribution if hasattr(player, 'contribution') else 0

        if player.available_before_punishment is not None:
            remaining_mu = player.available_before_punishment
        elif player.available_endowment is not None:
            remaining_mu = player.available_endowment
        else:
            remaining_mu = endowment - contribution
        remaining_mu_value = float(remaining_mu) if remaining_mu is not None else 0.0

        players = sorted(player.group.get_players(), key=lambda p: p.id_in_group)
        history_allow_vertical_scroll = len(players) > 5 and (len(players) % 5 == 0)
        players_data = []
        self_power_value = 1.0
        for member in players:
            power_value = member.punishment_power_after
            if power_value is None:
                power_value = member.punishment_power_before or member.participant.vars.get('punishment_power', 1.0)
            if member.id_in_group == player.id_in_group:
                self_power_value = float(power_value)
            players_data.append(
                dict(
                    player=member,
                    id_in_group=member.id_in_group,
                    is_self=member.id_in_group == player.id_in_group,
                    contribution=member.contribution,
                    contribution_display=_int_display(member.contribution),
                    power_value=float(power_value),
                    power_display=f"{float(power_value):.1f}",
                )
            )

        endowment_display = _int_display(endowment)
        deduction_points = session.config.get('per_target_dp_limit', session.config['deduction_points'])
        punishment_cost = session.config.get('punishment_cost', 1)
        max_total_dp = float(deduction_points) * max(len(players) - 1, 0)
        max_punishment_cost = max_total_dp * float(punishment_cost)
        max_total_dp_display = f"{int(max_total_dp)}"

        return dict(
            players_data=players_data,
            deduction_points=deduction_points,
            per_target_dp_limit=deduction_points,
            endowment=endowment,
            endowment_display=endowment_display,
            id_range=id_range,
            history_rounds=build_history_rounds(player),
            remaining_mu=remaining_mu,
            remaining_mu_value=remaining_mu_value,
            show_power_info=False,
            timeout_seconds=Punishment.get_timeout_seconds(player),
            punishment_cost=punishment_cost,
            max_total_dp=max_total_dp,
            max_total_dp_display=max_total_dp_display,
            max_punishment_cost=max_punishment_cost,
            max_punishment_cost_display=f"{max_punishment_cost:.1f}",
            power_effectiveness=session.config.get('power_effectiveness', Constants.power_effectiveness),
            self_power_value=self_power_value,
            history_allow_vertical_scroll=history_allow_vertical_scroll,
        )

    @staticmethod
    def error_message(player, values):
        total_punishment = 0
        per_target_limit = player.session.config.get('per_target_dp_limit', player.session.config['deduction_points'])
        endowment = player.session.config.get('endowment', Constants.endowment)
        contribution = player.contribution or 0
        for i in range(1, Constants.players_per_group + 1):
            field_name = f'punish_p{i}'
            if field_name in values and values[field_name] is not None:
                value = values[field_name]
                if value < 0:
                    return "DPは0以上の整数で入力してください。"
                if int(value) != value:
                    return "DPは整数で入力してください。"
                if value > per_target_limit:
                    return f"各プレイヤーへのDPは {per_target_limit} 以内で入力してください。"
                total_punishment += value
        punishment_cost = player.session.config.get('punishment_cost', 1)
        total_cost = total_punishment * punishment_cost
        available = float(player.available_before_punishment or player.available_endowment or 0)
        computed_available = float(endowment - contribution)
        if computed_available > available + 1e-6:
            available = computed_available
        if total_cost > available + 1e-4:
            if punishment_cost > 0:
                max_points = int((available + 1e-6) // punishment_cost)
            else:
                max_points = total_punishment
            return f"現在、使えるMUsは {max_points} です。もう一度試して下さい。"

    @staticmethod
    def before_next_page(player, timeout_happened):
        Contribution._update_timeout_streak(player, timeout_happened)
        punishment_cost = player.session.config.get('punishment_cost', 1)
        total_punishment = 0
        for i in range(1, Constants.players_per_group + 1):
            field_name = f'punish_p{i}'
            if hasattr(player, field_name):
                if timeout_happened:
                    setattr(player, field_name, 0)
                value = getattr(player, field_name, 0) or 0
                total_punishment += value
        total_cost = c(total_punishment * punishment_cost)
        player.available_before_punishment = player.available_endowment or c(0)
        player.attempted_punishment_cost = total_cost
        player.attempted_punishment_points = total_punishment
        player.participant.vars['punishment_submitted_round'] = player.round_number

# =============================================================================
# CLASS: PunishmentWaitPage
# =============================================================================
class PunishmentWaitPage(WaitPage):
    template_name = "game/PunishmentWait.html"

    @staticmethod
    def is_displayed(player):
        return player.round_number > 1

    @staticmethod
    def after_all_players_arrive(group):
        group.set_payoff()

    @staticmethod
    def vars_for_template(player):
        players = player.group.get_players()
        current_round = player.round_number
        submitted = sum(
            1
            for p in players
            if p.participant.vars.get('punishment_submitted_round') == current_round
        )
        total = len(players)
        return dict(waiting_progress=submitted, waiting_total=total)

# =============================================================================
# CLASS: RoundResult
# =============================================================================
class RoundResult(BasePage):
    @staticmethod
    def get_timeout_seconds(player):
        if not player.session.config.get('enable_timeout_autoplay', True):
            return None
        return player.session.config.get('non_decision_timeout_seconds', 10)

    @staticmethod
    def is_displayed(player):
        return player.round_number > 1

    @staticmethod
    def vars_for_template(player):
        session = player.session
        treatment_name = session.config.get('treatment_name', 'fixed')
        show_power_transfer = (
            session.config.get('power_transfer_allowed')
            and player.round_number >= 3
        )

        endowment = session.config['endowment']
        per_target_dp_limit = session.config.get('per_target_dp_limit', session.config['deduction_points'])
        endowment_currency = c(endowment)
        share = player.group.individual_share

        cumulative_payoff = player.participant.vars.get('cumulative_payoff', c(0))
        payoff_from_contribution = endowment_currency - player.contribution + share

        players = sorted(player.group.get_players(), key=lambda p: p.id_in_group)
        effectiveness_base = session.config.get('power_effectiveness', Constants.power_effectiveness)
        max_total_dp = float(per_target_dp_limit) * max(len(players) - 1, 0)
        max_total_dp_display = f"{int(max_total_dp)}"
        dp_cost_denom = max_total_dp if max_total_dp > 0 else 1.0

        players_map = {}
        for member in players:
            available_before_contribution = (
                member.available_before_contribution
                or (member.available_endowment or c(0)) + (member.contribution or c(0))
            )
            power_after_value = float(
                member.punishment_power_after
                or member.participant.vars.get('punishment_power', 1.0)
            )
            players_map[member.id_in_group] = dict(
                id_in_group=member.id_in_group,
                contribution=member.contribution,
                contribution_display=_int_display(member.contribution),
                endowment=endowment_currency,
                punishment_sent_total=0,
                punishment_sent_total_display="0",
                punishment_received_total=0,
                power_before=member.punishment_power_before,
                power_after=power_after_value,
                power_after_display=f"{power_after_value:.1f}",
                power_after_value=power_after_value,
                power_transfer_out=member.power_transfer_out_total,
                power_transfer_in=member.power_transfer_in_total,
                power_transfer_out_display=f"{member.power_transfer_out_total:.1f}",
                power_transfer_in_display=f"{member.power_transfer_in_total:.1f}",
                power_transfer_cost=member.power_transfer_cost,
                available_endowment=member.available_endowment,
                available_before_contribution=available_before_contribution,
                available_before_contribution_display=_int_display(available_before_contribution),
                punishment_effect_display="0.0",
                punishment_sent_fill_percent="0.00",
            )

        for member in players:
            total_sent = getattr(member, 'punishment_points_given_actual', None)
            if total_sent is None:
                total_sent = 0
                for other in players:
                    if other.id_in_group == member.id_in_group:
                        continue
                    field_name = f'punish_p{other.id_in_group}'
                    total_sent += getattr(member, field_name, 0) or 0
            players_map[member.id_in_group]['punishment_sent_total'] = total_sent
            players_map[member.id_in_group]['punishment_sent_total_display'] = str(int(round(float(total_sent))))
            effect_total = float(total_sent) * float(effectiveness_base) * players_map[member.id_in_group]['power_after_value']
            players_map[member.id_in_group]['punishment_effect_display'] = f"{effect_total:.1f}"
            players_map[member.id_in_group]['punishment_sent_fill_percent'] = (
                f"{max(0.0, min(100.0, (float(total_sent) / dp_cost_denom) * 100.0)):.2f}"
            )

        matrix_rows = []
        max_per_target = float(per_target_dp_limit) if float(per_target_dp_limit) > 0 else 1.0
        for giver in players:
            giver_power = players_map[giver.id_in_group]['power_after_value']
            row_cells = []
            for victim in players:
                is_self = giver.id_in_group == victim.id_in_group
                if is_self:
                    row_cells.append(dict(is_self=True))
                    continue

                points_raw = getattr(giver, f'punish_p{victim.id_in_group}', 0) or 0
                points_value = int(round(float(points_raw)))
                effect_value = float(points_value) * float(effectiveness_base) * float(giver_power)
                fill_percent = max(0.0, min(100.0, (float(points_value) / max_per_target) * 100.0))
                row_cells.append(
                    dict(
                        is_self=False,
                        points=points_value,
                        points_display=str(points_value),
                        effect_display=f"{effect_value:.1f}",
                        fill_percent=f"{fill_percent:.2f}",
                    )
                )

            matrix_rows.append(
                dict(
                    giver_id=giver.id_in_group,
                    is_self=giver.id_in_group == player.id_in_group,
                    power_display=players_map[giver.id_in_group]['power_after_display'],
                    cells=row_cells,
                )
            )

        players_summary = [players_map[idx] for idx in sorted(players_map.keys())]
        matrix_headers = [
            dict(
                id_in_group=member.id_in_group,
                is_self=member.id_in_group == player.id_in_group,
            )
            for member in players
        ]
        round_result_allow_vertical_scroll = len(players) > 5 and (len(players) % 5 == 0)

        return dict(
            payoff_from_contribution=payoff_from_contribution,
            cumulative_payoff=cumulative_payoff,
            players_summary=players_summary,
            matrix_rows=matrix_rows,
            matrix_headers=matrix_headers,
            show_power_transfer=show_power_transfer,
            treatment_name=treatment_name,
            per_target_dp_limit=per_target_dp_limit,
            max_total_dp=max_total_dp,
            max_total_dp_display=max_total_dp_display,
            endowment=endowment_currency,
            round_result_allow_vertical_scroll=round_result_allow_vertical_scroll,
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        Contribution._update_timeout_streak(player, timeout_happened)
        stop_round = player.session.config.get('browser_bot_stop_round')
        if (
            stop_round
            and player.round_number == stop_round
            and player.participant.is_browser_bot
        ):
            player.participant.is_browser_bot = False

        session = player.session
        if session.vars.get('early_stop_round'):
            return

        min_rounds = session.config.get('early_stop_min_rounds', 14)
        dropout_threshold = session.config.get('early_stop_dropout_count', 2)
        if dropout_threshold is None or dropout_threshold <= 0:
            return
        if player.round_number >= min_rounds:
            group_players = player.group.get_players()
            dropout_count = sum(
                1
                for p in group_players
                if p.participant.vars.get('auto_play')
            )
            if dropout_count >= dropout_threshold:
                session.vars['early_stop_round'] = player.round_number
                for p in group_players:
                    p.participant.vars['early_stop'] = True
                    p.participant.vars['early_stop_round'] = player.round_number

# =============================================================================
# CLASS: FinalResult (ゲームアプリ内の最終ページ)
# =============================================================================
class FinalResult(BasePage):
    @staticmethod
    def get_timeout_seconds(player):
        if not player.session.config.get('enable_timeout_autoplay', True):
            return None
        return player.session.config.get('non_decision_timeout_seconds', 10)

    @staticmethod
    def before_next_page(player, timeout_happened):
        Contribution._update_timeout_streak(player, timeout_happened)

    @staticmethod
    def is_displayed(player):
        early_stop_round = player.participant.vars.get('early_stop_round')
        if early_stop_round:
            return player.round_number == early_stop_round
        return player.round_number == Constants.num_rounds

    @staticmethod
    def app_after_this_page(player, upcoming_apps):
        early_stop_round = player.participant.vars.get('early_stop_round')
        if early_stop_round and player.round_number < Constants.num_rounds:
            if upcoming_apps:
                return upcoming_apps[0]
        return None

    @staticmethod
    def vars_for_template(player):
        final_payoff_jpy = player.participant.payoff_plus_participation_fee()
        performance_payoff = player.participant.payoff.to_real_world_currency(player.session)
        currency_code = player.session.config.get('real_world_currency_code', 'JPY')

        return {
            'players': sorted(player.group.get_players(), key=lambda p: p.id_in_group),
            'final_payoff_jpy': final_payoff_jpy,
            'C': Constants,
            'Constants': Constants,
            'performance_payoff': performance_payoff,
            'currency_code': currency_code,
        }


# =============================================================================
# ページの表示順
# =============================================================================
page_sequence = [
    PowerTransfer,
    PowerTransferWait,
    PowerTransferResult,
    Contribution,
    ContributionWaitPage,
    ContributionResult,
    Punishment,
    PunishmentWaitPage,
    RoundResult,
    FinalResult, # <--- ゲームアプリの最後に表示する最終結果ページ
]
