from domain import RocketDomain

class GraphPlan:




    
    def get_producers(self, proposition, actions):
        """
        Returns a list of actions that have the given proposition as a positive effect.
        :param proposition: Proposition object
        :param actions: list of Action objects
        :return: list
        """
        return [action for action in actions if proposition in action.positive_effects]
    
    def are_mutex_actions(self, action1, action2, mutex_propositions):
        if action1 == action2:
            return False
        if self.actions_dependencies[(action1, action2)]:
            return True
        for prop1 in action1.preconditions:
            for prop2 in action2.preconditions:
                if (prop1, prop2) in mutex_propositions:
                    return True
        return False

    def are_mutex_propositions(self, prop1, prop2, mutex_actions):
        for action1 in self.get_producers(prop1, self.actions):
            for action2 in self.get_producers(prop2, self.actions):
                if (action1, action2) not in mutex_actions:
                    return False
        return True

    def get_mutex_actions(self, actions, mutex_propositions):
        """
        Returns a set of tuples of actions that are mutex.
        :param actions: list of Action objects
        :param mutex_propositions: list of tuples of Proposition objects
        :return: list
        """
        return {(action1, action2) for action1 in actions for action2 in actions if self.are_mutex_actions(action1, action2, mutex_propositions)}

    def get_mutex_propositions(self, propositions, mutex_actions):
        """
        Returns a set of tuples of propositions that are mutex.
        :param propositions: list of Proposition objects
        :param mutex_actions: list of tuples of Action objects
        :return: list
        """
        return {(prop1, prop2) for prop1 in propositions for prop2 in propositions if self.are_mutex_propositions(prop1, prop2, mutex_actions)}