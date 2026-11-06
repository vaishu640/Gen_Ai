while True:
    print("\n=== OrganicPath ===")
    print("1. About")
    print("2. Exit")
    choice = input("Choose: ")

    if choice == "1":
        print("OrganicPath helps trace organic produce.")
    elif choice == "2":
        print("Bye!")
        break
    else:
        print("Wrong choice, try again.")