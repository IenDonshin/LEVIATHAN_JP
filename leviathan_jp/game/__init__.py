# game/__init__.py

from otree.api import *
import random

doc = """
公共財ゲームの実験
"""

class C(BaseConstants):
    NAME_IN_URL = 'game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 10  # デフォルト値、settings.pyで上書き可能

class Subsession(BaseSubsession):
    treatment = models.StringField()

class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    total_earning = models.CurrencyField()
    public_good = models.CurrencyField()

class Player(BasePlayer):
    # 各ラウンドの変数
    contribution = models.CurrencyField(
        min=0,
        max=100,  # will be overridden in form
        label="あなたの貢献額"
    )
    punishment_sent = models.CurrencyField(initial=0)
    punishment_received = models.CurrencyField(initial=0)
    
    # 懲罰権関連
    punishment_endowment = models.FloatField(initial=0)
    
    # 利得関連
    round_payoff = models.CurrencyField(initial=0)
    payoff_from_contribution = models.CurrencyField(initial=0)
    
    # 罰を与える各プレイヤーへの決定
    punish_p1 = models.CurrencyField(min=0, initial=0)
    punish_p2 = models.CurrencyField(min=0, initial=0) 
    punish_p3 = models.CurrencyField(min=0, initial=0)
    punish_p4 = models.CurrencyField(min=0, initial=0)
    punish_p5 = models.CurrencyField(min=0, initial=0)
    
    # 懲罰権の譲渡関連
    transfer_amount = models.FloatField(min=0, initial=0, label="譲渡する懲罰権")
    transfer_to = models.IntegerField(
        choices=[],  # 動的に設定
        label="譲渡相手",
        blank=True
    )
    transfer_cost = models.CurrencyField(initial=0)
    punishment_received_from_transfer = models.FloatField(initial=0)

# FUNCTIONS
def creating_session(subsession: Subsession):
    """セッション作成時の初期設定"""
    session = subsession.session
    
    # treatment設定
    if 'treatment' not in session.vars:
        # ROOMベースでtreatmentを決定
        room_name = session.config.get('room_name', '')
        if room_name == 'transfer_free':
            session.vars['treatment'] = 'transfer_free'
        elif room_name == 'transfer_cost':
            session.vars['treatment'] = 'transfer_cost'
        else:
            # デフォルトはpower_transfer_allowedの設定に従う
            if session.config.get('power_transfer_allowed', False):
                if session.config.get('costly_punishment_transfer', False):
                    session.vars['treatment'] = 'transfer_cost'
                else:
                    session.vars['treatment'] = 'transfer_free'
            else:
                session.vars['treatment'] = 'fixed'
    
    # subsessionにtreatmentを設定
    subsession.treatment = session.vars['treatment']
    
    # グループサイズを設定から取得
    players_per_group = session.config.get('players_per_group', 5)
    
    # 最初のラウンドでグループを作成
    if subsession.round_number == 1:
        subsession.group_randomly()
    else:
        # 2回目以降は同じグループを維持
        subsession.group_like_round(1)
    
    # 各プレイヤーの初期設定
    for player in subsession.get_players():
        if subsession.round_number == 1:
            # 初期懲罰権の付与
            player.punishment_endowment = session.config.get('initial_punishment_endowment', 5)
            # 参加者フィールドの初期化
            player.participant.punishment_points_history = []

def set_payoffs(group: Group):
    """グループの利得計算"""
    players = group.get_players()
    session = group.session
    
    # パラメータ取得
    endowment = session.config.get('endowment', 100)
    efficiency_factor = session.config.get('efficiency_factor', 1.6)
    punishment_rate = session.config.get('punishment_rate', 3)
    
    # 1. 貢献の合計を計算
    contributions = [p.contribution for p in players]
    total_contribution = sum(contributions)
    group.total_contribution = total_contribution
    
    # 2. 公共財を計算
    group.public_good = total_contribution * efficiency_factor
    
    # 3. 各プレイヤーの貢献からの利得を計算
    for p in players:
        p.payoff_from_contribution = (endowment - p.contribution) + (group.public_good / len(players))
    
    # 4. 罰の計算
    for p in players:
        # 与えた罰の合計
        punishment_given = 0
        for other in p.get_others_in_group():
            punish_field = f"punish_p{other.id_in_group}"
            if hasattr(p, punish_field):
                punishment_given += getattr(p, punish_field) or 0
        
        p.punishment_sent = punishment_given
        
        # 受けた罰の合計
        punishment_received = 0
        for other in p.get_others_in_group():
            punish_field = f"punish_p{p.id_in_group}"
            if hasattr(other, punish_field):
                punishment_received += getattr(other, punish_field) or 0
        
        p.punishment_received = punishment_received
    
    # 5. 最終利得を計算
    for p in players:
        # 罰のコスト（与えた罰）
        punishment_cost = p.punishment_sent
        
        # 罰の被害（受けた罰 × 罰率）
        punishment_damage = p.punishment_received * punishment_rate
        
        # このラウンドの利得
        p.round_payoff = p.payoff_from_contribution - punishment_cost - punishment_damage
        
        # トータル利得に加算
        p.payoff = p.round_payoff

