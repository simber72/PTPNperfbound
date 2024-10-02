# example with CASA database
# -> D. Cook, A. Crandall, B. Thomas, and N. Krishnan. CASAS: A smart home in a box. IEEE Computer, 2013.
# -> http://eecs.wsu.edu/~cook/pubs/computer12.pdf
# Le Moigne, 2024-06-20

# Simona Bernardi: 
# modified version of the original script from arpe-identification-main
# https://gitlab.crans.org/bleizi/arpe-identification/
# + export_pnml: to generate a net with the input format of the PTPNperfbound tool

import csv
from datetime import datetime, timedelta
import random

import matplotlib.pyplot as plt
import numpy as np
from pattern_discovery import *
from PTPN import ProbabilisticTimePetriNet
from scipy.stats import energy_distance, wasserstein_distance

# Test on database from CASAS

### Import data
filename = "assessmentdata"

name = "assessmentdata (CASAS 21)"

minimal_support = 1

print(name)

transition_names = [
    "",  # empty because no event with number 0
    "Sweep the kitchen and dust the living room",
    "Obtain a set of medicines and a weekly medicine dispenser, fill as per directions",
    "Write a birthday card, enclose a check and address an envelope",
    "Find the appropriate DVD and watch the corresponding news clip",
    "Obtain a watering can and water all plants in the living space",
    "Answer the phone and respond to questions pertaining to the video from task 4",
    "Prepare a cup of soup using the microwave",
    "Pick a complete outfit for an interview from a selection of clothing",
    "Check the wattage of a desk lamp and replace the bulb",
    "Wash hands with soap at the kitchen sink",
    "Wash and dry all kitchen countertop surfaces",
    "Place a phone call to a recording and write down the recipe heard",
    "Sort and fold a basketful of clothing containing men's, women's and children's articles",
    "Prepare a bowl of oatmeal on the stovetop from the directions given in task 12",
    "Sort and file a small collection of billing statements",
    "Setup hands for a card game, answer the phone and describe the rules of the game",
    "Examine a bus schedule; plan a trip including length of time and when to leave",
    "Microwave a comfort heat-pack for the bus ride",
    "Select a magazine to read during the trip",
    "Count out appropriate change for bus fare",
    "Take a dose of an anti-motion sickness medication",
    "Find a recipe book, gather ingredients cited as necessary for a picnic meal",
    "Obtain a picnic basket from the hall closet and fill with all items for the trip",
    "Take the filled picnic basket toward the apartment exit, as though leaving as planned"
]

casas_database = []
casas_timed_database = []
resources = {}

for number in range(1, 401):
    # print(number)
    sequence, timed_sequence = [], []
    with open("./database/"+filename+f"/data/{number:03d}.txt") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=" ")
        firstline = spamreader.__next__()
        if firstline[0] == "No" or firstline[0] == "NO":
            continue
        time = datetime.fromisoformat("1970-01-01 " + firstline[0][0:8])  # we keep only time in hour-minute-seconde (no microsecond)
        # print(firstline)
        if len(firstline) > 3 and firstline[3]:
            events = firstline[3].split(",")
            for event in events:
                if event[-6:] == "-start":
                    sequence.append(transition_names[int(event[0:-6])])
                    timed_sequence.append([transition_names[int(event[0:-6])], time])
                if event[-4:] == "-end":  # set the final time. Be careful, handle only event with exactly one "start" and one "end" (with "start" before "end")
                    for i in range(len(timed_sequence)):
                        if timed_sequence[i][0] == transition_names[int(event[0:-4])]:
                            timed_sequence[i][1] = time - timed_sequence[i][1]
                            break
        for line in spamreader:
            # print(line)
            if not line[0]:
                continue
            time = datetime.fromisoformat("1970-01-01 " + line[0][0:8])
            if len(line) > 3 and line[3]:
                events = line[3].split(",")
                for event in events:
                    if event[-6:] == "-start":
                        sequence.append(transition_names[int(event[0:-6])])
                        timed_sequence.append([transition_names[int(event[0:-6])], time])
                    if event[-4:] == "-end":  # set the final time. See previous comment
                        for i in range(len(timed_sequence)):
                            if timed_sequence[i][0] == transition_names[int(event[0:-4])]:
                                timed_sequence[i][1] = time - timed_sequence[i][1]
    casas_database.append(sequence)
    # if the end of an event is not given, we assume the event finish at the end of the record
    # maybe we can try to remove the event instead
    for i in range(len(timed_sequence)):
        if type(timed_sequence[i][1]) is datetime:
            timed_sequence[i][1] = time - timed_sequence[i][1]
        # to avoid log undefined problem, timedelta is not null (set 1 second instead)
        if timed_sequence[i][1] == timedelta(0):
            timed_sequence[i][1] = timedelta(1)
    casas_timed_database.append(timed_sequence)
# print(casas_database, len(casas_database))
# print(casas_timed_database, len(casas_timed_database))


### Search patterns
nb_sequence = len(casas_database)
alphabet = generate_alphabet(casas_database)
#### Using modificated pattern discovery algorithm to be faster
#with open("../database/"+filename+"/patterns.txt", "w") as f:
#     f.write(str(patterns))
with open("./database/"+filename+"/patterns.txt") as f:
    patterns = f.readline()
patterns = eval(patterns)
# print(patterns)

## Generate PTPN

place_num = 0
resource_places = {}
transitions = {}
PTPN = ProbabilisticTimePetriNet(name)


### Plot the distribution of time for transitions and chose the best one (according to Wasserstein distance)
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


