# examples and tests
# Le Moigne, 2024-06-04
#SB: modified to get PNML file

import csv
from datetime import datetime, timedelta
import random
import unicodedata

from graph import Graphe
import matplotlib.pyplot as plt
import numpy as np
from pattern_discovery import *
from PTPN import ProbabilisticTimePetriNet
from scipy.stats import energy_distance, wasserstein_distance

"""
article_example_database = [
    [1, 2, 3, 4, 5, 6],
    [1, 2, 3, 4, 7, 8],
    [1, 2, 4, 7, 8, 5],
    [1, 2, 3, 7, 8, 4]]
print("Article's example 1 with support 2:", continuous_pattern_discovery(article_example_database, 2))

print("\nTest:")
test = [
    [1, 2, 3, 4, 5, 6],
    [1, 2, 3, 4, 5, 6, 7],
    [1, 2, 4, 3, 5, 6],
    [1, 2, 4, 3, 5, 15],
    [1, 2, 4, 3, 5, 23],
    [5, 6, 7, 8, 9, 10],
    [11, 12, 13, 17, 18, 15]]
all_patterns = pattern_discovery(test)
for i in range(1, 7):
    print(f"Pattern of support {i} (direct):", continuous_pattern_discovery(test, i))
    print(f"Pattern of support {i} (global):", all_patterns[i])

print("\nTest2:")
test2 = [
    [1, 2, 4, 5, 6],
    [2, 3, 4, 5, 6, 7],
    [5, 6, 7, 8, 9]]
sigma = generate_alphabet(test2)
print("Alphabet:", sigma)
list_disc = init_all_supports(test2, sigma)
print("Elementary patterns", list_disc)
all_patterns2 = pattern_discovery(test2)
for i in range(1, 4):
    print(f"Pattern of support {i} (global):", all_patterns2[i])
distributions = {}
for support in range(len(test2), 0, -1):
    print("Support:", support)
    for pattern in all_patterns2[support]:
        print(pattern)
        for i in range(len(pattern)-1):
            print(pattern[i], pattern[i+1], support)
            if pattern[i] not in distributions:
                distributions[pattern[i]] = {pattern[i+1]: support}
                print('add')
            elif pattern[i+1] not in distributions[pattern[i]]:
                distributions[pattern[i]][pattern[i+1]] = support
                print('add')
print(distributions)
"""

# Test on database, mostly from HCU

### Import data
# filename = "PTC"
filename = "lca"
# filename = "PTC_letter"
# filename = "lca"
# filename = "sepsis"

name = {
    "PTC": "HCU database (PTC)",
    "PTC_alt": "HCU database (PTC_alt)",
    "PTC_letter": "HCU database (PTC_letter)",
    "lca": "HCU database (LCA)",
    "sepsis": "sepsis"
}
name = name[filename]
act_row = {"PTC": 4, "PTC_alt": 4, "PTC_letter": 4, "lca": 3, "sepsis": 1}
act_row = act_row[filename]
res_row = {"PTC": 7, "PTC_alt": 7, "PTC_letter": 7, "lca": 6, "sepsis": None}
res_row = res_row[filename]

use_resources = False

lognormal_time = True  # else interval

minimal_support = 1
if filename == "sepsis":
    minimal_support = 20

print(name)


def normalize(s):
    s = s.replace("/", "").replace(" ", "_")
    # remove accents
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


hcu_database = []
sequence = []
time = 0
hcu_timed_database = []
timed_sequence = []
resources = {}
max_activity_time = 100

with open('./database/lca/lca_eng'+".csv") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=";")
    spamreader.__next__()  # skip the header line
    nhc = None
    for row in spamreader:
        if filename == "sepsis":
            time = datetime.fromisoformat(row[2])
        elif lognormal_time:
            time += random.lognormvariate(1, 1)  # time is end
        else:
            time += random.randint(1, max_activity_time)  # time is end
        if (filename != "sepsis" and row[1] and row[act_row]) or (filename == "sepsis" and row[0] and row[0] != nhc):
            nhc = row[0]
            if sequence:
                hcu_database.append(sequence)
                hcu_timed_database.append(timed_sequence)
            sequence = [normalize(row[act_row])]
            timed_sequence = [[normalize(row[act_row]), time]]
        elif row[act_row]:
            sequence.append(normalize(row[act_row]))
            timed_sequence.append([normalize(row[act_row]), time])
        if use_resources and row[act_row]:
            act = normalize(row[act_row])
            res_list = row[res_row].replace(" ", "").split(",")
            if act not in resources:
                resources[act] = {"nb activity": 1}
            else:
                resources[act]["nb activity"] += 1
            for res in res_list:
                if res == "":
                    continue
                if res not in resources[act]:
                    resources[act][res] = 1
                else:
                    resources[act][res] += 1
    if sequence:
        hcu_database.append(sequence)
        hcu_timed_database.append(timed_sequence)
