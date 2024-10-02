######################################
#           Pattern discovery        #
#     Author :  Le Moigne            #
# theo.le-moigne@ens-paris-saclay.fr #
#              30/11/2023            #
#         modified 04/06/2024        #
######################################

"""
Implementation of Continuous Pattern Discovery from "Automated Generation of Models of Activities
of Daily Living" by Jérémie Saives and Gregory Faraut (https://hal.science/hal-00999505) and
"Automatic Discovery and Deviation Detection of Temporal Inhabitant Habits" by Kevin Viard
(unpublished).

Use a database of n sequences of event (max length: m) from an alphabet sigma (max length: l) and a minimal support supp_min
"""

import copy
from datetime import timedelta
import math


def eval_dates(timed_database, pattern):
    """
    Evaluate dates of a pattern
    timed_database: list of n sequences (lists containing events from alphabet sigma and time)
    pattern: a list of event to find in sequences
    return ld: the dates of the given pattern (start, end for each occurrence)
    """
    k = len(pattern)
    ld = []
    for sequence in timed_database:
        for n in range(len(sequence)-k+1):
            if pattern == map(lambda x: x[0], sequence[n:n+k]):
                ld.append([sequence[n][1], sequence[n+k][1]])
    return ld


def average_pattern_duration(timed_database, pattern):
    """
    Evaluate average duration of a pattern
    timed_database: list of n sequences (lists containing events from alphabet sigma and time)
    pattern: a list of event to find in sequences
    return: float
    """
    ld = eval_dates(timed_database, pattern)
    durations = map(lambda x: x[1]-x[0], ld)
    return sum(durations)/len(durations)


def average_event_duration(timed_database, event):
    """
    Evaluate average duration of an event
    timed_database: list of n sequences (lists containing events from alphabet sigma and time)
    return: float
    """
    durations = []
    for id_sequence in range(len(timed_database)):
        sequence = timed_database[id_sequence]
        for id_event in range(len(sequence)):
            if sequence[id_event][0] == event:
                if id_event != 0:
                    durations.append(sequence[id_event][1] - sequence[id_event-1][1])
                elif id_sequence != 0:
                    durations.append(sequence[id_event][1] - timed_database[id_sequence-1][-1][1])
                else:
                    durations.append(sequence[id_event][1])
    return sum(durations)/len(durations)


def interval_event_duration(timed_database, event, initial_time=None):
    """
    Evaluate the interval duration of an event
    timed_database: list of n sequences (lists containing events from alphabet sigma and time)
    return: interval, list of min and max duration
    """
    durations = []
    for id_sequence in range(len(timed_database)):
        sequence = timed_database[id_sequence]
        for id_event in range(len(sequence)):
            if sequence[id_event][0] == event:
                if id_event != 0:
                    durations.append(sequence[id_event][1] - sequence[id_event-1][1])
                elif id_sequence != 0:  # b careful, only possible if it's folowing sequences
                    durations.append(sequence[id_event][1] - timed_database[id_sequence-1][-1][1])
                elif initial_time is not None:  # if initial time is not defined, it's not possible to compute the duration of the first event
                    durations.append(sequence[id_event][1] - initial_time)
    return [min(durations), max(durations)]


