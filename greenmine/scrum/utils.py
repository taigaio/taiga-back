from django.conf import settings

__all__ = ('SCRUM_STATES',)


class GmScrumStates(object):
    def __init__(self):
        self._states = settings.GM_SCRUM_STATES

    def get_task_choices(self):
        task_choices = []
        for us_state in self._states.values():
            task_choices += us_state['task_states']
        return task_choices

    def get_us_choices(self):
        us_choices = []
        for key, value in self._states.iteritems():
            us_choices.append((key, value['name']))
        return us_choices

    def get_finished_task_states(self):
        finished_task_states = []
        for us_state in self._states.values():
            if us_state['is_finished']:
                finished_task_states += us_state['task_states']
        return [x[0] for x in finished_task_states]

    def get_unfinished_task_states(self):
        unfinished_task_states = []
        for us_state in self._states.values():
            if not us_state['is_finished']:
                unfinished_task_states += us_state['task_states']
        return [x[0] for x in unfinished_task_states]

    def get_finished_us_states(self):
        finished_us_states = []
        for key, value in self._states.iteritems():
            if value['is_finished']:
                finished_us_states.append(key)
        return finished_us_states

    def get_unfinished_us_states(self):
        finished_us_states = []
        for key, value in self._states.iteritems():
            if not value['is_finished']:
                finished_us_states.append(key)
        return finished_us_states

    def get_us_state_for_task_state(self, state):
        for key, value in self._states.iteritems():
            if state in [x[0] for x in value['task_states']]:
                return key
        return None

    def get_task_states_for_us_state(self, state):
        if state in self._states.keys():
            return [x[0] for x in self._states[state]['task_states']]
        return None

    def ordered_us_states(self):
        ordered = sorted([(value['order'], key) for key, value in self._states.iteritems()])
        return [x[1] for x in ordered]

SCRUM_STATES = GmScrumStates()