print("="*50)
print("Compute Energy and Wasserstein distance")
print("Distribution\t| Energy | Wasserstein")
for transition_name in alphabet:
    durations = []
    for id_sequence in range(len(casas_timed_database)):
        sequence = casas_timed_database[id_sequence]
        for id_event in range(len(sequence)):
            if sequence[id_event][0] == transition_name:
                durations.append(sequence[id_event][1])
    durations = [d.total_seconds() if type(d) is timedelta else d for d in durations]
    # start plot
    x = np.linspace(0.01, max(durations), 100)
    print("-"*50)
    print(f"{transition_name} ({len(durations)} events)")
    plt.hist(durations, bins=10, density=True, range=None)

    # log-normal
    lognormal_parameters = lognormal_event_duration(casas_timed_database, transition_name)
    lognormal_sample = [random.lognormvariate(**lognormal_parameters) for _ in range(10000)]
    lognormal_wasserstein_distance = wasserstein_distance(durations, lognormal_sample)
    print("log-normal ", round(energy_distance(durations, lognormal_sample), 1), round(lognormal_wasserstein_distance), sep="\t| ")
    plt.plot(x, lognormal_proba(x, **lognormal_parameters), label="log-normal "+param(lognormal_parameters))
    time_function_type = "lognormal"
    time_function = lognormal_parameters
    min_wasserstein_distance = lognormal_wasserstein_distance

    # normal
    normal_parameters = normal_event_duration(casas_timed_database, transition_name)
    normal_sample = [random.normalvariate(**normal_parameters) for _ in range(10000)]
    normal_wasserstein_distance = wasserstein_distance(durations, normal_sample)
    print("normal     ", round(energy_distance(durations, normal_sample), 1), round(normal_wasserstein_distance), sep="\t| ")
    plt.plot(x, normal_proba(x, **normal_parameters), label="normal "+param(normal_parameters))
    if normal_wasserstein_distance < min_wasserstein_distance:
        time_function_type = "normal"
        time_function = normal_parameters
        min_wasserstein_distance = normal_wasserstein_distance

    # exponential
    exponential_parameters = exponential_event_duration(casas_timed_database, transition_name)
    exponential_sample = [random.expovariate(exponential_parameters["lambd"]) for _ in range(10000)]
    exponential_wasserstein_distance = wasserstein_distance(durations, exponential_sample)
    print("exponential", round(energy_distance(durations, exponential_sample), 1), round(exponential_wasserstein_distance), sep="\t| ")
    plt.plot(x, exponential_proba(x, **exponential_parameters), label="exponential "+param(exponential_parameters))    
    if exponential_wasserstein_distance < min_wasserstein_distance:
        time_function_type = "exponential"
        time_function = exponential_parameters
        min_wasserstein_distance = exponential_wasserstein_distance
    
    # gamma
    gamma_parameters = gamma_event_duration(casas_timed_database, transition_name)
    gamma_sample = [random.gammavariate(gamma_parameters["k"], gamma_parameters["theta"]) for _ in range(10000)]
    gamma_wasserstein_distance = wasserstein_distance(durations, gamma_sample)
    print("gamma      ", round(energy_distance(durations, gamma_sample), 1), round(gamma_wasserstein_distance), sep="\t| ")
    plt.plot(x, gamma_proba(x, **gamma_parameters), label="gamma "+param(gamma_parameters))
    if gamma_wasserstein_distance < min_wasserstein_distance:
        time_function_type = "gamma"
        time_function = gamma_parameters
        min_wasserstein_distance = gamma_wasserstein_distance
    

    # SB: interval
    #interval_parameters = {"min" :  min(durations), "max" : max(durations) }
    #time_function_type = "interval"
    #time_function = interval_parameters

    # finish plot
    plt.title(transition_name)
    plt.xlabel("time (s)")
    plt.ylabel("frequency / probability")
    plt.legend()
    # ax = plt.gca()
    # ax.set_ylim([0, 3e-5])
    plt.savefig("lognorm_dist/" + transition_name + ".png")
    plt.close("all")

    # transition = PTPN.add_transition(transition_name, lognormal_parameters, "lognormal")
    transition = PTPN.add_transition(transition_name, time_function, time_function_type)
    print("Chosen time distribution:", transition.display_time())
    transitions[transition_name] = transition
print("="*50)

distributions = {}
### Pattern discovery
for support in range(nb_sequence, minimal_support-1, -1):
    for pattern in patterns[support]:
        for i in range(len(pattern)-1):
            if transitions[pattern[i]] not in distributions:
                distributions[transitions[pattern[i]]] = {transitions[pattern[i+1]]: support}
            elif transitions[pattern[i+1]] not in distributions[transitions[pattern[i]]]:
                distributions[transitions[pattern[i]]][transitions[pattern[i+1]]] = support
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
        PTPN.add_distribution(transition, [outcome], [1])  # no weight for the moment, probability 1
if start_place.post_transitions == []:
    # it is a loop: not playable without information about initial marking
    PTPN.remove_place(start_place)
if end_place.pre_transitions == []:
    # it is a loop: not playable without information about initial marking
    PTPN.remove_place(end_place)

#PTPN.build_graphviz_png(path=name)
#SB:Write the generated net
#f = open("assessmentdata.xml", "w")
#f.write(PTPN.build_xml())
#f.close()

#SB:Write to file PNML
PTPN.export_pnml("assessmentdata.pnml")

try:
    print("Most probable path:")
    shortest_path = PTPN.find_most_probable_pathway(start_place, end_place)
    print(*shortest_path, sep="\n")
    print("-"*20)
    print("Expeted duration of this path:", PTPN.get_pathway_expected_duration(shortest_path))
except Exception:
    print("Cannot find most probable path")

#PTPN.play(1000*len(PTPN.transitions), {end_place: 1})
