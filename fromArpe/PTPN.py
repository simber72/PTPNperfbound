######################################
# PTPN: Probabilistic time Petri net #
#     Author :  Le Moigne            #
# theo.le-moigne@ens-paris-saclay.fr #
#              22/11/2023            #
#         modified 20/06/2024        #
######################################

#Simona Bernardi: 12/7/2024 Added export_pnml method to have a reference schema for the PTPN

from datetime import timedelta
import math
import random

import dijkstar
import graphviz

import string  #to generate random IDs
from collections.abc import Mapping

class ProbabilisticTimePetriNet:
    """
    Probabilistic time Petri net (PTPN)
    Formalist proposed by Y. Emzivat and al. in 2016 (https://hal.science/hal-01590900)
    Use methods to build PTPN, to play PTPN and to export PTPN (xml for PIPE and png)

    name: string
    """

    def __init__(self, name, initial_time=0, unit_time_increment=1):
        self.name = name
        self.transitions = []  # dict or sommeting to get transitions by name ?
        self.places = []  # dict or sommeting to get places by name ?
        self.initial_time = initial_time
        self.time = initial_time
        self.unit_time_increment = unit_time_increment
        # TODO initial marking is a distibution

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def add_transition(self, transition_name, time_function, function_type=None):
        """
        Add a transition to the PTPN with time function and eventually its type
        transition_name: string
        time_function: None, number (integer/float), interval (list/tuple with two growing values),
            function (with parameters time and enable_time)
        function_type: string or None, type of time_function. With None auto-detect but only for
            interval and None
        return: Transition
        """
        if transition_name in map(lambda t: t.name, self.transitions):
            raise Exception("Transition " + str(transition_name) + " already exists")
        transition = Transition(transition_name, time_function, function_type)
        self.transitions.append(transition)
        return transition

    def add_place(self, place_name, initial_marking):
        """
        Add a place to the PTPN with initial_marking
        place_name: string
        intial_marking: integer
        return: Place
        """
        if place_name in map(lambda p: p.name, self.places):
            raise Exception("Place " + str(place_name) + " already exists")
        place = Place(place_name, initial_marking)
        self.places.append(place)
        return place

    def add_distribution(self, transition, outcomes, probablilities, fusion_duplicate_outcomes=True, create_empty_outcome=False, check=True):
        """
        Add a distribution after a transition
        transition: Transition
        outcomes: list of dict of place with weight (marking)
        probabilities: list of probablilities for outcomes (same size as outcomes)
        fusion_duplicate_outcomes: boolean (default True)
        create_empty_outcome: boolena (default False)
        check: boolean (default True), check respect of probablilities rules
        return: Distribution
        """
        distribution = Distribution(outcomes, probablilities, fusion_duplicate_outcomes, create_empty_outcome, check)
        transition.add_post_distibution(distribution)
        for outcome in outcomes:
            for place in outcome:
                place.add_pre_transition(transition)
        return distribution

    def add_edge(self, place, transition, weight):
        """
        Add an edge form a place to a transition with a weight
        place: Place
        transition: Transition
        weight: integer
        """
        if transition in place.post_transitions or place in transition.pre:
            raise Exception("Place " + place.name + " is already before transition" + transition.name)
        transition.add_pre_place(place, weight)
        place.add_post_transition(transition)

    def remove_place(self, place):
        """
        Remove a place
        place: Place
        """
        if place not in self.places:
            raise Exception("Place " + str(place) + " does not exists")
        self.places.remove(place)
        for transition in place.pre_transitions:
            for distribution in transition.post:
                for outcome in distribution.outcomes:
                    if place in outcome:
                        outcome.remove(place)
                        # TODO check if distribution/outcome is empty/duplicate ?
        for transition in place.post_transitions:
            transition.pre.remove(place)

    def enabled_transitions(self):
        """
        Select the enabled transition
        return: filter of Transition
        """
        return filter(lambda transition: transition.is_enabled(), self.transitions)

    def firable_transitions(self):
        """
        Select the firable transition
        return: filter of Transition
        """
        return filter(lambda transition: transition.is_firable(self.time), self.transitions)

    def fire_transition(self, transition):
        """
        Fire a given transition
        transition: Transition
        """
        transition.fire(self.time)

    def fire(self):
        """
        Fire a random transition in the firable transitions
        return: Transition, the fired transition
        """
        transition = random.choice(list(self.firable_transitions()))
        transition.fire(self.time)
        return transition

    def find_most_probable_pathway(self, start, end, return_only_transitions=True):
        """
        Find the most probable pathway attribut of the PTPN between start and end
        It use sortest path algorithm apply to probabilities.
        start: Place
        end: Place
        return_only_transitions: boolean which select the type of output
        return: list of Transition (or dijkstar.PathInfo if return_only_transitions is False)
        """
        graph = dijkstar.Graph()
        for transition in self.transitions:
            for distribution in transition.post:
                for outcome, probability in zip(distribution.outcomes, distribution.probabilities):
                    for post_place in outcome:
                        for pre_place in transition.pre:
                            graph.add_edge(pre_place, post_place, (-math.log10(probability), transition))
        shortest_path = dijkstar.find_path(graph, start, end, cost_func=lambda u, v, x, y: x[0])
        return list(map(lambda x: x[1], shortest_path.edges)) if return_only_transitions else shortest_path

    def get_pathway_expected_duration(self, pathway):
        """
        Return the expected value of the duration of a pathway
        pathway: list of Transition
        """
        total_expected_duration = 0
        for transition in pathway:
            duration = transition.get_expected_duration()
            if duration is not None:
                total_expected_duration += duration
        return total_expected_duration

    def build_xml(self):
        """
        Build the XML of the PTPN (with initial_marking)
        Loss in the format: probabilities and weight are collapsed
        return: string
        """
        string = '<?xml version="1.0" encoding="iso-8859-1"?> \n <pnml> \n <net id="Net-One" \
            type="P/T net"> \n <token id="Default" enabled="true" red="0" green="0" blue="0"/>'
        positionx = 0
        for place in self.places:
            string += '<place id="{0}">\n <graphics>\n <position x="{1}" y="150.0"/>\n </graphics>\n <name>\n <value>{0}</value>\n \
            </name><initialMarking>\n <value>Default,{2}</value>\n </initialMarking>\n </place>\n'.format(place.name, positionx, place.initial_marking)
            positionx += 50
        positionx = 0
        for transition in self.transitions:
            string += '<transition id="{0}">\n <graphics>\n <position x="{1}" y="240.0"/>\n </graphics>\n <name>\n \
                <value>{0}</value></name>\n </transition>\n'.format(transition.name, positionx)
            positionx += 50
            for place in transition.pre:
                if place in self.places:
                    string += '<arc id="{0} to {1}" source="{0}" target="{1}">\n'.format(place.name, transition.name)
                    string += '<graphics/>\n <inscription>\n <value>Default,{0}</value>\n <graphics/>\n </inscription>\n \
                        <tagged>\n <value>false</value>\n </tagged>\n '.format(transition.pre[place])  # weight
                    string += '<type value="normal"/>\n </arc>\n '
            for distribution in transition.post:
                # TODO find a way to modelise distribution
                for outcome, probablility in zip(distribution.outcomes, distribution.probabilities):
                    for place in outcome:
                        if place in self.places:
                            string += '<arc id="{0} to {1} with prob {2}" source="{0}" target="{1}">\n'.format(transition.name, place.name, probablility)
                            string += '<graphics/>\n <inscription>\n <value>Default,{0};{1}</value>\n <graphics/>\n \
                                </inscription>\n <tagged>\n <value>false</value>\n </tagged>\n '.format(outcome[place], probablility)
                            # TODO verify how to write on an arc
                            string += '<type value="normal"/>\n </arc>\n '
        string += '</net>\n </pnml>\n  '
        return string


    ## Source code: https://www.geeksforgeeks.org/generating-random-ids-python/
    def generate_custom_id(self):
        LENGTH = 8
        cid = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(LENGTH)])
        return cid

    def export_pnml(self,filename):
        """
        Export the PTPN model to (extended) pnml of the PTPN 
        filename: filename.pnml is created
        """
        #Heading
        ptpn = '<?xml version="1.0" encoding="iso-8859-1"?>\n'
        netid = self.generate_custom_id()
        pageid = self.generate_custom_id()
        ptpn  = '<pnml xmlns="http://www.pnml.org/version-2009/grammar/pnml">\n'
        ptpn += ' <net id="{0}" type="http://www.pnml.org/version-2009/grammar/ptnet">\n'.format(netid)
        ptpn += '  <page id="{0}">\n'.format(pageid)

        #Places
        positionx = 0
        place_ids = dict()
        for place in self.places:
            pid = self.generate_custom_id()
            place_ids.update({place.name: pid}) 
            ptpn += '    <place id="{0}">\n'.format(pid)
            ptpn += '     <graphics>\n'
            ptpn += '      <position x="{0}" y="150.0"/>\n'.format(positionx)
            ptpn += '     </graphics>\n'
            ptpn += '     <name>\n'
            ptpn += '      <text>{0}</text>\n'.format(place.name)
            ptpn += '     </name>\n'
            ptpn += '     <initialMarking>\n'
            ptpn += '      <text>{0}</text>\n'.format(place.initial_marking)
            ptpn += '     </initialMarking>\n' 
            ptpn += '    </place>\n'
            positionx += 50
        #Transitions
        positionx = 0
        trans_ids = dict()
        for transition in self.transitions:
            tid = self.generate_custom_id()
            trans_ids.update({transition.name: tid}) 
            #time_spec = transition.display_time()
            time_func_type = transition.time_function_type
            parameters = transition.time_function
            ptpn += '    <transition id="{0}">\n'.format(tid)
            ptpn += '     <graphics>\n'
            ptpn += '      <position x="{0}" y="240.0"/>\n'.format(positionx)
            ptpn += '     </graphics>\n'
            ptpn += '     <name>\n'
            ptpn += '      <text>{0}</text>\n'.format(transition.name)
            ptpn += '     </name>\n'
            ptpn += '     <toolspecific tool="PTPN" version="0.1">\n'
            ptpn += '      <time_function type="{0}">\n'.format(time_func_type)
            if isinstance(parameters,list):
                ptpn += '       <param name="min">\n'
                ptpn += '         <text>{0}</text>\n'.format(parameters[0])
                ptpn += '       </param>\n'
                ptpn += '       <param name="max">\n'
                ptpn += '         <text>{0}</text>\n'.format(parameters[1])
                ptpn += '       </param>\n'
            if isinstance(parameters,Mapping):
                for param, value in zip(parameters.keys(), parameters.values()):
                    ptpn += '       <param name="{0}">\n'.format(param)
                    ptpn += '         <text>{0}</text>\n'.format(value)
                    ptpn += '       </param>\n'
            ptpn += '      </time_function>\n'
            ptpn += '     </toolspecific>\n'
            ptpn += '    </transition>\n'
            positionx += 50
            #Input arcs
            for place in transition.pre:
                if place in self.places:
                    aid = self.generate_custom_id()
                    ptpn += '    <arc id="{0}" source="{1}" target="{2}">\n'.format(aid, place_ids[place.name], trans_ids[transition.name])
                    ptpn += '     <inscription>\n'
                    ptpn += '      <text>{0}</text>\n'.format(transition.pre[place])  # arc weight
                    ptpn += '     </inscription>\n'
                    ptpn += '    </arc>\n'
            #Output arcs
            did = 0 #distribution identifier (constant - transition context)
            for distribution in transition.post:   
                for outcome, probability in zip(distribution.outcomes, distribution.probabilities):
                    for place in outcome:
                        if place in self.places:
                            aid = self.generate_custom_id()
                            ptpn += '    <arc id="{0}" source="{1}" target="{2}">\n'.format(aid, trans_ids[transition.name], place_ids[place.name])
                            ptpn += '     <inscription>\n'
                            ptpn += '       <text>{0}</text>\n'.format(outcome[place])
                            ptpn += '     </inscription>\n'
                            ptpn += '     <toolspecific tool="PTPN" version="0.1">\n'
                            ptpn += '      <distribution id="{0}">\n'.format(did)
                            ptpn += '        <probability>\n'
                            ptpn += '          <text>{0}</text>\n'.format(probability)
                            ptpn += '        </probability>\n'
                            ptpn += '      </distribution>\n'
                            ptpn += '     </toolspecific>\n'
                            ptpn += '    </arc>\n'
                did += 1

        #Closings
        ptpn += '  </page>\n'
        ptpn += ' </net>\n'
        ptpn += '</pnml>'
        #Write to file
        f = open(filename, "w")
        f.write(ptpn)
        f.close()


    def build_graphviz_png(self, path=None):
        """
        Draw the PTPN (with the current marking) with graphviz in a PNG file
        """
        # color to identifi outcome from the same distribution
        # /!\ more than 5 distributions on the same transition cause color reuse and could cause graphviz issue with sametail
        color = ["red", "blue", "green", "orange", "purple"]
        if path is None:
            path = self.name

        dot = graphviz.Digraph(comment=self.name, format='png')
        dot.attr(rankdir='TB')  # vertical
        for place in self.places:
            dot.node(place.name, label="•"*place.marking, xlabel=place.name)
            # use marking and not initial_marking so a played PTPN could be represented
        for transition in self.transitions:
            dot.node(transition.name, shape='rect', label="", height='0.05', width='0.5', xlabel=transition.name+"\n"+transition.display_time())
            for place in transition.pre:
                if place in self.places:
                    dot.edge(place.name, transition.name, label=str(transition.pre[place]))
            dist_num = 0  # TODO put in distribution ?
            for distribution in transition.post:
                dist_name = transition.name + " dist " + str(dist_num)
                outcome_num = 0
                for outcome, probablility in zip(distribution.outcomes, distribution.probabilities):
                    outcome_name = dist_name + " outcome " + str(outcome_num)
                    dot.node(outcome_name, shape='point', label="")
                    dot.edge(
                        transition.name, outcome_name, label=str(round(probablility, 2)),
                        style='dashed', sametail=dist_name, color=color[dist_num % len(color)])
                    for place in outcome:
                        if place in self.places:
                            dot.edge(outcome_name, place.name, label=str(outcome[place]))
                    outcome_num += 1
                dist_num += 1
        dot.render(filename=path)  # TODO problems with label position
        return  # TODO return instead of create file ?

    def current_marking(self, show_null=True):
        for place in self.places:
            if place.marking > 0 or show_null:
                print('Place ', place, ': ', place.marking, 'token')

    def reset(self):
        """
        Reset the PTPN
        """
        for place in self.places:
            place.marking = place.initial_marking
            place.analysis = {
                "arrival_sum": 0,
                "departure_sum": 0,
                "presence_time": [],
                "presence_time_start": [self.initial_time]*place.initial_marking,
                "number_mark": []
            }
        self.time = self.initial_time
        for transition in self.transitions:
            transition.check_enable(self.time)
            transition.analysis = {"fire_sum": 0, "waiting_time": [], "enabled_time": 0}

    def increment_time(self, increment=None):  # TODO incremente to next change
        """
        Increment the time
        If no increment is given, use a unit increment
        increment: duration (int, timedelta...)
        """
        if not increment:
            increment = self.unit_time_increment
        self.time += increment
        for place in self.places:
            place.analysis["number_mark"].append(place.marking)
        for transition in self.enabled_transitions():
            transition.analysis["enabled_time"] += increment

    def is_minimal_marking(self, minimal_marking):
        """
        Checks if the current marking is greater than the minimal marking
        minimal_marking: dict of place with there minimal marking
        return: boolean
        """
        for place in minimal_marking:
            if place.marking < minimal_marking[place]:
                return False
        return True

    def display_analysis(self):
        """
        Display the analysis of the PTPN since the last reset
        """
        def avg(numbers):
            """
            Calculate the average of a list
            Return None for an empty list
            numbers: list of numbers
            """
            if not numbers:
                return None
            else:
                return sum(numbers)/len(numbers)

        print("Global analysis:")
        print("Total time:", self.time)
        print("-"*20)
        print("Places analysis:")
        for place in self.places:
            print(place)
            print("\tArrival sum:", place.analysis["arrival_sum"])
            print("\tThroughput sum:", place.analysis["departure_sum"])
            print("\tWaiting time average (by token):", avg(place.analysis["presence_time"]))
            print("\tQueue length average (by time unit):", avg(place.analysis["number_mark"]))
        print("-"*20)
        print("Transitions analysis:")
        for transition in self.transitions:
            print(transition)
            print("\tService sum:", transition.analysis["fire_sum"])
            print("\tWaiting time average (by fire):", avg(transition.analysis["waiting_time"]))
            print("\tEnabled time:", transition.analysis["enabled_time"])

    def play(self, max_time, final_marking, analysis=True):
        """
        Play the PTPN until the end condition
        max_time: integer
        final_marking: dict of place with a minimal marking to reach
        analysis: boolean (default=True) which enable the display of analysis at the end
        """
        self.reset()
        print("="*20)
        print("Play", self.name)
        print("-"*20)
        print("Initial marking:")
        self.current_marking(show_null=True)
        print("="*20)
        while self.time <= max_time and not self.is_minimal_marking(final_marking):
            print("Time =", self.time)
            firable_transitions = list(self.firable_transitions())
            while firable_transitions:
                print("-"*20)
                print("Fire", self.fire())
                self.current_marking(show_null=False)
                firable_transitions = list(self.firable_transitions())
            self.increment_time()
            for transition in self.transitions:
                transition.check_enable(self.time)
            print("="*20)
        print("Final time:", self.time)
        print("Final marking:")
        self.current_marking(show_null=True)
        print("="*20)
        if analysis:
            self.display_analysis()
            print("="*20)
        self.reset()