def lognormal_event_duration(timed_database, event, initial_time=None):
    """
    Evaluate log-normal parameters of the duration of an event
    timed_database: list of n sequences (lists containing events from alphabet sigma and time)
    return: dict with "mu" and "sigma" parameters
    """
    following_event = False  # if True, compute duration by difference of following event time, else, the duration is already given
    durations = []
    for id_sequence in range(len(timed_database)):
        sequence = timed_database[id_sequence]
        for id_event in range(len(sequence)):
            if sequence[id_event][0] == event:
                if following_event:
                    if id_event != 0 and sequence[id_event][1] > sequence[id_event-1][1]:
                        durations.append(sequence[id_event][1] - sequence[id_event-1][1])
                    elif id_sequence != 0 and sequence[id_event][1] > timed_database[id_sequence-1][-1][1]:  # be careful, only possible for folowing sequences
                        durations.append(sequence[id_event][1] - timed_database[id_sequence-1][-1][1])
                    elif initial_time is not None:  # if initial time is not defined, it's not possible to compute the duration of the first event
                        durations.append(sequence[id_event][1] - initial_time)
                else:
                    durations.append(sequence[id_event][1])
    durations = [d.total_seconds() if type(d) is timedelta else d for d in durations]
    mu = sum([math.log(d) for d in durations])/len(durations)
    sigma = math.sqrt(sum([(math.log(d) - mu)**2 for d in durations])/(len(durations)-1))  # Bessel's correction
    return {"mu": mu, "sigma": sigma}


def normal_event_duration(timed_database, event, initial_time=None):
    """
    Evaluate normal parameters of the duration of an event
    timed_database: list of n sequences (lists containing events from alphabet sigma and time)
    return: dict with "mu" and "sigma" parameters
    """
    following_event = False  # if True, compute duration by difference of following events time, else, the duration is already given
    durations = []
    for id_sequence in range(len(timed_database)):
        sequence = timed_database[id_sequence]
        for id_event in range(len(sequence)):
            if sequence[id_event][0] == event:
                if following_event:
                    if id_event != 0 and sequence[id_event][1] > sequence[id_event-1][1]:
                        durations.append(sequence[id_event][1] - sequence[id_event-1][1])
                    elif id_sequence != 0 and sequence[id_event][1] > timed_database[id_sequence-1][-1][1]:  # be careful, only possible for folowing sequences
                        durations.append(sequence[id_event][1] - timed_database[id_sequence-1][-1][1])
                    elif initial_time is not None:  # if initial time is not defined, it's not possible to compute the duration of the first event
                        durations.append(sequence[id_event][1] - initial_time)
                else:
                    durations.append(sequence[id_event][1])
    durations = [d.total_seconds() if type(d) is timedelta else d for d in durations]
    mu = sum(durations)/len(durations)
    sigma = math.sqrt(sum([(d - mu)**2 for d in durations])/(len(durations)-1))  # Bessel's correction
    return {"mu": mu, "sigma": sigma}


def exponential_event_duration(timed_database, event, initial_time=None):
    """
    Evaluate exopnential parameter of the duration of an event
    timed_database: list of n sequences (lists containing events from alphabet sigma and time)
    return: dict with "lambd" parameter
    """
    following_event = False  # if True, compute duration by difference of following events time, else, the duration is already given
    durations = []
    for id_sequence in range(len(timed_database)):
        sequence = timed_database[id_sequence]
        for id_event in range(len(sequence)):
            if sequence[id_event][0] == event:
                if following_event:
                    if id_event != 0 and sequence[id_event][1] > sequence[id_event-1][1]:
                        durations.append(sequence[id_event][1] - sequence[id_event-1][1])
                    elif id_sequence != 0 and sequence[id_event][1] > timed_database[id_sequence-1][-1][1]:  # be careful, only possibles for folowing sequences
                        durations.append(sequence[id_event][1] - timed_database[id_sequence-1][-1][1])
                    elif initial_time is not None:  # if initial time is not defined, it's not possible to compute the duration of the first event
                        durations.append(sequence[id_event][1] - initial_time)
                else:
                    durations.append(sequence[id_event][1])
    durations = [d.total_seconds() if type(d) is timedelta else d for d in durations]
    lambd = len(durations)/sum(durations)
    return {"lambd": lambd}


