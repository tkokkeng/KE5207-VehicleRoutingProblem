######################################################################################################################
# Import libraries
######################################################################################################################
import os
import pandas as pd
import math
import random


######################################################################################################################
# Private Parameters
######################################################################################################################
# Load the data.
_data_df_ = pd.read_csv(os.path.join('data', 'gifts.csv'), header=0, index_col=0)


######################################################################################################################
# Public Parameters
######################################################################################################################
# Initialise the dictionaries for gift lat/long and weight.
gift_weight = _data_df_['Weight'].to_dict()
gift_latlong = _data_df_[['Latitude', 'Longitude']].to_dict(orient='index')

# Add the depot lat/long to the dictionary
gift_latlong[0] = {'Latitude': 90, 'Longitude': 0}

base_weight = 10
weight_limit = 100

######################################################################################################################
# Public Functions
######################################################################################################################
# This function returns ...
def haversine_distance(origin, destination):

    lat1, lon1 = origin['Latitude'], origin['Longitude']
    lat2, lon2 = destination['Latitude'], destination['Longitude']
    radius = 6371  # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d


######################################################################################################################
# Private Functions
######################################################################################################################

# This function creates an individual for the population.
def create_indiv(gifts):

    # Create an individual in the population.
    undelivered_gifts = gifts
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
        indiv.append(trip)

    return indiv


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
        if (best_weariness == 0) | (trip_weariness < best_weariness) :
            best_weariness = trip_weariness
            best_insert_pos = trip[len(trip)-1]  # last gift
            best_insert_gift = i
            inserted = True

    if inserted:
        if best_insert_pos == 0:
            new_trip = [best_insert_gift] + trip
        elif trip.index(best_insert_pos) == (len(trip)-1):
            new_trip = trip + [best_insert_gift]
        else:
            new_trip = trip[:(trip.index(best_insert_pos) + 1)] + [best_insert_gift] + trip[(trip.index(best_insert_pos) + 1):]
        remaining_gifts.remove(best_insert_gift)
    return inserted, new_trip, remaining_gifts


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


