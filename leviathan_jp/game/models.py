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
    
    # 从 settings.py 中获取参数
    # 如果 settings.py 中没有定义，则使用这里的默认值
    endowment = 20
    multiplier = 1.5
    deduction_points = 10
    punishment_cost = 1
    punishment_effectiveness = 1

class Subsession(BaseSubsession):
    def creating_session(self):
        # 从 session.config 中读取实验参数，这样就可以通过 settings.py 灵活配置
        self.group_randomly()
        if self.round_number == 1:
            for p in self.get_players():
                p.participant.vars['cumulative_payoff'] = 0


class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    individual_share = models.CurrencyField()

    def set_group_contribution(self):
        """计算小组总贡献和每个人的回报"""
        players = self.get_players()
        contributions = [p.contribution for p in players]
        self.total_contribution = sum(contributions)
        self.individual_share = (
            self.total_contribution * self.session.config['contribution_multiplier'] / Constants.players_per_group
        )

    def set_payoff(self):
        """在惩罚阶段结束后为每位玩家结算收益"""
        for player in self.get_players():
            player.set_payoff()

class Player(BasePlayer):
    contribution = models.CurrencyField(
        min=0,
        label="您想为公共项目贡献多少？",
    )

    def contribution_max(self):
        return self.session.config['endowment']

    # 为每个可能的惩罚对象创建一个字段
    # 假设小组最多有5人，id_in_group 从 1 到 5
    punish_p1 = models.IntegerField(min=0, initial=0, label="对玩家1的惩罚点数")
    punish_p2 = models.IntegerField(min=0, initial=0, label="对玩家2的惩罚点数")
    punish_p3 = models.IntegerField(min=0, initial=0, label="对玩家3的惩罚点数")
    punish_p4 = models.IntegerField(min=0, initial=0, label="对玩家4的惩罚点数")
    punish_p5 = models.IntegerField(min=0, initial=0, label="对玩家5的惩罚点数")

    punishment_given = models.CurrencyField(doc="送出的惩罚总成本")
    punishment_received = models.CurrencyField(doc="收到的惩罚总损失")

    # payoff 字段 oTree 会自动创建，我们将在后面给它赋值

    def set_payoff(self):
        """计算本轮最终收益"""
        # 惩罚相关计算
        # 1. 计算自己送出惩罚的总点数和成本
        punishment_fields = [self.punish_p1, self.punish_p2, self.punish_p3, self.punish_p4, self.punish_p5]
        # 排除对自己惩罚的字段（虽然界面上会禁止，但逻辑上要严谨）
        # id_in_group 是从 1 开始的
        punishment_points_given = 0
        for i in range(len(punishment_fields)):
            if (i + 1) != self.id_in_group:
                 punishment_points_given += punishment_fields[i] if punishment_fields[i] is not None else 0
        
        self.punishment_given = punishment_points_given * self.session.config['punishment_cost']

        # 2. 计算自己收到的总惩罚点数和损失
        punishment_points_received = 0
        for other_player in self.get_others_in_group():
            field_name = f'punish_p{self.id_in_group}'
            punishment_points_received += getattr(other_player, field_name, 0)
        
        self.punishment_received = punishment_points_received * self.session.config['punishment_effectiveness']

        # 3. 根据公式计算最终收益
        # π_i = E - c_i + (m/n)Σc_j - pc*Σd_ij - pe*Σd_ji
        payoff_before_punishment = (
            self.session.config['endowment'] - self.contribution + self.group.individual_share
        )
        self.payoff = payoff_before_punishment - self.punishment_given - self.punishment_received
        
        # 更新累计收益
        if 'cumulative_payoff' not in self.participant.vars:
            self.participant.vars['cumulative_payoff'] = c(0)
        self.participant.vars['cumulative_payoff'] += self.payoff
