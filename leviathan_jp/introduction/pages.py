# introduction/pages.py

from otree.api import Page, WaitPage

from .models import Constants

class Introduction(Page): # 之前可能是 IntroductionFixed
    @staticmethod
    def vars_for_template(player):
        return {
            'treatment_name': player.session.config['treatment_name']
        }

class Test(Page): # 之前可能是 TestFixed
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        treatment = player.session.config['treatment_name']
        if treatment == 'fixed':
            return ['q1_fixed', 'q2_fixed']
        elif treatment == 'transfer_free':
            return ['q1_transfer_free', 'q2_transfer_free', 'q3_transfer_free']
        elif treatment == 'transfer_cost':
            return ['q1_transfer_cost', 'q2_transfer_cost']
        return []

    @staticmethod
    def vars_for_template(player):
        return {
            'treatment_name': player.session.config['treatment_name']
        }

    @staticmethod
    def error_message(player, values):
        treatment = player.session.config['treatment_name']
        # 注意: 这里的正确答案应该与您的实验设计相符
        if treatment == 'fixed':
            if values['q1_fixed'] != player.session.config['endowment'] or \
               values['q2_fixed'] != player.session.config['contribution_multiplier']:
                return f"固定惩罚条件下的测试答案不正确。初始禀赋是{player.session.config['endowment']}，公共池乘数是{player.session.config['contribution_multiplier']}，请重新尝试。"
        elif treatment == 'transfer_free':
            # 假设惩罚权可以转移，转移成本为0，最大可转移点数为初始惩罚点数
            if values['q1_transfer_free'] != 'yes' or \
               values['q2_transfer_free'] != 0 or \
               values['q3_transfer_free'] != player.session.config['deduction_points']:
                return f"无成本转移条件下的测试答案不正确。惩罚权可以转移，转移成本为0，最大可转移点数为{player.session.config['deduction_points']}，请重新尝试。"
        elif treatment == 'transfer_cost':
            # 假设惩罚权可以转移，转移成本率为1，需要支付成本
            if values['q1_transfer_cost'] != player.session.config['punishment_transfer_cost_rate'] or \
               values['q2_transfer_cost'] != 'yes':
                return f"有成本转移条件下的测试答案不正确。转移成本率为{player.session.config['punishment_transfer_cost_rate']}，转移惩罚需要支付成本，请重新尝试。"

page_sequence = [Introduction, Test]