# print(hcu_database, len(hcu_database))

if use_resources:
    act_by_resources = {}
    for act in resources:
        for res in resources[act]:
            if resources[act][res] != resources[act]["nb activity"]:
                print("There is not always the same resources for", act)
                resources[act] = ["Unclear resources"]
                break
        else:
            resources[act] = [x for x in resources[act] if x != "nb activity"]
            for res in resources[act]:
                if res in act_by_resources:
                    act_by_resources[res].append(act)
                else:
                    act_by_resources[res] = [act]
    print(act_by_resources)

### Search patterns
nb_sequence = len(hcu_database)
alphabet = generate_alphabet(hcu_database)
#### Using no modificated pattern discovery
# print("Search pattern with support between", minimal_support, "and", nb_sequence)
# patterns = continuous_pattern_discovery(hcu_database, 1, alphabet)
# patterns = {support: continuous_pattern_discovery(hcu_database, support, alphabet) for support in range(minimal_support, nb_sequence+1)}
# patterns = elementary_pattern_discovery(hcu_database,1)
# print(patterns)
# for support in patterns:
#     print(len(patterns[support]), "patterns with support", support)
#### Using modificated pattern discovery algorithm to be faster
if filename != "sepsis":
    patterns = pattern_discovery(hcu_database, alphabet)
else:
    with open("sepsis_log/99.txt") as f:
        patterns = f.readline()
    patterns = eval(patterns)

### Generate edges (two consecutive events with frequence)
print("Generate edges")
edges = []
added_edges = []
for support in range(nb_sequence, minimal_support-1, -1):
    frequency = support/nb_sequence
    for pattern in patterns[support]:
        for i in range(len(pattern)-1):
            if (pattern[i], pattern[i+1]) not in added_edges:
                added_edges.append((pattern[i], pattern[i+1]))
                edges.append([pattern[i], pattern[i+1], frequency])

### Generate graph (state)
print("Generate graph")
graph = Graphe(name+"graphe")
graph.construireAvecDonnee(alphabet, edges)
graph.tracerGraphe()
graph.affichageHTML()

## Generate PTPN

place_num = 0
resource_places = {}
if use_resources:
    start_transitions = {}
    end_transitions = {}
else:
    transitions = {}
PTPN = ProbabilisticTimePetriNet(name)

for transition_name in alphabet:
    if lognormal_time:
        interval = lognormal_event_duration(hcu_timed_database, transition_name)
    else:
        interval = interval_event_duration(hcu_timed_database, transition_name)
    print(transition_name, interval)
    if use_resources:
        start_transitions[transition_name] = PTPN.add_transition("start "+transition_name, None, None)  # no time
        end_transition = PTPN.add_transition("end "+transition_name, interval, None)  # time interval
        place = PTPN.add_place(transition_name, 0)  # no marking
        PTPN.add_distribution(start_transitions[transition_name], [{place: 1}], [1])  # no weight for the moment, probability 1
        PTPN.add_edge(place, end_transition, 1)
        end_transitions[transition_name] = end_transition
        resources[end_transition] = resources.pop(transition_name)
    else:
        transition = PTPN.add_transition(transition_name, interval, None)  # no time
        transitions[transition_name] = transition


### Plot the distribution of time for the first transition
def lognormal_proba(x, mu, sigma):
    return np.exp(-((np.log(x)-mu)**2)/(2*sigma**2))/(x*sigma*np.sqrt(2*np.pi))


def normal_proba(x, mu, sigma):
    return np.exp(-((x-mu)**2)/(2*sigma**2))/(sigma*np.sqrt(2*np.pi))