class Transition:
    """
    Transition of probabilistic time Petri net

    transition_name: string
    time_function: None, number (integer/float), interval (list/tuple with two growing values),
        dict (for probablilites distribution), function (with parameters time and enable_time)
    function_type: string or None, type of time_function. With None, it try to auto-detect but only
        for interval and None
    """

    def __init__(self, transition_name, time_function, function_type=None):
        self.name = str(transition_name)
        self.pre = {}  # dict with place in key and weight (marking) in value
        self.post = []  # list of distribution
        self.time_function_type = self.function_type(function_type, time_function)  # None, "time", "interval", "function"
        self.time_function = time_function  # None, int/float, list/tuple with 2 int/floats, function
        self.fire_time = None
        self.analysis = {"fire_sum": 0, "waiting_time": [], "enabled_time": 0}

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def display_time(self):
        """
        Display time function of the transition
        return: string
        """
        def param(dictionnary):
            """
            Return a human lisible version of the parameter dictionnary
            """
            txt = " ("
            for p in dictionnary:
                if p == "gamma_k":
                    continue
                if p == "lambda":
                    name = "lambda"
                else:
                    name = p
                txt += f"{name}: {dictionnary[p]:.4g}, "
            return txt[:-2]+")"

        if self.time_function_type in ["lognormal", "normal", "exponential", "gamma"]:
            return str(self.time_function_type) + param(self.time_function)
        return str(self.time_function)

    def function_type(self, function_type, time_function):
        """
        Evaluate the type of the time function
        function_type: None or string, use the given value instead of evaluate it
        time_function: object to evaluate
        return: None, or string ("interval", "lognormal")
        """
        if function_type is not None:
            return function_type
        if time_function is None:
            return None
        if hasattr(time_function, '__iter__') and sorted(list(time_function)) == ['mu', 'sigma']:
            return "lognormal"  # be careful, it could be a normal distribution
        else:  # we limit to interval
            try:
                if not time_function[0] <= time_function[1]:
                    raise Exception("time_function is not an interval for transition" + self.name)
            except Exception:
                raise Exception("time_function is not an interval for transition" + self.name)
            return "interval"
        # TODO check other types

    def is_enabled(self):
        """
        Check is the transition is enable:
        It need to have more mark than weight in each place before the transition
        return: boolean
        """
        for place in self.pre:
            if place.marking < self.pre[place]:
                return False  # not enough tokens
        return True  # good to go

    def get_fire_duration(self):
        """
        Return the duration before fire transition
        return: time (integer or timedelta)
        """
        if self.time_function_type is None:
            return None
        if self.time_function_type == "time":
            return self.time_function
        if self.time_function_type == "interval":
            return random.uniform(self.time_function[0], self.time_function[1])
        if self.time_function_type == "lognormal":
            return random.lognormvariate(**self.time_function)  # unpack mu and sigma
        if self.time_function_type == "normal":
            return random.normalvariate(**self.time_function)  # unpack mu and sigma
        if self.time_function_type == "exponential":
            return random.expovariate(self.time_function["lambda"])
        if self.time_function_type == "gamma":
            return random.gammavariate(self.time_function["k"], self.time_function["theta"])
        if self.time_function_type == "function":
            return self.time_function()  # TODO args (self, time ?)
        raise Exception("cannot determine fire duration for transition" + self.name)

    def check_enable(self, time):
        """
        Upade the enable state of the transtion
        time: integer
        """
        is_enabled = self.is_enabled()
        if not is_enabled:
            self.fire_time = None
        elif self.time_function_type is not None and self.fire_time is None:
            fire_duration = self.get_fire_duration()
            if fire_duration is not None:
                if type(time) is timedelta and type(fire_duration) is not timedelta:
                    fire_duration = timedelta(seconds=fire_duration)
                self.fire_time = time + fire_duration
                self.analysis["waiting_time"].append(fire_duration)
            else:
                self.fire_time = time

    def is_firable(self, time):
        """
        Check if the transition is firable:
        It needs to be enabled and be at the right time
        time: integer
        return: boolean
        """
        # TODO it's not analylising if the transition is firable but if it's probablity now that it sould be fire
        # For infinite distribution, we can add a parameter to know if the probability is greater than a minimum
        # Add a function that check if we should fire according to fire_time = enable_time + waiting_time
        if not self.is_enabled():
            return False
        if self.time_function_type is None:
            # firable if enable (#TODO priority)
            return True
        if time >= self.fire_time:
            return True
        return False

    def fire(self, time):
        """
        Fire the transition
        time: integer
        Tokens are first removed then added, so if a token is removed and added to the same transition, this transition time is reinitialized
        """
        self.analysis["fire_sum"] += 1
        for place in self.pre:
            place.remove_token(self.pre[place], time)
            place.analysis["departure_sum"] += 1
        for distibution in self.post:
            outcome = distibution.choose_outcome()
            for place in outcome:
                place.add_token(outcome[place], time)
                place.analysis["arrival_sum"] += 1

    def add_pre_place(self, place, weight):
        """
        Add a place to the dict of place and weight before the transition
        place: Place
        weight: integer
        """
        self.pre[place] = weight

    def add_post_distibution(self, distribution):
        """
        Add a distribution to the list of distributions after the transition
        distribution: Distribution
        """
        self.post.append(distribution)

    def get_expected_duration(self):
        """
        Return the expected value of the duration according to the time function
        """
        if self.time_function_type is None:
            return None
        if self.time_function_type == "time":
            return self.time_function
        if self.time_function_type == "interval":
            return (self.time_function[1] - self.time_function[1])/2
        if self.time_function_type == "lognormal":
            return math.exp(self.time_function["mu"] + self.time_function["sigma"]**2/2)
        if self.time_function_type == "normal":
            return self.time_function["mu"]
        if self.time_function_type == "exponential":
            return 1/self.time_function["lambda"]
        if self.time_function_type == "gamma":
            return self.time_function["k"]*self.time_function["theta"]
        if self.time_function_type == "function":
            raise Exception("cannot determine expected duration for transition " + self.name + " with function")
        raise Exception("cannot determine expected duration for transition " + self.name)


