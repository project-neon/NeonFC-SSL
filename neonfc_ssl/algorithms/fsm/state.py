class State:
    def __init__(self):
        self.transitions = []  # [(condition, next_sate)]

    def update(self, *args, **kwargs):
        for state, condition in self.transitions:
            if condition(*args, **kwargs):
                return state
        return self

    def add_transition(self, state, condition):
        self.transitions.append((state, condition))
