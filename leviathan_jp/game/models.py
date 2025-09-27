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
Public Goods Game with Punishment (Fixed)
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
    punishment_effectiveness = 1

class Subsession(BaseSubsession):
    def creating_session(self):
        # session.config から実験設定を読み込み、settings.py で柔軟に変更可能にする
        self.group_randomly()
        if self.round_number == 1:
            for p in self.get_players():
                p.participant.vars['cumulative_payoff'] = 0


class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    individual_share = models.CurrencyField()

    def set_group_contribution(self):
        """グループの総貢献額と各自の取り分を計算"""
        players = self.get_players()
        contributions = [p.contribution or 0 for p in players]
        self.total_contribution = sum(contributions)
        group_size = len(players) or 1
        multiplier = self.session.config.get('contribution_multiplier', Constants.multiplier)
        share_value = float(self.total_contribution) * float(multiplier) / group_size
        self.individual_share = c(share_value)

    def set_payoff(self):
        """懲罰フェーズ終了後に各プレイヤーの利得を確定"""
        for player in self.get_players():
            player.set_payoff()

class Player(BasePlayer):
    contribution = models.CurrencyField(
        min=0,
        max=Constants.endowment,
        initial=0,
        label="公共財プロジェクトにいくら拠出しますか？",
    )

    def contribution_max(self):
        return self.session.config['endowment']

    # 各プレイヤーに与える罰点を入力するフィールド
    # グループは最大5人を想定し、id_in_group は 1〜5
    punish_p1 = models.IntegerField(min=0, initial=0, label="プレイヤー1への罰点")
    punish_p2 = models.IntegerField(min=0, initial=0, label="プレイヤー2への罰点")
    punish_p3 = models.IntegerField(min=0, initial=0, label="プレイヤー3への罰点")
    punish_p4 = models.IntegerField(min=0, initial=0, label="プレイヤー4への罰点")
    punish_p5 = models.IntegerField(min=0, initial=0, label="プレイヤー5への罰点")

    punishment_given = models.CurrencyField(doc="与えた罰の総コスト")
    punishment_received = models.CurrencyField(doc="受けた罰による総損失")

    # payoff フィールドは oTree が自動生成するため、後で値を代入する

    def set_payoff(self):
        """今ラウンドの最終利得を計算"""
        # 懲罰に関する計算
        # 1. 自分が与えた罰点とコストを集計
        punishment_fields = [self.punish_p1, self.punish_p2, self.punish_p3, self.punish_p4, self.punish_p5]
        # 自分自身への罰フィールドは除外（UI でも制限しているが念のため）
        # id_in_group は 1 から始まる
        punishment_points_given = 0
        for i in range(len(punishment_fields)):
            if (i + 1) != self.id_in_group:
                 punishment_points_given += punishment_fields[i] if punishment_fields[i] is not None else 0
        
        self.punishment_given = punishment_points_given * self.session.config['punishment_cost']

        # 2. 自分が受けた罰点と損失を集計
        punishment_points_received = 0
        for other_player in self.get_others_in_group():
            field_name = f'punish_p{self.id_in_group}'
            punishment_points_received += getattr(other_player, field_name, 0)
        
        self.punishment_received = punishment_points_received * self.session.config['punishment_effectiveness']

        # 3. 式に基づいて最終利得を算出
        # π_i = E - c_i + (m/n)Σc_j - pc*Σd_ij - pe*Σd_ji
        payoff_before_punishment = (
            self.session.config['endowment'] - self.contribution + self.group.individual_share
        )
        self.payoff = payoff_before_punishment - self.punishment_given - self.punishment_received
        
        # 累積利得を更新
        if 'cumulative_payoff' not in self.participant.vars:
            self.participant.vars['cumulative_payoff'] = c(0)
        self.participant.vars['cumulative_payoff'] += self.payoff
