class Proposition:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __str__(self):
        return f'{self.args[0]} {self.name}{" " + self.args[1] if len(self.args) > 1 else ""}'
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        return self.name == other.name and self.args == other.args
    
    def __hash__(self):
        return hash(self.name) + hash(tuple(self.args))

class Action:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.preconditions = set()
        self.positive_effects = set()
        self.negative_effects = set()

    def __eq__(self, other):
        return self.name == other.name and self.args == other.args
    
    def __hash__(self):
        return hash(self.name) + hash(tuple(self.args))
    
    def __repr__(self):
        return self.__str__()

class RocketDomain:
    def __init__(self, r_fact):
        self.cargos, self.rockets, self.places, self.init_propositions, self.goal = self.parse_r_fact(r_fact)
        self.propositions = self.get_propositions(self.cargos, self.rockets, self.places)
        self.actions = self.get_actions(self.cargos, self.rockets, self.places, self.propositions)
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
            self.negative_effects.add(Proposition('has-fuel', [args[0]]))
        
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
        with open(r_fact, 'r') as f:
            lines = f.readlines()
        cargos = []
        rockets = []
        places = []
        init_propositions = set()
        goal = set()

        i = 1
        while lines[i] != '\n':
            l = lines[i].replace('(', '').replace(')', '').strip().split()
            if l[1] == 'CARGO':
                cargos.append(l[0])
            elif l[1] == 'ROCKET':
                rockets.append(l[0])
            elif l[1] == 'PLACE':
                places.append(l[0])
            i += 1
        i += 2
        while lines[i] != '\n':
            l = lines[i].replace('(', '').replace(')', '').strip().split()
            init_propositions.add(Proposition(l[0], l[1:]))
            i += 1
        i += 2
        while lines[i] != '\n':
            l = lines[i].replace('(', '').replace(')', '').strip().split()
            goal.add(Proposition(l[0], l[1:]))
            i += 1
        
        return cargos, rockets, places, init_propositions, goal
    
    def get_propositions(self, cargos, rockets, places):
        propositions = set()
        for cargo in cargos:
            for rocket in rockets:
                propositions.add(Proposition('in', [cargo, rocket]))
            for place in places:
                propositions.add(Proposition('at', [cargo, place]))
        for rocket in rockets:
            propositions.add(Proposition('has-fuel', [rocket]))
            for place in places:
                propositions.add(Proposition('at', [rocket, place]))
        return propositions

    def get_actions(self, cargos, rockets, places, propositions):
        actions = set()
        for prop in propositions:
            actions.add(self.NOOP('NOOP', [prop]))
        for cargo in cargos:
            for rocket in rockets:
                for place in places:
                    actions.add(self.LOAD('LOAD', [cargo, rocket, place]))
                    actions.add(self.UNLOAD('UNLOAD', [cargo, rocket, place]))
        for rocket in rockets:
            for place1 in places:
                for place2 in places:
                    if place1 != place2:
                        actions.add(self.MOVE('MOVE', [rocket, place1, place2]))
        return actions
    
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


if __name__ == '__main__':
    # Test pasring
    r_fact = 'examples/r_fact2.txt'
    domain = RocketDomain(r_fact)
    print(f'Cargos:\n{domain.cargos}\n')
    print(f'Rockets:\n{domain.rockets}\n')
    print(f'Places:\n{domain.places}\n')
    print(f'Initial propositions:\n{domain.init_propositions}\n')
    print(f'Goals:\n{domain.goal}\n')
    # print(f'\nActions:\n{domain.actions}\n\n')
    print(f'Number of actions (excluding No-op): {len(domain.actions)}\n')
    print(f'Dependency table size: {len(domain.actions_dependencies)}')

    # Test sets of actions and propositions and operations on them
    domain = RocketDomain('examples/r_fact2.txt')
    prop1 = Proposition('at', ['c1', 'r1'])
    prop2 = Proposition('at', ['c2', 'r2'])
    prop3 = Proposition('at', ['c1', 'r2'])
    prop4 = Proposition('in', ['c1', 'r1'])

    props = {prop1, prop2, prop3, prop4}

    print(Proposition('at', ['c1', 'r1']) in props)
    props_copy = props.copy()
    props_copy.update({Proposition('at', ['c1', 'r1'])})
    print(props_copy == props)
    print(props - {Proposition('at', ['c1', 'r1'])})
