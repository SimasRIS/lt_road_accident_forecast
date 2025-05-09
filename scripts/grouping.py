import pandas as pd

"""
Grouping: Events data:
"""

# Groups the number of traffic accidents by year.
def group_by_year(events_df):
    return events_df.groupby('metai').size().reset_index(name='accident_number')

# Groups the number of traffic accidents by municipality.
def group_by_municipality(events_df):
    return events_df.groupby('savivaldybe').size().reset_index(name='accident_number')

# Groups the number of traffic accidents by type of accident
def group_by_event_type(events_df):
    return events_df.groupby('rusis').size().reset_index(name='accident_number')

# Groups the number of traffic accidents by road surface condition.
def group_by_road_surface(events_df):
    return events_df.groupby('dangosBukle').size().reset_index(name='accident_number')

"""
Grouping: Participants data:
"""

# Groups participants by age.
def group_participants_by_age(participants_df):
    return participants_df.groupby('amzius').size().reset_index(name='number_of_participants')

# Groups participants by gender.
def group_participants_by_gender(participants_df):
    return participants_df.groupby('lytis').size().reset_index(name='number_of_participants')

# Groups participants according to their legal status in the event (e.g., perpetrator, non-violator)
def group_participants_by_status(participants_df):
    return participants_df.groupby('dalyvioBusena').size().reset_index(name='number_of_participants')

# Groups participants according to their condition (e.g., injured, uninjured).
def group_participants_by_condition(participants_df):
    return participants_df.groupby('bukle').size().reset_index(name='number_of_participants')

# Groups participants according to driving experience.
def group_participants_by_experience(participants_df):
    return participants_df.groupby('vairavimoStazas').size().reset_index(name='number_of_participants')

if __name__ == '__main__':
    # Reading cleaned files
    events_df = pd.read_csv('../data/processed/cleaned_events.csv')
    participants_df = pd.read_csv('../data/processed/cleaned_participants.csv')

    print(group_by_year(events_df).head(15))

    print(group_participants_by_gender(participants_df).head(15))

    print(group_participants_by_condition(participants_df).head(15))



