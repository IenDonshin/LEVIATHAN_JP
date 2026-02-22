from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)

doc = """
Public goods game with deduction and deduction-effect transfer.
"""

class Constants(BaseConstants):
    name_in_url = 'game'
    players_per_group = 5
    num_rounds = 20
    
    # settings.py からパラメータを取得
    # settings.py で未定義の場合は以下のデフォルトを使用
    endowment = 20
    multiplier = 1.5
    deduction_points = 10
    punishment_cost = 1
    power_effectiveness = 1

class Subsession(BaseSubsession):
    def creating_session(self):
        # session.config から実験設定を読み込み、settings.py で柔軟に変更可能にする
        self.group_randomly()
        players = self.get_players()

        for p in players:
            if self.round_number == 1:
                initial_power = 1.0
                p.participant.vars['cumulative_payoff'] = c(0)
                p.participant.vars['punishment_power'] = initial_power
            else:
                prev_round = p.in_round(self.round_number - 1)
                initial_power = prev_round.punishment_power_after or p.participant.vars.get('punishment_power', 1.0)
                p.participant.vars['punishment_power'] = initial_power

            p.punishment_power_before = initial_power
            p.punishment_power_after = initial_power
            p.power_transfer_out_total = 0
            p.power_transfer_in_total = 0
            p.power_transfer_cost = c(0)
            p.available_endowment = c(self.session.config.get('endowment', Constants.endowment))
            p.available_before_contribution = p.available_endowment
            p.available_before_punishment = p.available_endowment
            p.attempted_punishment_cost = c(0)
            p.attempted_punishment_points = 0
            p.punishment_points_given_actual = 0
            p.punishment_points_received_actual = 0

            for i in range(1, Constants.players_per_group + 1):
                setattr(p, f'power_transfer_p{i}', 0)


class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    individual_share = models.CurrencyField()

    def set_group_contribution(self):
        """グループの総投資額と各自の取り分を計算"""
        players = self.get_players()
        contributions = [p.contribution or 0 for p in players]
        self.total_contribution = sum(contributions)
        group_size = len(players) or 1
        multiplier = self.session.config.get('contribution_multiplier', Constants.multiplier)
        share_value = float(self.total_contribution) * float(multiplier) / group_size
        self.individual_share = c(share_value)

    def set_payoff(self):
        """減点フェーズ終了後に各プレイヤーの利得を確定"""
        self.adjust_punishments()
        for player in self.get_players():
            player.set_payoff()

    def adjust_punishments(self):
        session = self.session
        players = self.get_players()
        cost_per_point = session.config.get('punishment_cost', 1)
        effectiveness_base = session.config.get('power_effectiveness', Constants.power_effectiveness)

        actual_cost = {p: 0.0 for p in players}
        actual_points_sent = {p: 0.0 for p in players}

        for victim in players:
            punish_entries = []
            for punisher in players:
                if punisher.id_in_group == victim.id_in_group:
                    continue
                attempted_points = getattr(punisher, f'punish_p{victim.id_in_group}', 0) or 0
                if attempted_points <= 0:
                    continue
                effective_power = punisher.punishment_power_after or punisher.participant.vars.get('punishment_power', 1.0)
                loss_per_point = effectiveness_base * effective_power
                punish_entries.append((punisher, attempted_points, loss_per_point))

            actual_loss = 0.0
            received_points = 0.0
            for punisher, attempted_points, loss_per_point in punish_entries:
                points_used = attempted_points
                loss = points_used * loss_per_point
                actual_loss += loss
                received_points += points_used

                actual_points_sent[punisher] += points_used
                actual_cost[punisher] += points_used * cost_per_point

            available_before = float(victim.available_before_punishment or victim.available_endowment or 0)
            victim_available = available_before - actual_loss
            victim.available_endowment = c(victim_available)
            victim.punishment_points_received_actual = received_points
            victim.punishment_received = c(actual_loss)

        for punisher in players:
            attempted_cost = float(punisher.attempted_punishment_cost or 0)
            actual_cost_value = min(actual_cost[punisher], attempted_cost)

            available_before = float(punisher.available_before_punishment or punisher.available_endowment or 0)
            new_available = available_before - actual_cost_value
            punisher.available_endowment = c(new_available)
            punisher.punishment_given = c(actual_cost_value)
            punisher.punishment_points_given_actual = actual_points_sent[punisher]


