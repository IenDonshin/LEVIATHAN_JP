from os import environ

from os import environ
SESSION_CONFIGS = [
    dict(
        name='public_goods',
        display_name="公共物品博弈",
        app_sequence=['game'],
        num_demo_participants=4,
    ),
]
# 如果您使用的是较旧版本的 oTree，可能需要添加：
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc=""
)
PARTICIPANT_FIELDS = []
SESSION_FIELDS = []
# ISO-639 code
LANGUAGE_CODE = 'zh-hans'
# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'CNY'
USE_POINTS = True
ADMIN_USERNAME = 'admin'
# recommended to put in environ variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '8789319257150'

INSTALLED_APPS = ['otree']