def gamma_event_duration(timed_database, event, initial_time=None):
    """
    Evaluate gamme parameters of the duration of an event
    timed_database: list of n sequences (lists containing events from alphabet sigma and time)
    return: dict with "k" and "theta" parameter
    """
    following_event = False  # if True, compute duration by difference of following events time, else, the duration is already given
    durations = []
    for id_sequence in range(len(timed_database)):
        sequence = timed_database[id_sequence]
        for id_event in range(len(sequence)):
            if sequence[id_event][0] == event:
                if following_event:
                    if id_event != 0 and sequence[id_event][1] > sequence[id_event-1][1]:
                        durations.append(sequence[id_event][1] - sequence[id_event-1][1])
                    elif id_sequence != 0 and sequence[id_event][1] > timed_database[id_sequence-1][-1][1]:  # be careful, only possible for folowing sequences
                        durations.append(sequence[id_event][1] - timed_database[id_sequence-1][-1][1])
                    elif initial_time is not None:  # if initial time is not defined, it's not possible to compute the duration of the first event
                        durations.append(sequence[id_event][1] - initial_time)
                else:
                    durations.append(sequence[id_event][1])
    durations = [d.total_seconds() if type(d) is timedelta else d for d in durations]
    mu = sum(durations)/len(durations)
    sigma = math.sqrt(sum([(d - mu)**2 for d in durations])/(len(durations)-1))  # Bessel's correction
    k = (mu/sigma)**2
    theta = mu/k
    gamma_k = 1
    for i in range(1, 1000):
        gamma_k *= (1+1/i)**k/(1+k/i)
    gamma_k *= 1/k
    return {"k": k, "theta": theta, "gamma_k": gamma_k}


def check_inclusion(pattern, sequence):
    """
    Check if a pattern is include in a sequence (or an other pattern)
    pattern: the included or not pattern
    sequence: the sequence containing or not the pattern
    return: boolean
    complexity: O(m²/4)
    """
    # maybe optimisable
    for i in range(len(sequence)+1-len(pattern)):
        if pattern == sequence[i:i+len(pattern)]:
            return True
    return False


def eval_support(database, pattern, max_support=None):
    """
    Evaluate support of a pattern (stop searching when max_support is reached)
    database: list of n sequences (lists containing events from alphabet sigma)
    pattern: a list of event to find in sequences
    max_support: int
    return support: the support of the given pattern
    complexity: O(n*m²/4)
    """
    support = 0
    for sequence in database:
        if check_inclusion(pattern, sequence):
            support += 1
            if support == max_support:
                return support
    return support


def generate_alphabet(database):
    """
    Generate the alphabet Sigma of event in a database
    database: list of n sequences (lists containing events from alphabet sigma)
    return sigma: the alphabet in database
    complexity: O(n*m*l)
    """
    sigma = []
    for sequence in database:
        for event in sequence:
            if event not in sigma:
                sigma.append(event)
    return sigma


def init(database, supp_min, sigma):
    """
    Initialize the list of pattern with pattern of elementary length (length 2) for given support
    database: list of n sequences (lists containing events from alphabet sigma)
    sigma: an alphabet
    supp_min: minimal support
    return list_elem: list of patterns of elementary lenght
    """
    list_elem = []
    for event1 in sigma:
        for event2 in sigma:
            pattern_test = [event1, event2]
            if eval_support(database, pattern_test) >= supp_min:
                list_elem.append(pattern_test)
    return list_elem


def init_all_supports(database, sigma):
    """
    Initialize the list of pattern with pattern of elementary length (length 2) for all supports
    database: list of n sequences (lists containing events from alphabet sigma)
    sigma: an alphabet
    return list_elem: dict of list of patterns of elementary lenght indexed by support
    complexity: O(n*l²*m)
    """
    patterns = {(e1, e2): 0 for e1 in sigma for e2 in sigma}
    for sequence in database:
        patterns_found = {pattern: False for pattern in patterns}
        for i in range(len(sequence) - 1):
            patterns_found[(sequence[i], sequence[i+1])] = True
        for pattern, found in patterns_found.items():
            if found:
                patterns[pattern] += 1
    list_disc = {support: [] for support in range(1, len(database)+1)}
    for pattern, support in patterns.items():
        if support > 0:
            list_disc[support].append(list(pattern))
    return list_disc