def transfer_punishment_power(group: Group):
    """懲罰権の譲渡処理"""
    session = group.session
    treatment = session.vars.get('treatment', 'fixed')
    
    if treatment == 'fixed':
        return
    
    players = group.get_players()
    transfer_unit = session.config.get('punishment_transfer_unit', 0.1)
    
    # 譲渡処理
    for player in players:
        if player.transfer_amount > 0 and player.transfer_to:
            # 譲渡先を探す
            for other in players:
                if other.id_in_group == player.transfer_to:
                    # 譲渡実行
                    player.punishment_endowment -= player.transfer_amount
                    other.punishment_endowment += player.transfer_amount
                    other.punishment_received_from_transfer += player.transfer_amount
                    
                    # コスト計算（transfer_costの場合）
                    if treatment == 'transfer_cost':
                        cost_rate = session.config.get('punishment_transfer_cost_rate', 1)
                        player.transfer_cost = (player.transfer_amount / transfer_unit) * cost_rate
                    break

# PAGES
class Introduction(Page):
    """ゲーム説明ページ"""
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1
    
    @staticmethod
    def vars_for_template(player):
        session = player.session
        treatment = session.vars.get('treatment', 'fixed')
        group_size = len(player.get_others_in_group()) + 1
        
        # 根据不同条件准备不同的介绍内容
        return {
            'treatment': treatment,
            'group_size': group_size,
            'endowment': session.config.get('endowment', 100),
            'efficiency_factor': session.config.get('efficiency_factor', 1.6),
            'punishment_rate': session.config.get('punishment_rate', 3),
            'initial_punishment_endowment': session.config.get('initial_punishment_endowment', 5),
            'num_rounds': C.NUM_ROUNDS,
            'transfer_allowed': treatment in ['transfer_free', 'transfer_cost'],
            'transfer_has_cost': treatment == 'transfer_cost',
            'punishment_transfer_cost_rate': session.config.get('punishment_transfer_cost_rate', 1),
            'punishment_transfer_unit': session.config.get('punishment_transfer_unit', 0.1),
        }

class Contribution(Page):
    """貢献決定ページ"""
    form_model = 'player'
    form_fields = ['contribution']
    
    @staticmethod
    def contribution_max(player):
        return player.session.config.get('endowment', 100)
    
    @staticmethod
    def vars_for_template(player):
        # 履歴データ
        history = []
        if player.round_number > 1:
            for r in range(1, player.round_number):
                prev_player = player.in_round(r)
                history.append({
                    'round': r,
                    'contribution': prev_player.contribution,
                    'round_payoff': prev_player.round_payoff,
                })
        
        return {
            'endowment': player.session.config.get('endowment', 100),
            'round_number': player.round_number,
            'history': history,
            'my_punishment_endowment': player.punishment_endowment,
        }

class ResultsWaitPage(WaitPage):
    """全員の貢献決定を待つ"""
    body_text = "他のプレイヤーの決定を待っています..."
    
    @staticmethod
    def after_all_players_arrive(group):
        # まだ利得計算はしない（罰の後で計算）
        pass

class TransferPunishment(Page):
    """懲罰権譲渡ページ"""
    form_model = 'player'
    form_fields = ['transfer_to', 'transfer_amount']
    
    @staticmethod
    def is_displayed(player):
        treatment = player.session.vars.get('treatment', 'fixed')
        return treatment in ['transfer_free', 'transfer_cost']
    
    @staticmethod
    def transfer_amount_max(player):
        return player.punishment_endowment
    
    @staticmethod 
    def transfer_to_choices(player):
        choices = [(p.id_in_group, f'プレイヤー {p.id_in_group}') for p in player.get_others_in_group()]
        return choices
    
    @staticmethod
    def vars_for_template(player):
        treatment = player.session.vars.get('treatment', 'fixed')
        return {
            'treatment': treatment,
            'my_punishment_endowment': player.punishment_endowment,
            'transfer_has_cost': treatment == 'transfer_cost',
            'punishment_transfer_cost_rate': player.session.config.get('punishment_transfer_cost_rate', 1),
            'punishment_transfer_unit': player.session.config.get('punishment_transfer_unit', 0.1),
            'others_data': [
                {
                    'id_in_group': p.id_in_group,
                    'player_code': f'プレイヤー {p.id_in_group}',
                }
                for p in player.get_others_in_group()
            ]
        }

