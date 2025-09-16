from os import environ

ROOMS = [
    dict(
        name='fixed',
        display_name='罰威力の固定',
        participant_label_file='_rooms/fixed.txt',
        use_secure_urls=True
    ),
    dict(
        name='transfer_free',
        display_name='コストなしの罰威力の移譲',
        participant_label_file='_rooms/transfer_free.txt',
        use_secure_urls=True
    ),
    dict(
        name='transfer_cost',
        display_name='コストありの罰威力の移譲',
        participant_label_file='_rooms/transfer_cost.txt',
        use_secure_urls=True
    ),
]

PARTICIPANT_FIELDS = ["punishment_points_history"]
SESSION_FIELDS = ["treatment"]

# 暫く倍率を1pt=4円に設定し、参加費を500円に設定する
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=4, 
    participation_fee=500,
    doc="公共財ゲーム。Roomsで条件を振り分け。"
)

SESSION_CONFIGS = [
    dict(
        name='pggp_fixed',
        display_name="公共財ゲーム（罰威力固定）",
        app_sequence=['game'],
        num_demo_participants=5,
        players_per_group=5,
        punishment_rate=3,  # 懲罰効率
        endowment=100,  # 初期保有額
        efficiency_factor=1.6,  # 公共財の効率係数
        num_rounds=10,  # ラウンド数
        initial_punishment_endowment=5,  # 初期懲罰権
        power_transfer_allowed=False,  # 懲罰権譲渡不可
        costly_punishment_transfer=False,  # コストなし（固定なので関係ない）
        punishment_transfer_cost_rate=0,
        punishment_transfer_unit=0.1,
        practice_rounds=0,
    ),
    dict(
        name='pggp_transfer_free',
        display_name="公共財ゲーム（罰威力譲渡・コストなし）",
        app_sequence=['game'],
        num_demo_participants=5,
        players_per_group=5,
        punishment_rate=3,
        endowment=100,
        efficiency_factor=1.6,
        num_rounds=10,
        initial_punishment_endowment=5,
        power_transfer_allowed=True,  # 譲渡可能
        costly_punishment_transfer=False,  # コストなし
        punishment_transfer_cost_rate=0,
        punishment_transfer_unit=0.1,
        practice_rounds=0,
    ),
    dict(
        name='pggp_transfer_cost',
        display_name="公共財ゲーム（罰威力譲渡・コストあり）",
        app_sequence=['game'],
        num_demo_participants=5,
        players_per_group=5,
        punishment_rate=3,
        endowment=100,
        efficiency_factor=1.6,
        num_rounds=10,
        initial_punishment_endowment=5,
        power_transfer_allowed=True,  # 譲渡可能
        costly_punishment_transfer=True,  # コストあり
        punishment_transfer_cost_rate=1,  # 0.1ポイントあたり1通貨単位
        punishment_transfer_unit=0.1,
        practice_rounds=0,
    ),
]

LANGUAGE_CODE = 'ja'
REAL_WORLD_CURRENCY_CODE = 'JPY'
USE_POINTS = True
TIME_ZONE = "Asia/Tokyo" 
POINTS_CUSTOM_NAME = "実験円"  # 修正：POINTS_CUSTOM_NAME (複数形)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
SECRET_KEY = 'your-secret-key-here'

DEBUG = True
DEMO_PAGE_INTRO_HTML = """
<p>
    公共財ゲーム
</p>
<p>
    各roomのlinkから、対応する実験条件に参加してください
</p>
<ul>
    <li><a href="/room/fixed">罰威力の固定</a></li>
    <li><a href="/room/transfer_free">コストなしの罰威力の移譲</a></li>
    <li><a href="/room/transfer_cost">コストありの罰威力の移譲</a></li>
</ul>
"""
