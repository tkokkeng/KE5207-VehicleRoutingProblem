######################################################################################################################
# Import libraries
######################################################################################################################
import os
import pandas as pd
import math
import random
import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse import lil_matrix
import datetime


######################################################################################################################
# Private Parameters
######################################################################################################################
# Load the data.
_data_df_ = pd.read_csv(os.path.join('data', 'gifts.csv'), header=0, index_col=0)


######################################################################################################################
# Private Functions
######################################################################################################################
# undelivered_gifts is a list
def insert_best_gift_into_trip(trip, undelivered_gifts):
    best_weariness = 0
    best_insert_pos = 0
    best_insert_gift = 0
    inserted = False
    new_trip = trip
    remaining_gifts = undelivered_gifts

    # Look for the best gift to insert into the trip.
    # Check for each undelivered gift :
    for i in remaining_gifts:

        # Total weight of gifts in the trip
        gifts_weight = sum([gift_weight[a_leg] for a_leg in trip]) + base_weight + gift_weight[i]

        # Skip this gift if weight limit is exceeded.
        if gifts_weight > weight_limit:
            continue

        # Check for insertion before 1st gift in the trip:
        # Insert the gift to create a possible trip
        this_trip = [i] + trip

        # Calculate the trip weariness
        trip_weariness = reindeer_weariness_trip(this_trip)

        # Check if this possible trip is the best.
        if trip_weariness < best_weariness:
            best_weariness = trip_weariness
            best_insert_pos = 0  # depot
            best_insert_gift = i
            inserted = True

        # Check for insertion after each gift in the trip less last gift:
        for trip_idx, dest in enumerate(trip[:-1]):

            # Insert the gift to create a possible trip
            this_trip = trip[:(trip_idx + 1)] + [i] + trip[(trip_idx + 1):]

            # Calculate the trip weariness
            trip_weariness = reindeer_weariness_trip(this_trip)

            # Check if this possible trip is the best.
            if trip_weariness < best_weariness:
                best_weariness = trip_weariness
                best_insert_pos = dest
                best_insert_gift = i
                inserted = True

        # Check for insertion after last gift in the trip:
        # Insert the gift to create a possible trip
        this_trip = trip + [i]

        # Calculate the trip weariness
        trip_weariness = reindeer_weariness_trip(this_trip)

        # Check if this possible trip is the best.
        if (best_weariness == 0) | (trip_weariness < best_weariness):
            best_weariness = trip_weariness
            best_insert_pos = trip[len(trip) - 1]  # last gift
            best_insert_gift = i
            inserted = True

    if inserted:
        if best_insert_pos == 0:
            new_trip = [best_insert_gift] + trip
        elif trip.index(best_insert_pos) == (len(trip) - 1):
            new_trip = trip + [best_insert_gift]
        else:
            new_trip = trip[:(trip.index(best_insert_pos) + 1)] + [best_insert_gift] + trip[(trip.index(
                best_insert_pos) + 1):]
        remaining_gifts.remove(best_insert_gift)
    return inserted, new_trip, remaining_gifts


# This function returns a child which is a combination of randomly selected trips from 2 individuals and other trips to complete it.
def get_child(indiv1, indiv2):
    child = []

    insert = True
    while insert:

        # Randomly copy a trip from indiv1 to child1
        all_gifts_child = set([a_gift for a_trip in child for a_gift in a_trip])
        selectable_trips_indiv1 = [a_trip for a_trip in indiv1 if not set(a_trip).intersection(all_gifts_child)]
        if selectable_trips_indiv1:  # not empty list
            ##### for testing
            # x = random.sample(selectable_trips_indiv1, 1)[0]
            # if not x:
            #     print('empty')
            # child.append(x)
            child.append(random.sample(selectable_trips_indiv1, 1)[0])
        else:
            insert = False

        # Randomly copy a trip from indiv2 to child1
        all_gifts_child = set([a_gift for a_trip in child for a_gift in a_trip])
        selectable_trips_indiv2 = [a_trip for a_trip in indiv2 if not set(a_trip).intersection(all_gifts_child)]
        if selectable_trips_indiv2:  # not empty list
            ##### for testing
            # x = random.sample(selectable_trips_indiv2, 1)[0]
            # if not x:
            #     print('empty')
            # child.append(x)
            child.append(random.sample(selectable_trips_indiv2, 1)[0])
        else:
            insert = False

    # Insert remaining gifts into the child.
    # undelivered_gifts = [a_gift for a_gift in range(1, total_gifts + 1) if a_gift not in all_gifts_child]
    all_gifts = [a_gift for a_trip in indiv1 for a_gift in a_trip]
    undelivered_gifts = [a_gift for a_gift in all_gifts if a_gift not in all_gifts_child]
    while len(undelivered_gifts) > 0:

        # Create a new trip
        seed_gift = random.sample(undelivered_gifts, 1)
        undelivered_gifts.remove(seed_gift[0])
        trip = seed_gift

        # Add gifts to the trip.
        while len(undelivered_gifts) > 0:
            inserted, trip, undelivered_gifts = insert_best_gift_into_trip(trip, undelivered_gifts)
            if not inserted:
                break

        # Add the trip to the individual
        ##### for testing
        # if not trip:
        #     print('empty')
        child.append(trip)

    return (type(indiv1))(child)


# This function returns the weighted reindeer weariness for a complete solution.
def weighted_reindeer_weariness(indiv):
    weighted_reindeer_weariness = 0
    for trip in indiv:
        weighted_reindeer_weariness += reindeer_weariness_trip(trip)
    return weighted_reindeer_weariness