def exponential_proba(x, lambd):
    return lambd*np.exp(-x*lambd)


def gamma_proba(x, k, theta, gamma_k=None):
    if gamma_k is None:
        gamma_k = 1
        for i in range(1, 1000):
            gamma_k *= (1+1/i)**k/(1+k/i)
        gamma_k *= 1/k
    return x**(k-1)*np.exp(-x/theta)/(gamma_k*theta**k)


def param(dictionnary):
    txt = "("
    for p in dictionnary:
        if p == "gamma_k":
            continue
        if p == "lambd":
            name = "\\lambda"
        elif p == "k":
            name = "k"
        else:
            name = "\\" + p
        txt += f"${name}$: {dictionnary[p]:.4g}, "
    return txt[:-2]+")"


if lognormal_time:
    print("="*50)
    print("Compute Energy and Wasserstein distance")
    print("Distribution\t| Energy | Wasserstein")
    for transition in PTPN.transitions:
        transition_name = transition.name
        time_function = transition.time_function
        durations = []
        for id_sequence in range(len(hcu_timed_database)):
            sequence = hcu_timed_database[id_sequence]
            for id_event in range(len(sequence)):
                if sequence[id_event][0] == transition_name:
                    if id_event != 0 and sequence[id_event][1] > sequence[id_event-1][1]:
                        durations.append(sequence[id_event][1] - sequence[id_event-1][1])
                    elif id_sequence != 0 and sequence[id_event][1] > hcu_timed_database[id_sequence-1][-1][1]:  # only possible with following sequences
                        durations.append(sequence[id_event][1] - hcu_timed_database[id_sequence-1][-1][1])
        durations = [d.total_seconds() if type(d) is timedelta else d for d in durations]
        x = np.linspace(0.01, max(durations), 100)
        print("-"*50)
        print(f"{transition_name} ({len(durations)} events)")
        plt.hist(durations, bins=10, density=True, range=None)
        lognormal_sample = [random.lognormvariate(**time_function) for _ in range(10000)]
        print("log-normal ", round(energy_distance(durations, lognormal_sample)), round(wasserstein_distance(durations, lognormal_sample)), sep="\t| ")
        plt.plot(x, lognormal_proba(x, **time_function), label="log-normal "+param(time_function))
        normal_parameters = normal_event_duration(hcu_timed_database, transition_name)
        normal_sample = [random.normalvariate(**normal_parameters) for _ in range(10000)]
        print("normal     ", round(energy_distance(durations, normal_sample)), round(wasserstein_distance(durations, normal_sample)), sep="\t| ")
        plt.plot(x, normal_proba(x, **normal_parameters), label="normal "+param(normal_parameters))
        exponential_parameters = exponential_event_duration(hcu_timed_database, transition_name)
        exponential_sample = [random.expovariate(exponential_parameters["lambd"]) for _ in range(10000)]
        print("exponential", round(energy_distance(durations, exponential_sample)), round(wasserstein_distance(durations, exponential_sample)), sep="\t| ")
        plt.plot(x, exponential_proba(x, **exponential_parameters), label="exponential "+param(exponential_parameters))
        gamma_parameters = gamma_event_duration(hcu_timed_database, transition_name)
        gamma_sample = [random.gammavariate(gamma_parameters["k"], gamma_parameters["theta"]) for _ in range(10000)]
        print("gamma      ", round(energy_distance(durations, gamma_sample)), round(wasserstein_distance(durations, gamma_sample)), sep="\t| ")
        plt.plot(x, gamma_proba(x, **gamma_parameters), label="gamma "+param(gamma_parameters))
        plt.title(transition_name)
        plt.legend()
        #ax = plt.gca()
        #ax.set_ylim([0, 3e-5])
        plt.savefig("lognorm_dist/" + transition_name + ".png")
        plt.close("all")
    print("="*50)