class Player(BasePlayer):
    # Round 1: public goods introduction quiz
    intro1_q1 = models.IntegerField(
        label="第1問：あなたが20 MUのうち10 MUを投資した場合、分配前に手元に残るMUはいくらですか？",
        choices=[
            [1, "0 MU"],
            [2, "10 MU"],
            [3, "20 MU"],
        ],
        widget=widgets.RadioSelect,
    )
    intro1_q2 = models.IntegerField(
        label="第2問：5人グループで投資合計40 MUの場合、1.5倍後に1人あたり受け取るMUはいくらですか？",
        choices=[
            [1, "8 MU"],
            [2, "12 MU"],
            [3, "15 MU"],
        ],
        widget=widgets.RadioSelect,
    )
    intro1_q3 = models.IntegerField(
        label="第3問：あなたが10 MUを残し、グループ・プロジェクトから12 MUを受け取る場合、最終収益はいくらですか？",
        choices=[
            [1, "10 MU"],
            [2, "12 MU"],
            [3, "22 MU"],
        ],
        widget=widgets.RadioSelect,
    )
    intro1_q4 = models.IntegerField(
        label="第4問：他のグループメンバーの識別について正しいものはどれですか？",
        choices=[
            [1, "毎ラウンド異なるランダムなIDで表示される。"],
            [2, "誰がどの決定をしたかは一切表示されない。"],
            [3, "毎ラウンド同じIDで表示される。"],
        ],
        widget=widgets.RadioSelect,
    )

    # Round 2: deduction introduction quiz
    intro2_q1 = models.IntegerField(
        label="第1問：あなたが他者に2ポイントの減点を与えると、あなた自身のMUはどうなりますか？",
        choices=[
            [1, "自分のMUは変わらない。"],
            [2, "自分のMUが1減る。"],
            [3, "自分のMUが2減る。"],
        ],
        widget=widgets.RadioSelect,
    )
    intro2_q2 = models.IntegerField(
        label="第2問：あなたが他者に2ポイントの減点を与えると、相手のMUはどうなりますか？",
        choices=[
            [1, "相手のMUは変わらない。"],
            [2, "相手のMUが1減る。"],
            [3, "相手のMUが2減る。"],
        ],
        widget=widgets.RadioSelect,
    )
    intro2_q3 = models.IntegerField(
        label="第3問：他者があなたに4ポイントの減点を与えると、あなたのMUはどうなりますか？",
        choices=[
            [1, "自分のMUは変わらない。"],
            [2, "自分のMUが2減る。"],
            [3, "自分のMUが4減る。"],
        ],
        widget=widgets.RadioSelect,
    )

    # Round 3: power-transfer introduction quiz (transfer treatments)
    intro3_transfer_q1 = models.IntegerField(
        label="第1問：あなたが減点効果0.2を移譲するとき、コストはいくらですか？",
        choices=[
            [1, "0 MU（コストはかからない）"],
            [2, "1.0 MU"],
            [3, "2.0 MU"],
        ],
        widget=widgets.RadioSelect,
    )
    intro3_transfer_q2 = models.IntegerField(
        label="第2問：あなたの減点効果が0.0のとき、3ポイントの減点を与えた結果はどうなりますか？",
        choices=[
            [1, "自分のMUは減らず、相手のMUが3減る。"],
            [2, "自分のMUは3減るが、相手のMUは減らない。"],
            [3, "自分のMUは3減り、相手のMUも3減る。"],
        ],
        widget=widgets.RadioSelect,
    )
    intro3_transfer_q3 = models.IntegerField(
        label="第3問：あなたの減点効果が2.0のとき、3ポイントの減点を与えた結果はどうなりますか？",
        choices=[
            [1, "自分のMUは6減り、相手のMUも6減る。"],
            [2, "自分のMUは3減り、相手のMUは6減る。"],
            [3, "自分のMUは3減り、相手のMUも3減る。"],
        ],
        widget=widgets.RadioSelect,
    )

    # Round 3: fixed treatment confirmation quiz
    intro3_fixed_q1 = models.IntegerField(
        label="第1問：固定条件でこの後の流れとして正しいものはどれですか？",
        choices=[
            [1, "「投資フェーズ → 減点フェーズ」を繰り返す。"],
            [2, "「投資フェーズ → 減点効果移譲フェーズ → 減点フェーズ」を繰り返す。"],
            [3, "次ラウンドから減点フェーズは行われない。"],
        ],
        widget=widgets.RadioSelect,
    )

    contribution = models.CurrencyField(
        min=0,
        max=Constants.endowment,
        initial=0,
    )

    def contribution_max(self):
        if self.available_endowment is not None:
            return self.available_endowment
        return self.session.config['endowment']

    # 各プレイヤーに与える減点を入力するフィールド
    # グループは最大5人を想定し、id_in_group は 1〜5
    punish_p1 = models.IntegerField(min=0, initial=0, label="プレイヤー1への減点")
    punish_p2 = models.IntegerField(min=0, initial=0, label="プレイヤー2への減点")
    punish_p3 = models.IntegerField(min=0, initial=0, label="プレイヤー3への減点")
    punish_p4 = models.IntegerField(min=0, initial=0, label="プレイヤー4への減点")
    punish_p5 = models.IntegerField(min=0, initial=0, label="プレイヤー5への減点")

    punishment_given = models.CurrencyField(doc="与えた減点の総コスト")
    punishment_received = models.CurrencyField(doc="受けた減点による総損失")

    # 減点効果の移譲に関するフィールド
    power_transfer_p1 = models.FloatField(min=0, initial=0, blank=True)
    power_transfer_p2 = models.FloatField(min=0, initial=0, blank=True)
    power_transfer_p3 = models.FloatField(min=0, initial=0, blank=True)
    power_transfer_p4 = models.FloatField(min=0, initial=0, blank=True)
    power_transfer_p5 = models.FloatField(min=0, initial=0, blank=True)

    power_transfer_out_total = models.FloatField(initial=0, blank=True)
    power_transfer_in_total = models.FloatField(initial=0, blank=True)
    punishment_power_before = models.FloatField(initial=1.0, blank=True)
    punishment_power_after = models.FloatField(initial=1.0, blank=True)
    power_transfer_cost = models.CurrencyField(initial=c(0), blank=True)
    available_endowment = models.CurrencyField(initial=Constants.endowment, blank=True)
    available_before_contribution = models.CurrencyField(initial=Constants.endowment, blank=True)
    available_before_punishment = models.CurrencyField(initial=Constants.endowment, blank=True)
    attempted_punishment_cost = models.CurrencyField(initial=c(0), blank=True)
    attempted_punishment_points = models.FloatField(initial=0, blank=True)
    punishment_points_given_actual = models.FloatField(initial=0, blank=True)
    punishment_points_received_actual = models.FloatField(initial=0, blank=True)

    # payoff フィールドは oTree が自動生成するため、後で値を代入する

    def set_payoff(self):
        """今ラウンドの最終利得を計算"""
        # 減点に関する計算
        # 1. 自分が与えた減点とコストを集計
        punishment_points_given = self.punishment_points_given_actual
        if punishment_points_given in (None, 0):
            punishment_points_given = 0
            punishment_fields = [self.punish_p1, self.punish_p2, self.punish_p3, self.punish_p4, self.punish_p5]
            for i in range(len(punishment_fields)):
                if (i + 1) != self.id_in_group:
                    punishment_points_given += punishment_fields[i] if punishment_fields[i] is not None else 0
            self.punishment_points_given_actual = punishment_points_given
            self.punishment_given = c(punishment_points_given * self.session.config['punishment_cost'])

        # 2. 自分が受けた減点と損失を集計
        punishment_points_received = self.punishment_points_received_actual
        if punishment_points_received in (None, 0):
            punishment_points_received = 0
            punishment_loss = 0
            effectiveness_base = self.session.config.get('power_effectiveness', Constants.power_effectiveness)
            for other_player in self.get_others_in_group():
                field_name = f'punish_p{self.id_in_group}'
                points = getattr(other_player, field_name, 0) or 0
                punishment_points_received += points
                effective_power = other_player.punishment_power_after or other_player.participant.vars.get('punishment_power', 1.0)
                punishment_loss += points * effectiveness_base * effective_power
            self.punishment_points_received_actual = punishment_points_received
            self.punishment_received = c(punishment_loss)

        # 3. 式に基づいて最終利得を算出
        # π_i = E - c_i + (m/n)Σc_j - pc*Σd_ij - pe*Σd_ji
        payoff_before_punishment = (
            self.session.config['endowment'] - self.contribution + self.group.individual_share
        )
        total_costs = self.punishment_given + self.punishment_received + self.power_transfer_cost
        self.payoff = payoff_before_punishment - total_costs
        
        # 累積利得を更新
        if 'cumulative_payoff' not in self.participant.vars:
            self.participant.vars['cumulative_payoff'] = c(0)
        self.participant.vars['cumulative_payoff'] += self.payoff
        self.participant.vars['punishment_power'] = self.punishment_power_after