class Place:
    """
    Place of probabilistic time Petri net

    place_name: string
    initial_marking: integer
    """

    def __init__(self, place_name, initial_marking):
        self.name = str(place_name)
        self.marking = int(initial_marking)
        self.initial_marking = int(initial_marking)
        self.pre_transitions = []
        self.post_transitions = []
        self.analysis = {}

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def add_token(self, number, time):
        """
        Add a number of tokens to the place and update state of transitions
        number: integer
        time: integer
        """
        self.marking += number
        for transition in self.post_transitions:
            transition.check_enable(time)
        self.analysis["presence_time_start"].append(time)

    def remove_token(self, number, time):
        """
        Remove a number of tokens from the place and update state of transitions
        Raise error if the is not enought tokens
        number: integer
        time: integer
        """
        if self.marking < number:
            raise Exception("Impossible : No enought token in place " + str(self))
        else:
            self.marking -= number
            for transition in self.post_transitions:
                transition.check_enable(time)
            self.analysis["presence_time"].append(time - self.analysis["presence_time_start"].pop(0))

    def add_pre_transition(self, transition):
        """
        Add a transition to the list of transition before the place
        transition: Transition
        """
        if transition not in self.pre_transitions:
            self.pre_transitions.append(transition)

    def add_post_transition(self, transition):
        """
        Add a transition to the list of transition after the place
        transition: Transition
        """
        self.post_transitions.append(transition)


