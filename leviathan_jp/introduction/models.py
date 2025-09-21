# introduction/models.py
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer, Currency as c
)

class Constants(BaseConstants):
    name_in_url = 'introduction'
    players_per_group = None # 介绍 App 通常不需要分组
    num_rounds = 1 # 介绍 App 通常只有1轮

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # 针对不同实验条件的测试题字段
    q1_fixed = models.IntegerField(label="固定条件问题1：您的初始禀赋是多少？", min=0)
    q2_fixed = models.FloatField(label="固定条件问题2：公共池乘数是多少？", min=0)

    q1_transfer_free = models.StringField(label="无成本转移条件问题1：惩罚权可以转移吗？", choices=['yes', 'no'])
    q2_transfer_free = models.FloatField(label="无成本转移条件问题2：转移惩罚的成本是多少？", min=0)
    q3_transfer_free = models.IntegerField(label="无成本转移条件问题3：您最多能转移多少惩罚点？", min=0)

    q1_transfer_cost = models.IntegerField(label="有成本转移条件问题1：转移成本率是多少？", min=0)
    q2_transfer_cost = models.StringField(label="有成本转移条件问题2：转移惩罚需要支付成本吗？", choices=['yes', 'no'])

    # TODO: 更多测试题字段，根据实际需求添加