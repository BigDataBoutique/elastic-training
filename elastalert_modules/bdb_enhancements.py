from elastalert.enhancements import BaseEnhancement
from datetime import datetime
class MyEnhancement(BaseEnhancement):

    # The enhancement is run against every match
    # The match is passed to the process function where it can be modified in any way
    # ElastAlert will do this for each enhancement linked to a rule
    def process(self, match):
        match['triggered_time'] = datetime.now()