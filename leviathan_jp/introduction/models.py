from otree.api import (
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    models,
    widgets,
)


class Constants(BaseConstants):
    name_in_url = 'introduction'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
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

    intro3_fixed_q1 = models.IntegerField(
        label="第1問：固定条件でこの後の流れとして正しいものはどれですか？",
        choices=[
            [1, "「投資フェーズ → 減点フェーズ」を繰り返す。"],
            [2, "「投資フェーズ → 減点効果移譲フェーズ → 減点フェーズ」を繰り返す。"],
            [3, "次ラウンドから減点フェーズは行われない。"],
        ],
        widget=widgets.RadioSelect,
    )