def cand_gen(list_disc, list_comp=None):
    """
    Candidate Generation: two overlapping patterns form a candidate with a least one from
    list_disc: list of previous discoverd patterns (at least one needed)
    list_comp: list of patterns with other support
    return list_cand: list of possible patterns
    complexity: O(2*len(list_disc)*len(list_comp)+len(list_disc)²) <= O(3*nb_pattenrs) <= O(3*l²)
    """
    if list_comp is None:
        list_comp = []
    list_cand = []
    list_tot = list_disc + list_comp
    for pattern1 in list_disc:
        for pattern2 in list_tot:
            if pattern1[1:] == pattern2[:-1]:
                list_cand.append([pattern1[0]] + pattern2)
    for pattern1 in list_comp:
        for pattern2 in list_disc:
            if pattern1[1:] == pattern2[:-1]:
                list_cand.append([pattern1[0]] + pattern2)
    return list_cand


def continuous_pattern_discovery(database, supp_min, sigma=None):
    """
    Continuous Pattern Discovery which list pattern of minimal support found in a sequences
    database: list of n sequences (lists containing events from an alphabet sigma)
    supp_min: minimal support
    return list_disc: list of dicovered patterns
    """
    if not sigma:
        sigma = generate_alphabet(database)
    list_disc = init(database, supp_min, sigma)
    list_cand = cand_gen(list_disc)
    new_candidate = True
    # I change end condition to avoid inifinite loop (if a candidate has a small support)
    while new_candidate:
        # print(list_disc)
        new_candidate = False
        for pattern_cand in list_cand:
            if eval_support(database, pattern_cand) >= supp_min:
                to_remove = []
                for pattern_disc in list_disc:
                    if check_inclusion(pattern_disc, pattern_cand):
                        to_remove.append(pattern_disc)
                for pattern in to_remove:
                    list_disc.remove(pattern)
                list_disc.append(pattern_cand)
                new_candidate = True
        if new_candidate:
            list_cand = cand_gen(list_disc)
    return list_disc


def pattern_discovery(database, sigma=None):
    """
    Pattern Discovery which list pattern for each support found in a sequences
    database: list of n sequences (lists containing events from an alphabet sigma)
    return list_disc: dict of list of patterns of elementary lenght indexed by support
    complexity: O(n*m*l) + O(n*l²*m) + O(while*(n+n*(l²+l²*(n*m²/4+l²*m²/4)))) = O(while*n*l²*m²/4*(n+l²))
    complexity: while is majored by the maximal length of a pattern (=m) because the candidate pattern are strictly longuer than the previous ones
    complexity: O(n*m³*l²*(n+l²))
    complexity: l <= n*m (if all events are different)
    complexity: majored by O(n**5*m**7) which is polynomial
    """
    if not sigma:
        sigma = generate_alphabet(database)
    list_disc = init_all_supports(database, sigma)                      # discovered patterns
    list_old_disc = {support: [] for support in list_disc}
    start = len(database)
    while list_old_disc != list_disc:
        # print(list_disc)
        for support in range(start, 0, -1):
            if list_disc[support] == list_old_disc[support]:
                start = support-1
            else:
                break
        list_old_disc = copy.deepcopy(list_disc)
        list_cand = {support: [] for support in range(1, len(database)+1)}  # candidate patterns
        list_comp = []
        for support in range(start, 0, -1):
            list_cand[support] = cand_gen(list_disc[support], list_comp)
            # print(support, list_cand)
            list_comp.extend(list_old_disc[support])
            for pattern_cand in list_cand[support]:
                if pattern_cand in list_disc[support]:
                    continue
                support_found = eval_support(database, pattern_cand, support)
                if support_found == 0:
                    continue
                for pattern_disc in list_old_disc[support_found]:
                    if check_inclusion(pattern_disc, pattern_cand) and pattern_disc in list_disc[support_found]:
                        list_disc[support_found].remove(pattern_disc)
                list_disc[support_found].append(pattern_cand)
    return list_disc
