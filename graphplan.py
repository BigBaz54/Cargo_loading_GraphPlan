from domain import RocketDomain


class GraphPlan:
    def __init__(self, r_fact):
        self.rd = RocketDomain(r_fact)
        self.layers = [self.get_initial_layer(self.rd)]
        # a list of k sets (one for each layer) of frozen subsets of goal propositions that lead to failure
        self.nogood =[set()]
        self.trace = ''

    class Layer:
        def __init__(self):
            self.actions = set()
            self.propositions = set()
            self.mutex_actions = set()
            self.mutex_propositions = set()
            self.preconditions_links = set()
            self.positive_effects_links = set()
            self.negative_effects_links = set()

    def get_initial_layer(self, rd):
        """
        Returns the initial layer of the planning graph.
        :param rd: RocketDomain object
        :return: Layer object
        """
        initial_layer = self.Layer()
        initial_layer.propositions = rd.init_propositions
        # No mutex propositions in the initial layer since all propositions are known to be true at the start
        initial_layer.mutex_propositions = set()
        return initial_layer

    def expand(self):
        """
        Adds a layer to the planning graph.
        """
        new_layer = self.Layer()
        new_layer.actions = self.get_next_actions(self.layers[-1].propositions, self.layers[-1].mutex_propositions)
        new_layer.mutex_actions = self.get_mutex_actions(new_layer.actions, self.layers[-1].mutex_propositions)
        new_layer.propositions = self.get_next_propositions(new_layer.actions)
        new_layer.mutex_propositions = self.get_mutex_propositions(new_layer.propositions, new_layer.actions, new_layer.mutex_actions)

        #### Trace ####
        self.trace += f'Expanding the graph, building layer {len(self.layers)}\n'
        self.trace += f'\tLayer {len(self.layers)} actions:\n'
        for action in new_layer.actions:
            self.trace += f'\t\t{action}\n'
        self.trace += f'\tLayer {len(self.layers)} mutex actions:\n'
        for ma1, ma2 in new_layer.mutex_actions:
            self.trace += f'\t\t{ma1} and {ma2}\n'
        self.trace += f'\tLayer {len(self.layers)} propositions:\n'
        for prop in new_layer.propositions:
            self.trace += f'\t\t{prop}\n'
        self.trace += f'\tLayer {len(self.layers)} mutex propositions:\n'
        for mp1, mp2 in new_layer.mutex_propositions:
            self.trace += f'\t\t{mp1} and {mp2}\n'
        self.trace += '\n################################################################################\n\n'
        ##############

        for action in new_layer.actions:
            for prop in action.preconditions:
                if prop in self.layers[-1].propositions:
                    new_layer.preconditions_links.add((prop, action))
            for prop in action.positive_effects:
                if prop in new_layer.propositions:
                    new_layer.positive_effects_links.add((action, prop))
            for prop in action.negative_effects:
                if prop in new_layer.propositions:
                    new_layer.negative_effects_links.add((action, prop))
        self.layers.append(new_layer)
        self.nogood.append(set())

    def extract(self, goal, i):
        """
        Checks if the goal has already been proven to be unreachable, and maintains the nogood sets.
        :param goal: a set of Proposition objects
        :param i: the layer index
        :return: a list of sets of Action objects (a layered plan) or None (if the goal is unreachable)
        """
        self.trace += '################################################################################\n\n'
        self.trace += f'Trying to extract the following goal from layer {i}:\n'
        for prop in goal:
            self.trace += f'\t{prop}\n'
        self.trace += '\n'
        if i == 0:
            # A global plan has been found
            self.trace += '\n#####################################################################################################################\n'
            self.trace += '### The intermediate goal for layer 0 corresponds to the initial preconditions, the built layered plan is valid ! ###\n'
            self.trace += '######################## We can now concatenate the plans for each layer and end the search. ########################\n'
            self.trace += '#####################################################################################################################\n\n'
            return []
        if goal in self.nogood[i]:
            # This goal was already proven to be unreachable
            return None
        layered_plan = self.gp_search(goal, set(), i)
        if layered_plan is not None:
            return layered_plan
        # We found an unreachable goal, add it to the nogood set
        self.nogood[i].add(frozenset(goal))
        return None
        
    def gp_search(self, goal, plan, i, pad=0):
        """
        Builds a plan for the given goal in the given layer.
        :param goal: a set of Proposition objects
        :param plan: a set of Action objects
        :param i: the layer index
        :return: a list of sets of Action objects (a layered plan) or None (if the goal is unreachable)
        """
        if len(goal) == 0:
            # We found a valid plan that achieves the goal for the current layer
            next_preconditions = set()
            for action in plan:
                next_preconditions.update(action.preconditions)
            
            next_layered_plan = self.extract(next_preconditions, i - 1)
            if next_layered_plan is None:
                return None
            
            #### Trace ####
            self.trace += f'The valid intermediate goal that was extracted from layer {i - 1} is:\n'
            for prop in next_preconditions:
                self.trace += f'\t{prop}\n'
            self.trace += f'\nThe valid corresponding plan for layer {i} is:\n'
            for action in plan:
                self.trace += f'\t{action}\n'
            self.trace += '\n################################################################################\n\n'
            ##############
            
            return next_layered_plan + [plan]

        # Or is it a for loop ?
        prop = goal.pop()
        goal.add(prop)
        self.trace += '\t' * pad
        self.trace += f'\t\tLooking for an action that can provide {prop} in layer {i}\n'
        providers = self.get_providers(prop, self.layers[i].actions, self.layers[i].positive_effects_links, plan, self.layers[i].mutex_actions)
        self.trace += '\t' * pad
        self.trace += f'\t\t\tProviders for {prop} in layer {i}:\n'
        for action in providers:
            self.trace += '\t' * pad
            self.trace += f'\t\t\t\t{action}\n'
        if len(providers) == 0:
            self.trace += '\t' * pad
            self.trace += '\t\t\t\tNo provider found, choosing another provider for the previous proposition\n'
            return None
        for action in providers:
            self.trace += '\n'
            self.trace += '\t' * pad
            self.trace += f'\t\t\tTrying to add {action} to the plan\n\n'
            new_plan = plan.copy()
            new_plan.add(action)
            new_goal = goal - action.positive_effects
            layered_plan = self.gp_search(new_goal, new_plan, i, pad + 1)
            if layered_plan is not None:
                return layered_plan
        return None
    
    def graphplan(self):
        i = 0
        goal = self.rd.goal.copy()
        self.trace += '#################################################################################\n'
        self.trace += '### Expanding the planning graph until the goal is included in the last layer ###\n'
        self.trace += '#################################################################################\n\n'
        while self.continue_search(goal) and not self.fixed_point():
            i += 1
            self.expand()
        self.trace += '##############################################################################################\n'
        self.trace += f'### A valid plan might exist from layer {i}, we can try to extract the goal from this layer. ###\n'
        self.trace += '##############################################################################################\n'
        if self.continue_search(goal):
            # We stopped expanding the graph because we reached the fixed point and the goal is not yet achieved
            return None
        nogood_size = len(self.nogood[-1]) if self.fixed_point() else 0

        layered_plan = self.extract(goal, i)
        while layered_plan is None:
            i += 1
            self.expand()
            layered_plan = self.extract(goal, i)
            if layered_plan is None and self.fixed_point():
                if len(self.nogood[-1]) == nogood_size:
                    # We reached the fixed point and the nogood set did not change
                    return None
                nogood_size = len(self.nogood[-1])
        self.trace += f'The extracted goal from layer {i} is {goal}\n\n'
        self.trace += '##########################################################################################\n'
        self.trace += '### This actually is the global goal. The plans for each layer have been concatenated. ###\n'
        self.trace += '##########################################################################################\n\n'
        self.trace += 'We can return the layered plan:\n'
        for layer in layered_plan:
            for action in layer:
                if action.name != 'NOOP':
                    self.trace += f'\t{action}\n'
        return layered_plan

    def fixed_point(self):
        """
        Returns wether or not the graph's last layer is the same as the previous one.
        :return: boolean
        """
        if len(self.layers) < 2:
            return False
        return self.layers[-1].propositions == self.layers[-2].propositions \
            and self.layers[-1].actions == self.layers[-2].actions \
            and self.layers[-1].mutex_propositions == self.layers[-2].mutex_propositions \
            and self.layers[-1].mutex_actions == self.layers[-2].mutex_actions
    
    def continue_search(self, goal):
        """
        Returns wether or not the graph's last layer is a condidate to be the last of the search.
        :param goal: a set of Proposition objects
        :return: boolean
        """
        if not goal.issubset(self.layers[-1].propositions):
            return True
        for prop1 in goal:
            for prop2 in goal:
                if {prop1, prop2} in self.layers[-1].mutex_propositions:
                    return True
        return False

    def get_providers(self, proposition, actions, positive_effects_links, current_plan, mutex_actions):
        """
        Returns a list of Action objects that can provide a given proposition.
        The action must not be mutex with any action in the current plan and must have the given proposition as a positive effect.
        The returned list is sorted to have the No-op actions first.
        :param proposition: Proposition object
        :param actions: set of Action objects
        :param positive_effects_links: set of tuples of Action and Proposition objects
        :param current_plan: set of Action objects
        :param mutex_actions: set of frozen sets of Action objects
        :return: list of Action objects
        """
        providers = set()
        for action in actions:
            if (action, proposition) in positive_effects_links:
                for added_action in current_plan:
                    if {action, added_action} in mutex_actions:
                        break
                else:
                    providers.add(action)
        providers = list(providers)
        providers.sort(key=lambda action: action.name != 'NOOP')
        return providers

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
        if self.rd.actions_dependencies[(action1, action2)]:
            return True
        for prop1 in action1.preconditions:
            for prop2 in action2.preconditions:
                if {prop1, prop2} in mutex_propositions:
                    return True
        return False

    def are_mutex_propositions(self, prop1, prop2, actions, mutex_actions):
        if prop1 == prop2:
            return False
        for action1 in self.get_producers(prop1, actions):
            for action2 in self.get_producers(prop2, actions):
                if {action1, action2} not in mutex_actions:
                    return False
        return True

    def get_mutex_actions(self, actions, mutex_propositions):
        """
        Returns a set of frozen sets of actions that are mutex.
        :param actions: list of Action objects
        :param mutex_propositions: list of tuples of Proposition objects
        :return: list
        """
        return {frozenset([action1, action2]) for action1 in actions for action2 in actions if self.are_mutex_actions(action1, action2, mutex_propositions)}

    def get_mutex_propositions(self, propositions, actions, mutex_actions):
        """
        Returns a set of frozen sets of propositions that are mutex.
        :param propositions: list of Proposition objects
        :param mutex_actions: list of tuples of Action objects
        :return: list
        """
        return {frozenset([prop1, prop2]) for prop1 in propositions for prop2 in propositions if self.are_mutex_propositions(prop1, prop2, actions, mutex_actions)}
    
    def get_next_actions(self, previous_propositions, previous_mutex_propositions):
        """
        Returns a set of Action objects that can be added to the next layer.
        :param previous_propositions: list of Proposition objects
        :param previous_mutex_propositions: list of tuples of Proposition objects
        :return: list
        """
        next_actions = set()
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
        return next_actions
    
    def get_next_propositions(self, current_actions):
        """
        Returns a set of Proposition objects that can be added to the next layer.
        :param actions: set of Action objects
        :return: set
        """
        next_propositions = set()
        for action in current_actions:
            for prop in action.positive_effects:
                next_propositions.add(prop)
        return next_propositions
    
    def write_trace(self):
        with open(f'trace_{self.rd.r_fact.split("/")[-1]}', 'w') as f:
            f.write(self.trace)


if __name__ == "__main__":
    r_fact = 'examples/my_r_fact3.txt'
    gp = GraphPlan(r_fact)
    layered_plan = gp.graphplan()
    gp.write_trace()
    # print('\n\nGoal:')
    # print(gp.rd.goal)
    # print()
    # print('Plan:')
    # print(*layered_plan, sep='\n')
    # print('Plan (without NOOP):')
    # print(*[', '.join([str(action) for action in layer if action.name != 'NOOP']) for layer in layered_plan], sep='\n\n')