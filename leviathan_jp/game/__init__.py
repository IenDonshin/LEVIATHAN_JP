from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'public_goods_game'
    PLAYERS_PER_GROUP = 5 
    NUM_ROUNDS = 10
    
    # 实验参数
    ENDOWMENT = cu(20)
    MULTIPLIER = 2 
    
    # 指令文本
    INSTRUCTIONS = """
    欢迎参加本次实验！
    
    在每一轮中：
    1. 您将获得{}的初始资金
    2. 您可以选择向公共账户贡献0到{}之间的任意金额
    3. 您保留的金额将直接计入您的收益
    4. 所有人贡献到公共账户的总金额将乘以{}
    5. 然后平均分配给组内所有{}名成员
    
    您的收益 = 保留的金额 + 公共账户分配
    """.format(ENDOWMENT, ENDOWMENT, MULTIPLIER, PLAYERS_PER_GROUP)
class Subsession(BaseSubsession):
    pass
class Group(BaseGroup):
    total_contribution = models.CurrencyField()  # 组内总贡献
    individual_share = models.CurrencyField()  # 每人从公共账户获得的金额
class Player(BasePlayer):
    contribution = models.CurrencyField(
        min=0,
        max=C.ENDOWMENT,
        label="您想向公共账户贡献多少？"
    )
    
    # 记录收益相关变量
    private_account = models.CurrencyField()  # 私人账户（保留的钱）
    public_account_share = models.CurrencyField()  # 从公共账户获得的份额
# PAGES
class Instructions(Page):
    """说明页面"""
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1  # 只在第一轮显示
class Contribute(Page):
    """贡献决策页面"""
    form_model = 'player'
    form_fields = ['contribution']
    
    @staticmethod
    def vars_for_template(player):
        return {
            'round_number': player.round_number,
            'endowment': C.ENDOWMENT,
        }
class ResultsWaitPage(WaitPage):
    """等待所有人完成决策"""
    body_text = "请等待其他参与者完成决策..."
    
    @staticmethod
    def after_all_players_arrive(group):
        # 计算总贡献
        contributions = [p.contribution for p in group.get_players()]
        group.total_contribution = sum(contributions)
        
        # 计算公共账户总额和每人份额
        public_account_total = group.total_contribution * C.MULTIPLIER
        group.individual_share = public_account_total / C.PLAYERS_PER_GROUP
        
        # 计算每个玩家的收益
        for p in group.get_players():
            p.private_account = C.ENDOWMENT - p.contribution
            p.public_account_share = group.individual_share
            p.payoff = p.private_account + p.public_account_share
class Results(Page):
    """结果展示页面"""
    @staticmethod
    def vars_for_template(player):
        group = player.group
        
        return {
            'my_contribution': player.contribution,
            'total_contribution': group.total_contribution,
            'my_private_account': player.private_account,
            'public_account_share': player.public_account_share,
            'my_payoff': player.payoff,
            'others_contributions': [
                p.contribution for p in group.get_players() 
                if p.id != player.id
            ],
        }
class FinalResults(Page):
    """最终结果页面"""
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
    
    @staticmethod
    def vars_for_template(player):
        # 计算所有轮次的总收益
        total_payoff = sum([p.payoff for p in player.in_all_rounds()])
        
        # 获取每轮的数据
        rounds_data = []
        for p in player.in_all_rounds():
            rounds_data.append({
                'round': p.round_number,
                'contribution': p.contribution,
                'payoff': p.payoff
            })
        
        return {
            'total_payoff': total_payoff,
            'rounds_data': rounds_data,
        }
page_sequence = [
    Instructions,
    Contribute,
    ResultsWaitPage,
    Results,
    FinalResults,
]