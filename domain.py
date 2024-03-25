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