import pandas as pd

"""
Grouping: Events data:
"""

# Groups the number of traffic accidents by year.
def group_by_year(events_df):
    return events_df.groupby('metai').size().reset_index(name='accident_number').sort_values(by='accident_number', ascending=False)

# Groups the number of traffic accidents by municipality.
def group_by_municipality(events_df):
    return events_df.groupby('savivaldybe').size().reset_index(name='accident_number').sort_values(by='accident_number', ascending=False)

# Groups the number of traffic accidents by type of accident.
def group_by_event_type(events_df):
    return events_df.groupby('rusis').size().reset_index(name='accident_number').sort_values(by='accident_number', ascending=False)

# Groups the number of traffic accidents by road surface condition.
def group_by_road_surface(events_df):
    return events_df.groupby('dangosBukle').size().reset_index(name='accident_number').sort_values(by='accident_number', ascending=False)

"""
Grouping: Participants data:
"""

# Groups participants by age.
def group_participants_by_age(participants_df):
    return participants_df.groupby('amzius').size().reset_index(
        name='number_of_participants').sort_values(by='number_of_participants', ascending=False)

# Groups participants by gender.
def group_participants_by_gender(participants_df):
    return participants_df.groupby('lytis').size().reset_index(
        name='number_of_participants').sort_values(by='number_of_participants', ascending=False)

# Groups participants according to their legal status in the event (e.g., perpetrator, non-violator)
def group_participants_by_status(participants_df):
    return participants_df.groupby('dalyvioBusena').size().reset_index(
        name='number_of_participants').sort_values(by='number_of_participants', ascending=False)

# Groups participants according to their condition (e.g., injured, uninjured).
def group_participants_by_condition(participants_df):
    return participants_df.groupby('bukle').size().reset_index(
        name='number_of_participants').sort_values(by='number_of_participants', ascending=False)

# Groups participants according to driving experience.
def group_participants_by_experience(participants_df):
    return participants_df.groupby('vairavimoStazas').size().reset_index(
        name='number_of_participants').sort_values(by='number_of_participants', ascending=False)

"""
Meniu - Main menu options for the user
"""

def main_menu():
    """
    Displays the main menu options to the user and asks for input.
    """
    print("\n--- MAIN MENU ---")
    print("1. Show number of events by year")
    print("2. Show number of events by municipality")
    print("3. Show number of events by type of traffic accident")
    print("4. Show number of events by road surface condition")
    print("5. Number of participants by age")
    print("6. Number of participants by gender")
    print("7. Number of participants by condition")
    print("8. Number of participants by status")
    print("9. Number of participants by driving experience")
    print("10. Exit")
    choice = input("Select an option (1-10): ")
    return choice

def main():
    """
    Main function to execute the program.
    Handles loading data, displaying the menu, and executing selected options.
    """
    try:
        # Attempting to read the CSV files containing events and participants data
        events_df = pd.read_csv('../data/processed/cleaned_events.csv', low_memory=False)
        participants_df = pd.read_csv('../data/processed/cleaned_participants.csv', low_memory=False)
    except FileNotFoundError as e:
        # Handling the error if the files are not found
        print(f"File not found: {e}")
        return

    # Continuously display the menu until the user selects to exit
    while True:
        choice = main_menu()  # Show the menu and get user choice

        if choice == "1":
            print(group_by_year(events_df).head(15))
        elif choice == "2":
            print(group_by_municipality(events_df).head(15))
        elif choice == "3":
            print(group_by_event_type(events_df).head(15))
        elif choice == "4":
            print(group_by_road_surface(events_df).head(15))
        elif choice == "5":
            print(group_participants_by_age(participants_df).head(15))
        elif choice == "6":
            print(group_participants_by_gender(participants_df).head(15))
        elif choice == "7":
            print(group_participants_by_condition(participants_df).head(15))
        elif choice == "8":
            print(group_participants_by_status(participants_df).head(15))
        elif choice == "9":
            print(group_participants_by_experience(participants_df).head(15))
        elif choice == "10":
            print("Program ended. Goodbye!")  # Exit message
            break  # Exit the loop and end the program
        else:
            print("Invalid choice. Please try again.")  # If the user enters an invalid option

# Entry point of the program
if __name__ == "__main__":
    main()  # Run the main function