class Distribution:
    """
    Distribution is a group of probabilist outcome. When fired only one outcome append.

    outcomes: list of dict of place with weight (marking)
    probabilities: list of probablilities for outcomes (same size as outcomes)
    fusion_duplicate_outcomes: boolean (default True)
    create_empty_outcome: boolena (default False)
    check: boolean (default True), check respect of probablilities rules
    """

    def __init__(self, outcomes, probablilities, fusion_duplicate_outcomes=True, create_empty_outcome=False, check=True):
        self.nb_outcomes = len(outcomes)
        self.outcomes = outcomes  # list of outcome: dict of place with weight (marking)
        self.probabilities = probablilities  # probability of each outome (sum is 1)
        if fusion_duplicate_outcomes:
            self.fusion_duplicate_outcomes()
        if create_empty_outcome:
            self.create_empty_outcome()
        if check:
            self.check()

    def __repr__(self):
        return "Distibution with " + str(self.nb_outcomes) + " outcomes"

    def __str__(self):
        return "Distibution with " + str(self.nb_outcomes) + " outcomes"

    def choose_outcome(self):
        """
        Choose an outcome with a probability trial (when transition is fired)
        return: outcome, dict of place with weight
        """
        total_prob = 0
        value = random.random()
        for i in range(self.nb_outcomes):
            total_prob += self.probabilities[i]
            if value < total_prob:
                return self.outcomes[i]

    def most_probable_outcome(self):
        """
        Select the most probable outcome
        return: outcome, dict of place with weight
        """
        max_prob = 0
        max_outcome = []
        for i in range(self.nb_outcomes):
            if self.probabilities[i] > max_prob:
                max_prob = self.probabilities[i]
                max_outcome = self.outcomes[i]
        return max_outcome

    def get_probablility(self, outcome):
        """
        Return probability of an outcome in the distribution
        Raise exception if the outcome does not exist
        Be careful, if outcomes are duplicates, only return probability of the first one
        outcome: dict of place with weight
        return: float in [0,1], probability of the outcome
        """
        return self.probabilities[self.outcomes.index(outcome)]

    def fusion_duplicate_outcomes(self):
        """
        Fusion duplicate outcomes and sum their probabilities
        """
        duplicate = []
        for i in range(self.nb_outcomes):
            for j in range(i):
                if self.outcomes[i] == self.outcomes[j]:
                    self.probabilities[j] += self.probabilities[i]
                    duplicate.append(i)
                    print("Fusion duplicate outcomes")
        for i in duplicate:
            self.outcomes.pop(i)
            self.probabilities.pop(i)
        self.nb_outcomes -= len(duplicate)

    def create_empty_outcome(self):
        """
        Create an empty outcome with probabilities completion to 1
        Raise exception if probablilities sum is greater than 1
        """
        probability = 1-sum(self.probabilities)
        if probability < 0:
            raise Exception("Sum of probablilities must lower than 1 to complete distribution")
        if probability > 0:
            print("Add empty outcome to distribution")
            self.outcomes.append({})
            self.probabilities.append(probability)

    def check(self):
        """
        Check distribution properties: probabilities sum and values, list size
        """
        if sum(self.probabilities) < 1-1e14 or sum(self.probabilities) > 1+1e14:
            raise Exception(f"Sum of probablilities must be 1 in distibution. Here: {sum(self.probabilities)}")
        for probability in self.probabilities:
            if not 0 <= probability <= 1:
                raise Exception(f"Probability must be in [0,1] interval. Here: {probability}")
        if self.nb_outcomes != len(self.outcomes) or self.nb_outcomes != len(self.probabilities):
            raise Exception("Distibution needs the same number of outcomes and probablilities")
#        for i in range(self.nb_outcomes):
#            for j in range(i):
#                if self.outcomes(i) == self.outcomes(j):
#                    raise Exception('Outcomes are duplicate in distibution')
