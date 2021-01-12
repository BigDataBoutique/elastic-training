
from elastalert.ruletypes import FrequencyRule



class FrequencyComparisonRule(FrequencyRule):
    @staticmethod
    def compareValues(actualValue,comparator,compareValue):
        if comparator == "gte":
            return actualValue >= compareValue
        elif comparator == "eq":
            return actualValue == compareValue
        elif comparator == "gt":
            return actualValue > compareValue
        elif comparator == "lt":
            return actualValue < compareValue
        elif comparator == "lte":
            return actualValue <= compareValue

    def check_for_match(self, key, end=False):
        # Match if, after removing old events, the comparison returns true for num_events.
        # the 'end' parameter depends on whether this was called from the
        # middle or end of an add_data call and is used in subclasses

        if self.compareValues(self.occurrences[key].count(),self.rules['frequency_comparison_relation'], self.rules['num_events']):
            event = self.occurrences[key].data[-1][0]
            if self.attach_related:
                event['related_events'] = [data[0] for data in self.occurrences[key].data[:-1]]
            self.add_match(event)
            self.occurrences.pop(key)