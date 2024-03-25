from domain import RocketDomain

class GraphPlan:
    def __init__(self, r_fact):
        self.rd = RocketDomain(r_fact)
        self.layers = []

    class Layer:
        def __init__(self):
            self.actions = {}
            self.propositions = {}
            self.mutex_actions = {}
            self.mutex_propositions = {}
            self.preconditions_links = {}
            self.positive_effects_links = {}
            self.negative_effects_links = {}

    def expand(self):
        new_layer = self.Layer()
        new_layer.actions = self.get_next_actions(self.layers[-1].propositions, self.layers[-1].mutex_propositions)
        new_layer.mutex_actions = self.get_mutex_actions(new_layer.actions, self.layers[-1].mutex_propositions)
        new_layer.propositions = self.get_next_propositions(new_layer.actions)
        new_layer.mutex_propositions = self.get_mutex_propositions(new_layer.propositions, new_layer.mutex_actions)
        for action in new_layer.actions:
            for prop in action.preconditions:
                if prop in self.layers[-1].propositions:
                    new_layer.preconditions_links.add((prop, action))
            for prop in action.positive_effects:
                if prop in self.propositions:
                    new_layer.positive_effects_links.add((action, prop))
            for prop in action.negative_effects:
                if prop in self.propositions:
                    new_layer.negative_effects_links.add((action, prop))
        self.layers.append(new_layer)

    def get_producers(self, proposition, actions):
        """
        Returns a set of actions that have the given proposition as a positive effect.
        :param proposition: Proposition object
        :param actions: list of Action objects
        :return: list
        """
        return {action for action in actions if proposition in action.positive_effects}
    
    def are_mutex_actions(self, action1, action2, mutex_propositions):
        if action1 == action2:
            return False
        if self.actions_dependencies[(action1, action2)]:
            return True
        for prop1 in action1.preconditions:
            for prop2 in action2.preconditions:
                if {prop1, prop2} in mutex_propositions:
                    return True
        return False

    def are_mutex_propositions(self, prop1, prop2, mutex_actions):
        if prop1 == prop2:
            return False
        for action1 in self.get_producers(prop1, self.actions):
            for action2 in self.get_producers(prop2, self.actions):
                if {action1, action2} not in mutex_actions:
                    return False
        return True

    def get_mutex_actions(self, actions, mutex_propositions):
        """
        Returns a set of set of actions that are mutex.
        :param actions: list of Action objects
        :param mutex_propositions: list of tuples of Proposition objects
        :return: list
        """
        return {{action1, action2} for action1 in actions for action2 in actions if self.are_mutex_actions(action1, action2, mutex_propositions)}

    def get_mutex_propositions(self, propositions, mutex_actions):
        """
        Returns a set of tuples of propositions that are mutex.
        :param propositions: list of Proposition objects
        :param mutex_actions: list of tuples of Action objects
        :return: list
        """
        return {{prop1, prop2} for prop1 in propositions for prop2 in propositions if self.are_mutex_propositions(prop1, prop2, mutex_actions)}
    
    def get_next_actions(self, previous_propositions, previous_mutex_propositions):
        """
        Returns a set of Action objects that can be added to the next layer.
        :param previous_propositions: list of Proposition objects
        :param previous_mutex_propositions: list of tuples of Proposition objects
        :return: list
        """
        next_actions = {}
        for action in self.rd.actions:
            for prop1 in action.preconditions:
                if prop1 not in previous_propositions:
                    break
                for prop2 in action.preconditions:
                    if {prop1, prop2} in previous_mutex_propositions:
                        break
                else:
                    continue
                break
            else:
                next_actions.add(action)
        for prop in previous_propositions:
            next_actions.add(self.rd.NOOP(prop))
        return next_actions
    
    def get_next_propositions(self, current_actions):
        """
        Returns a set of Proposition objects that can be added to the next layer.
        :param actions: set of Action objects
        :return: set
        """
        next_propositions = {}
        for action in current_actions:
            for prop in action.positive_effects:
                next_propositions.add(prop)
        return next_propositions