distributions = {}
### Pattern discovery
for support in range(nb_sequence, minimal_support-1, -1):
    for pattern in patterns[support]:
        for i in range(len(pattern)-1):
            if use_resources:
                if end_transitions[pattern[i]] not in distributions:
                    distributions[end_transitions[pattern[i]]] = {start_transitions[pattern[i+1]]: support}
                elif start_transitions[pattern[i+1]] not in distributions[end_transitions[pattern[i]]]:
                    distributions[end_transitions[pattern[i]]][start_transitions[pattern[i+1]]] = support
            else:
                if transitions[pattern[i]] not in distributions:
                    distributions[transitions[pattern[i]]] = {transitions[pattern[i+1]]: support}
                elif transitions[pattern[i+1]] not in distributions[transitions[pattern[i]]]:
                    distributions[transitions[pattern[i]]][transitions[pattern[i+1]]] = support
if use_resources:
    for res in act_by_resources:
        resource_place = PTPN.add_place(res, 1)  # 1 mark by default for each ressource
        resource_places[res] = resource_place
        for act in act_by_resources[res]:
            PTPN.add_edge(resource_place, start_transitions[act], 1)
for transition in distributions:
    outcomes = []
    supports = []
    for post_transition in distributions[transition]:
        for potential_place in post_transition.pre:
            if potential_place not in resource_places.values():
                place = potential_place
                break
        else:
            place = PTPN.add_place("P" + str(place_num), 0)  # no marking
            place_num += 1
            PTPN.add_edge(place, post_transition, 1)  # no weight for the moment
        outcome = {place: 1}  # no weight for the moment
        if use_resources:
            for res in resources[transition]:
                outcome[resource_places[res]] = 1
        outcomes.append(outcome)
        supports.append(distributions[transition][post_transition])
    probabilities = [support/sum(supports) for support in supports]
    PTPN.add_distribution(transition, outcomes, probabilities)

start_place = PTPN.add_place("start", 1)  # 1 mark in starting place
end_place = PTPN.add_place("end", 0)  # no marking
for transition in PTPN.transitions:
    if all(place in resource_places.values() for place in transition.pre):
        PTPN.add_edge(start_place, transition, 1)  # no weight for the moment
    if not transition.post:
        outcome = {end_place: 1}
        if use_resources:
            for res in resources[transition]:
                outcome[resource_places[res]] = 1
        PTPN.add_distribution(transition, [outcome], [1])  # no weight for the moment, probability 1
if start_place.post_transitions == []:
    # it is a loop: not playable without information about initial marking
    PTPN.remove_place(start_place)
if end_place.pre_transitions == []:
    # it is a loop: not playable without information about initial marking
    PTPN.remove_place(end_place)

if use_resources:
    PTPN.build_graphviz_png(path=name+"_with_resources")
else:
    with open(name + '.xml', 'w') as f:
        f.write(PTPN.build_xml())
    PTPN.build_graphviz_png(path=name)
    #SB:Write to file PNML
    PTPN.export_pnml(name+".pnml")


if not use_resources:  # with resouces most probable path is by resiurce places #TODO fix it
    try:
        print("Most probable path:")
        shortest_path = PTPN.find_most_probable_pathway(start_place, end_place)
        print(*shortest_path, sep="\n")
        print("-"*20)
        print("Expeted duration of this path:", PTPN.get_pathway_expected_duration(shortest_path))
    except Exception:
        print("Cannot find most probable path")

PTPN.play(max_activity_time*len(PTPN.transitions), {end_place: 1})


# test shortest path
PTPN = ProbabilisticTimePetriNet("shortest_path")
transitions = {}
for transition_name in ["A", "B", "C"]:
    transition = PTPN.add_transition(transition_name, None, None)
    transitions[transition_name] = transition
places = {}
for place_name in ["a", "b", "c", "d"]:
    place = PTPN.add_place(place_name, 0)
    places[place_name] = place
edges = [["a", "A", 1], ["b", "B", 1], ["c", "C", 1]]
for edge in edges:
    PTPN.add_edge(places[edge[0]], transitions[edge[1]], edge[2])
distributions = [
    ["A", [{places["b"]: 1}, {places["c"]: 1}], [0.4, 0.6]],
    ["B", [{places["d"]: 1}, {places["d"]: 1}], [0.1, 0.9]],
    ["C", [{places["d"]: 1}, {places["d"]: 1}], [0.55, 0.45]]
]
for distribution in distributions:
    PTPN.add_distribution(transitions[distribution[0]], distribution[1], distribution[2], fusion_duplicate_outcomes=False)