# This function returns the weighted reindeer weariness for a single trip (starting and ending at depot).
def reindeer_weariness_trip(trip):
    trip_weariness = 0
    gifts_weight = sum([gift_weight[a_leg] for a_leg in trip]) + base_weight
    leg_start = [0] + trip[0:-1]

    for index, leg_end in enumerate(trip):
        leg_distance = haversine_distance(gift_latlong[leg_start[index]], gift_latlong[leg_end])
        trip_weariness = trip_weariness + leg_distance * gifts_weight
        gifts_weight = gifts_weight - gift_weight[leg_end]

    return trip_weariness


# This function returns the haversine distance between 2 points.
def haversine_distance(origin, destination):
    lat1, lon1 = origin['Latitude'], origin['Longitude']
    lat2, lon2 = destination['Latitude'], destination['Longitude']
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


# This function returns a distance matrix of the inter-gift haversine distances.
def _init_dist_matrix_():

    latlon_arr = _data_df_[['Latitude', 'Longitude']].values
    #dist_arr = np.zeros(shape=(latlon_arr.shape[0], latlon_arr.shape[0]))
    dist_arr = lil_matrix((latlon_arr.shape[0], latlon_arr.shape[0]), dtype=np.uint16)

    radius = 6371  # km

    print('start time =', datetime.datetime.now())

    for i in range(latlon_arr.shape[0]):

        dlatlon2 = np.radians(latlon_arr[i:] - latlon_arr[i])[1:]
        dlatlon2_sin_squared = np.square(np.sin(dlatlon2 / 2))

        lat1_cos = math.cos(math.radians(latlon_arr[i, 0]))
        lat2_cos = np.cos(np.radians(latlon_arr[i + 1:, 0]))

        a = dlatlon2_sin_squared[:, 0] + lat1_cos * lat2_cos * dlatlon2_sin_squared[:, 1]
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        d = np.rint(radius * c)

        #test = dist_arr[i+1:, i].shape
        if i % 500 == 0:
            print('giftid =', i, '  ', datetime.datetime.now())
        d = d.reshape((-1, 1))
        dist_arr[i+1:, i] = d

    dist_arr = dist_arr.tocsc()
    return dist_arr


######################################################################################################################
# Public Parameters
######################################################################################################################
# Initialise the dictionaries for gift lat/long and weight.
gift_weight = _data_df_['Weight'].to_dict()
gift_latlong = _data_df_[['Latitude', 'Longitude']].to_dict(orient='index')
#dist_matrix = _init_dist_matrix_()


# Add the depot lat/long to the dictionary
gift_latlong[0] = {'Latitude': 90, 'Longitude': 0}

total_gifts = len(_data_df_)
base_weight = 10
weight_limit = 100

######################################################################################################################
# Public Functions
######################################################################################################################
# This function creates an individual for the population.
def create_indiv(icls, gifts):

    # Create an individual in the population.
    undelivered_gifts = gifts.copy()
    # so that the original list is not changed; need it for each following call to create the population
    indiv = []
    while len(undelivered_gifts) > 0:

        # Create a new trip
        seed_gift = random.sample(undelivered_gifts, 1)
        undelivered_gifts.remove(seed_gift[0])
        trip = seed_gift

        # Add gifts to the trip.
        while len(undelivered_gifts) > 0:
            inserted, trip, undelivered_gifts = insert_best_gift_into_trip(trip, undelivered_gifts)
            if not inserted:
                break

        # Add the trip to the individual
        ##### for testing
        # if not trip:
        #     print('empty trip')
        indiv.append(trip)

    return icls(indiv)


# This function creates an individual for the population using multiprocessing.
def mp_create_indiv(icls, gifts, for_pop, n=1):
    for_pop.append(create_indiv(icls, gifts))
    return None


# This function is a crossover function.
def mate(indiv1, indiv2):
    return (get_child(indiv1, indiv2), get_child(indiv1, indiv2))


# Mutation function 08

# A randomly selected trip is divided into 2 trips using 1 gift as the cut point.
def mutate_08(indiv):

    mutant = indiv.copy()  # if mutation fails, return the same individual, here mutant is converted to type list
    mutant_idx = list(range(0, len(mutant)))
    not_mutated = True

    while (mutant_idx and not_mutated):

        selected_trip_idx = random.sample(mutant_idx, 1)[0]
        selected_trip = mutant[selected_trip_idx]

        if len(selected_trip) > 1:  # perform mutation

            selected_gift_idx = random.randint(0, len(selected_trip) - 1)

            if selected_gift_idx > 0:
                mutated_trip = [selected_trip[:selected_gift_idx], selected_trip[selected_gift_idx:]]
            else:  # special case of index 0
                mutated_trip = [[selected_trip[0]], selected_trip[1:]]

            if selected_trip_idx == 0:  # first trip
                mutant = mutated_trip + mutant[1:]
            elif selected_trip_idx == (len(mutant)-1):  # last trip
                mutant = mutant[:-1] + mutated_trip
            else:  # trip in middle of indiv
                mutant = mutant[:selected_trip_idx] + mutated_trip + mutant[selected_trip_idx + 1:]

            not_mutated = False  # mutation completed

        else:  # cannot mutate because only 1 gift in trip, look for another trip
            mutant_idx.remove(selected_trip_idx)

    ##### for testing
    # for i in mutant:
    #     if not i:
    #         print('empty')
    return ((type(indiv))(mutant),)