# survey/pages.py

from otree.api import *

class Questionnaire(Page): # 之前可能是 QuestionnaireFixed
    def vars_for_template(self):
        return {
            'treatment_name': self.session.config['treatment_name']
        }

page_sequence = [Questionnaire]