class TransferWaitPage(WaitPage):
    """懲罰権譲渡を待つ"""
    body_text = "他のプレイヤーの決定を待っています..."
    
    @staticmethod
    def is_displayed(group):
        treatment = group.session.vars.get('treatment', 'fixed')
        return treatment in ['transfer_free', 'transfer_cost']
    
    @staticmethod
    def after_all_players_arrive(group):
        transfer_punishment_power(group)

class Punishment(Page):
    """懲罰決定ページ"""
    form_model = 'player'
    
    @staticmethod
    def get_form_fields(player):
        # 他のプレイヤーの数に応じてフィールドを決定
        others = player.get_others_in_group()
        fields = []
        for other in others:
            field_name = f'punish_p{other.id_in_group}'
            if hasattr(player, field_name):
                fields.append(field_name)
        return fields
    
    @staticmethod
    def vars_for_template(player):
        group = player.group
        players = group.get_players()
        
        # 平均貢献を計算
        avg_contribution = sum([p.contribution for p in players]) / len(players)
        
        # 他のプレイヤーのデータ
        others_data = []
        for p in player.get_others_in_group():
            others_data.append({
                'id_in_group': p.id_in_group,
                'player_code': f'プレイヤー {p.id_in_group}',
                'contribution': p.contribution,
            })
        
        # 履歴データ
        history = []
        if player.round_number > 1:
            for r in range(1, player.round_number):
                prev_player = player.in_round(r)
                history.append({
                    'round': r,
                    'contribution': prev_player.contribution,
                    'payoff_from_contribution': prev_player.payoff_from_contribution,
                    'punishment_sent': prev_player.punishment_sent,
                    'punishment_received': prev_player.punishment_received,
                    'round_payoff': prev_player.round_payoff,
                })
        
        return {
            'punishment_endowment': player.punishment_endowment,
            'my_contribution': player.contribution,
            'avg_contribution': avg_contribution,
            'others_data': others_data,
            'history': history,
            'round_number': player.round_number,
        }
    
    @staticmethod
    def error_message(player, values):
        # 罰の合計が上限を超えていないかチェック
        total_punishment = sum(values.values())
        if total_punishment > player.punishment_endowment:
            return f'懲罰の合計（{total_punishment}）が利用可能な懲罰権（{player.punishment_endowment}）を超えています。'

class PunishmentWaitPage(WaitPage):
    """全員の懲罰決定を待つ"""
    body_text = "他のプレイヤーの決定を待っています..."
    
    @staticmethod
    def after_all_players_arrive(group):
        set_payoffs(group)

class Results(Page):
    """結果表示ページ"""
    @staticmethod
    def vars_for_template(player):
        group = player.group
        
        # 次ラウンドの懲罰権を計算
        next_round_punishment = player.punishment_endowment - player.punishment_sent + player.punishment_received_from_transfer
        
        # 履歴データを更新
        history_item = {
            'round': player.round_number,
            'contribution': player.contribution,
            'punishment_sent': player.punishment_sent,
            'punishment_received': player.punishment_received,
            'round_payoff': player.round_payoff,
            'punishment_endowment': player.punishment_endowment,
        }
        
        if not hasattr(player.participant, 'punishment_points_history'):
            player.participant.punishment_points_history = []
        player.participant.punishment_points_history.append(history_item)
        
        # 次のラウンドがある場合、懲罰権を更新
        if player.round_number < C.NUM_ROUNDS:
            next_player = player.in_round(player.round_number + 1)
            next_player.punishment_endowment = next_round_punishment
        
        return {
            'total_contribution': group.total_contribution,
            'public_good': group.public_good,
            'my_contribution': player.contribution,
            'payoff_from_contribution': player.payoff_from_contribution,
            'punishment_sent': player.punishment_sent,
            'punishment_received': player.punishment_received,
            'round_payoff': player.round_payoff,
            'next_round_punishment': next_round_punishment,
            'transfer_cost': player.transfer_cost if hasattr(player, 'transfer_cost') else 0,
            'is_final_round': player.round_number == C.NUM_ROUNDS,
        }

class FinalResults(Page):
    """最終結果ページ"""
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
    
    @staticmethod
    def vars_for_template(player):
        # 全ラウンドの履歴
        history = player.participant.punishment_points_history
        
        # 合計を計算
        total_payoff = sum([h['round_payoff'] for h in history])
        total_contribution = sum([h['contribution'] for h in history])
        total_punishment_sent = sum([h['punishment_sent'] for h in history])
        total_punishment_received = sum([h['punishment_received'] for h in history])
        
        return {
            'history': history,
            'total_payoff': total_payoff,
            'total_contribution': total_contribution,
            'total_punishment_sent': total_punishment_sent,
            'total_punishment_received': total_punishment_received,
            'average_payoff': total_payoff / C.NUM_ROUNDS,
        }

page_sequence = [
    Introduction,
    Contribution,
    ResultsWaitPage,
    TransferPunishment,
    TransferWaitPage,
    Punishment,
    PunishmentWaitPage,
    Results,
    FinalResults,
]
