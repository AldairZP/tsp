from tsp_core import build_cities, load_maps, solve_tsp
from tsp_config import GAConfig


def main():
    maps = load_maps()
    map_names = list(maps.keys())

    print("Available Maps:")
    for i, name in enumerate(map_names):
        print(f"{i + 1}. {name} ({len(maps[name])} cities)")

    choice = input("\nSelect a map number: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(map_names):
            selected_map_name = map_names[idx]
            city_data = maps[selected_map_name]
            cities = build_cities(city_data)

            config = GAConfig()
            best_route, _, _ = solve_tsp(cities, selected_map_name, config=config, verbose=True)

            print("\nBest Route Found:")
            for city in best_route:
                print(city, end=" -> ")
            print(best_route[0])
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a number.")


if __name__ == "__main__":
    main()