PTPN.build_graphviz_png()
shortest_path = PTPN.find_most_probable_pathway(places["a"], places["d"], return_only_transitions=False)
print(shortest_path)
print(*list(map(lambda x: x[1], shortest_path.edges)), sep="\n")


# PTPN article fig 1
PTPN = ProbabilisticTimePetriNet("PTPN_article_fig1")
transitions = {"T1": [1, 3], "T2": [0, 4], "T3": [1, 1000], "T4": [0, 1], "T5": [2, 2]}
for transition_name in transitions:
    transition = PTPN.add_transition(transition_name, transitions[transition_name], None)
    transitions[transition_name] = transition
places = {"P1": 1, "P2": 2, "P3": 3, "P4": 1, "P5": 0, "P6": 2, "P7": 1, "P8": 1, "P9": 1}
for place_name in places:
    place = PTPN.add_place(place_name, places[place_name])
    places[place_name] = place
edges = [["P1", "T2", 1], ["P1", "T3", 1], ["P2", "T2", 2], ["P3", "T1", 1], ["P5", "T4", 1], ["P6", "T3", 1], ["P8", "T4", 1], ["P9", "T5", 2]]
for edge in edges:
    PTPN.add_edge(places[edge[0]], transitions[edge[1]], edge[2])
distributions = [
    ["T1", [{places["P4"]: 1}], [1]],
    ["T1", [{places["P1"]: 5}, {}], [0.2, 1-0.2]],
    ["T2", [{places["P1"]: 1, places["P3"]: 3, places["P4"]: 1}, {places["P4"]: 2, places["P5"]: 1, places["P6"]: 1}, {}], [0.3, 0.5, 0.2]],
    ["T2", [{places["P6"]: 1}, {places["P6"]: 2}], [0.6, 1-0.6]],
    ["T3", [{places["P2"]: 7, places["P7"]: 2}], [1]],
    ["T3", [{}, {places["P5"]: 1}], [0.4, 1-0.4]],
    ["T4", [{places["P3"]: 2}], [1]],
    ["T4", [{places["P8"]: 1, places["P9"]: 1}, {places["P9"]: 1}], [0.7, 0.3]]
]
for distribution in distributions:
    PTPN.add_distribution(transitions[distribution[0]], distribution[1], distribution[2])
PTPN.build_graphviz_png()

# Test resources
PTPN = ProbabilisticTimePetriNet("resources")
transitions = {"start activity 1": None, "end activity 1": [10, 20], "start activity 2": None, "end activity 2": [40, 50], "start activity 3": None, "end activity 3": [25, 30]}
for transition_name in transitions:
    transition = PTPN.add_transition(transition_name, transitions[transition_name], None)
    transitions[transition_name] = transition
places = {"start": 1, "activity 1": 0, "activity 2": 0, "activity 3": 0, "waiting resources for 2": 0, "waiting material for 3": 0, "end": 0, "resources": 2, "material": 1}
for place_name in places:
    place = PTPN.add_place(place_name, places[place_name])
    places[place_name] = place
edges = [["start", "start activity 1", 1], ["activity 1", "end activity 1", 1], ["resources", "start activity 1", 1], ["activity 2", "end activity 2", 1], ["activity 3", "end activity 3", 1], ["resources", "start activity 2", 2], ["material", "start activity 3", 1], ["waiting resources for 2", "start activity 2", 1], ["waiting material for 3", "start activity 3", 1]]
for edge in edges:
    PTPN.add_edge(places[edge[0]], transitions[edge[1]], edge[2])
distributions = [
    ["start activity 1", [{places["activity 1"]: 1}], [1]],
    ["end activity 1", [{places["waiting resources for 2"]: 1, places["resources"]: 1}, {places["waiting material for 3"]: 1, places["resources"]: 1}], [0.6, 0.4]],
    ["start activity 2", [{places["activity 2"]: 1}], [1]],
    ["end activity 2", [{places["end"]: 1, places["resources"]: 2}], [1]],
    ["start activity 3", [{places["activity 3"]: 1}], [1]],
    ["end activity 3", [{places["end"]: 1, places["material"]: 1}], [1]]
]
for distribution in distributions:
    PTPN.add_distribution(transitions[distribution[0]], distribution[1], distribution[2])
PTPN.build_graphviz_png()


