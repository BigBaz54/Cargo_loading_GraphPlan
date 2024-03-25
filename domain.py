class Proposition:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __str__(self):
        return f'{self.args[0]} {self.name} {self.args[1] if len(self.args) > 1 else ""}'
    
    def __eq__(self, other):
        return self.name == other.name and self.args == other.args

class Action:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.preconditions = {}
        self.positive_effects = {}
        self.negative_effects = {}

    def __eq__(self, other):
        return self.name == other.name and self.args == other.args

class RocketDomain:
    def __init__(self, r_fact):
        self.cargos, self.rockets, self.places, self.init_propositions, self.goals = self.parse_r_fact(r_fact)
        self.actions = self.get_actions(self.cargos, self.rockets, self.places)
        # actions_dependencies[(action1, action2)] = True if action1 and action2 are dependent, False otherwise
        self.actions_dependencies = self.get_actions_dependencies(self.actions)

    class MOVE(Action):
        def __init__(self, name, args):
            super().__init__(name, args)
            assert len(args) == 3

            self.preconditions.add(Proposition('at', [args[0], args[1]]))
            self.preconditions.add(Proposition('has-fuel', [args[0]]))

            self.positive_effects.add(Proposition('at', [args[0], args[2]]))

            self.negative_effects.add(Proposition('at', [args[0], args[1]]))
        
        def __str__(self):
            return f'{self.name} {self.args[0]} from {self.args[1]} to {self.args[2]}'

    class LOAD(Action):
        def __init__(self, name, args):
            super().__init__(name, args)
            assert len(args) == 3

            self.preconditions.add(Proposition('at', [args[1], args[2]]))
            self.preconditions.add(Proposition('at', [args[0], args[2]]))
            
            self.positive_effects.add(Proposition('in', [args[0], args[1]]))

            self.negative_effects.add(Proposition('at', [args[0], args[2]]))

        def __str__(self):
            return f'{self.name} {self.args[0]} in {self.args[1]} at {self.args[2]}'

    class UNLOAD(Action):
        def __init__(self, name, args):
            super().__init__(name, args)
            assert len(args) == 3

            self.preconditions.add(Proposition('at', [args[1], args[2]]))
            self.preconditions.add(Proposition('in', [args[0], args[1]]))
            
            self.positive_effects.add(Proposition('at', [args[0], args[2]]))

            self.negative_effects.add(Proposition('in', [args[0], args[1]]))

        def __str__(self):
            return f'{self.name} {self.args[0]} from {self.args[1]} at {self.args[2]}'
        
    class NOOP(Action):
        # No-op action that propagates a proposition to the next state
        def __init__(self, name, args):
            super().__init__(name, args)
            assert len(args) == 1

            self.preconditions.add(args[0])

            self.positive_effects.add(args[0])

        def __str__(self):
            return f'{self.name} {self.args[0]}'
        
    def parse_r_fact(self, r_fact):
        pass

    def get_actions(self, cargos, rockets, places):
        actions = []
        for cargo in cargos:
            for rocket in rockets:
                for place in places:
                    actions.append(self.LOAD('LOAD', [cargo, rocket, place]))
                    actions.append(self.UNLOAD('UNLOAD', [cargo, rocket, place]))
        for rocket in rockets:
            for place1 in places:
                for place2 in places:
                    if place1 != place2:
                        actions.append(self.MOVE('MOVE', [rocket, place1, place2]))
        return actions

    def get_producers(self, proposition, actions):
        """
        Returns a list of actions that have the given proposition as a positive effect.
        :param proposition: Proposition object
        :param actions: list of Action objects
        :return: list
        """
        return [action for action in actions if proposition in action.positive_effects]
    
    def are_independent(self, action1, action2):
        for n in action1.negative_effects:
            if n in action2.preconditions or n in action2.positive_effects:
                return False
        for n in action2.negative_effects:
            if n in action1.preconditions or n in action1.positive_effects:
                return False
        return True
    
    def get_actions_dependencies(self, actions):
        """
        Returns a dictionary of dependencies between actions, where the key is a tuple of actions and the value is a boolean
        being True if the actions are dependent and False otherwise.
        :param actions: list of Action objects
        :return: dict
        """
        dependencies = {(action1, action2): (not self.are_independent(action1, action2)) for action1 in actions for action2 in actions}
        return dependencies
    
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
        Returns a list of tuples of actions that are mutex.
        :param actions: list of Action objects
        :param mutex_propositions: list of tuples of Proposition objects
        :return: list
        """
        return [(action1, action2) for action1 in actions for action2 in actions if self.are_mutex_actions(action1, action2, mutex_propositions)]

    def get_mutex_propositions(self, propositions, mutex_actions):
        """
        Returns a list of tuples of propositions that are mutex.
        :param propositions: list of Proposition objects
        :param mutex_actions: list of tuples of Action objects
        :return: list
        """
        return [(prop1, prop2) for prop1 in propositions for prop2 in propositions if self.are_mutex_propositions(prop1, prop2, mutex_actions)]