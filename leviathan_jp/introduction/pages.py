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
                return (
                    f"固定条件の解答が正しくありません。初期保有額は{player.session.config['endowment']}、"
                    f"公共財の乗数は{player.session.config['contribution_multiplier']}です。もう一度確認してください。"
                )
        elif treatment == 'transfer_free':
            # 假设罰威力可以移譲，移譲成本为0，最大可移譲点数为初始惩罚点数
            if values['q1_transfer_free'] != 'yes' or \
               values['q2_transfer_free'] != 0 or \
               values['q3_transfer_free'] != player.session.config['deduction_points']:
                return (
                    f"無コスト移譲条件の解答が正しくありません。罰威力は移譲可能で、移譲コストは0、"
                    f"最大移譲ポイントは{player.session.config['deduction_points']}です。もう一度確認してください。"
                )
        elif treatment == 'transfer_cost':
            # 假设罰威力可以移譲，移譲成本率为1，需要支付成本
            if values['q1_transfer_cost'] != player.session.config['punishment_transfer_cost_rate'] or \
               values['q2_transfer_cost'] != 'yes':
                return (
                    f"コストあり移譲条件の解答が正しくありません。移譲コスト率は"
                    f"{player.session.config['punishment_transfer_cost_rate']}であり、罰威力を移譲する際にはコストが必要です。"
                    "もう一度確認してください。"
                )

page_sequence = [Introduction, Test]
