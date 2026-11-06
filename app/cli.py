from app import records

data = records.load_records()

while True:
    print("\n1. Show all")
    print("2. Search")
    print("3. Exit")
    choice = input("Choose: ")

    if choice == "1":
        for r in data:
            print(r["id"], r["product"], r["location"], r["price_per_kg"])
    elif choice == "2":
        word = input("Search: ")
        for r in records.search(data, word):
            print(r["id"], r["product"], r["location"], r["price_per_kg"])
    elif choice == "3":
        break