import json
import math
import random
import sys
from typing import Callable, Optional

from tsp_config import GAConfig


class City:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, City):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def distance_to(self, other_city):
        x_dist = abs(self.x - other_city.x)
        y_dist = abs(self.y - other_city.y)
        return math.sqrt((x_dist ** 2) + (y_dist ** 2))

    def __repr__(self):
        return f"({self.x},{self.y})"


def load_maps(filename="maps.json"):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            return data["maps"]
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)


def build_cities(city_data):
    return [City(d["x"], d["y"]) for d in city_data]


def create_route(cities):
    return random.sample(cities, len(cities))


def calculate_route_distance(route):
    path_distance = 0
    for i in range(len(route)):
        from_city = route[i]
        to_city = route[(i + 1) % len(route)]
        path_distance += from_city.distance_to(to_city)
    return path_distance


def tournament_selection(population, k):
    selection = random.sample(population, k)
    return min(selection, key=calculate_route_distance)


def ordered_crossover(parent1, parent2):
    child = [None] * len(parent1)

    start_pos = random.randint(0, len(parent1) - 1)
    end_pos = random.randint(0, len(parent1) - 1)

    if start_pos > end_pos:
        start_pos, end_pos = end_pos, start_pos

    for i in range(start_pos, end_pos + 1):
        child[i] = parent1[i]

    p2_index = 0
    for i in range(len(child)):
        if child[i] is None:
            while parent2[p2_index] in child:
                p2_index += 1
            child[i] = parent2[p2_index]

    return child


def mutate(route, mutation_rate):
    if random.random() < mutation_rate:
        idx1, idx2 = random.sample(range(len(route)), 2)
        route[idx1], route[idx2] = route[idx2], route[idx1]
    return route


def simulated_annealing_improver(route, initial_temp, cooling_rate, iterations):
    current_route = route[:]
    current_dist = calculate_route_distance(current_route)

    temp = initial_temp

    for _ in range(iterations):
        new_route = current_route[:]
        idx1, idx2 = random.sample(range(len(new_route)), 2)
        new_route[idx1], new_route[idx2] = new_route[idx2], new_route[idx1]

        new_dist = calculate_route_distance(new_route)
        delta = new_dist - current_dist

        if delta < 0:
            accept = True
        else:
            try:
                probability = math.exp(-delta / temp)
            except OverflowError:
                probability = 0
            accept = random.random() < probability

        if accept:
            current_route = new_route
            current_dist = new_dist

        temp *= cooling_rate
        if temp < 1e-8:
            break

    return current_route


def solve_tsp(
    cities_list,
    map_name,
    config: Optional[GAConfig] = None,
    collect_history=False,
    history_interval=10,
    progress_callback: Optional[Callable[[int, float], None]] = None,
    verbose=True,
):
    config = config or GAConfig()

    population = [create_route(cities_list) for _ in range(config.population_size)]

    if verbose:
        print(f"\nStarting Hybrid GA-SA solver for map: {map_name}")
        print(f"Population: {config.population_size}, Generations: {config.generations}")
        print("-" * 50)

    best_route_global = min(population, key=calculate_route_distance)
    best_dist_global = calculate_route_distance(best_route_global)

    if verbose:
        print(f"Initial Best Distance: {best_dist_global:.2f}")

    history = []
    if collect_history:
        history.append(best_route_global[:])

    for gen in range(config.generations):
        new_population = []

        sorted_pop = sorted(population, key=calculate_route_distance)
        new_population.extend(sorted_pop[: config.elitism_size])

        current_best = sorted_pop[0]
        current_best_dist = calculate_route_distance(current_best)

        if collect_history and gen % history_interval == 0:
            history.append(current_best[:])

        if current_best_dist < best_dist_global:
            best_route_global = current_best
            best_dist_global = current_best_dist

        while len(new_population) < config.population_size:
            parent1 = tournament_selection(population, config.tournament_size)
            parent2 = tournament_selection(population, config.tournament_size)

            child = ordered_crossover(parent1, parent2)
            child = mutate(child, config.mutation_rate)
            child = simulated_annealing_improver(
                child,
                config.sa_initial_temp,
                config.sa_cooling_rate,
                config.sa_iterations,
            )

            new_population.append(child)

        population = new_population

        if progress_callback is not None:
            progress_callback(gen, current_best_dist)
        elif verbose and gen % 10 == 0:
            print(f"Generation {gen}: Best Distance = {current_best_dist:.2f}")

    final_best = min(population, key=calculate_route_distance)
    final_dist = calculate_route_distance(final_best)

    if collect_history:
        history.append(final_best[:])

    if verbose:
        print("-" * 50)
        print(f"Final Best Distance: {final_dist:.2f}")

    return final_best, final_dist, history
