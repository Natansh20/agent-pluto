def get_user_input():
    return input("\nWhat would you like to do?: ")

def confirm_actions(actions, registry):
    print("\nThe system will perform the following actions:")
    for action in actions:
        print(f"- {registry[action]['description']}")

    choice = input("\nDo you want to continue? (yes/no): ").lower()
    if choice not in ["yes", "no"]:
        print("Invalid input. Please enter 'yes' or 'no'.")
        return confirm_actions(actions, registry)
    return choice == "yes"
