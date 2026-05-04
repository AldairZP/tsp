import json
import math
import random
import statistics
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


def tournament_selection(population, k, key=None):
    if key is None:
        key = calculate_route_distance
    selection = random.sample(population, k)
    return min(selection, key=key)


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


# ---------------------------------------------------------------------------
# AG Puro (Genetic Algorithm without Simulated Annealing improver)
# ---------------------------------------------------------------------------
def solve_tsp_ga_only(
    cities_list,
    config: GAConfig,
    seed: int = None,
):
    if seed is not None:
        random.seed(seed)

    population = [create_route(cities_list) for _ in range(config.population_size)]

    best_route_global = min(population, key=calculate_route_distance)
    best_dist_global = calculate_route_distance(best_route_global)

    for _ in range(config.generations):
        new_population = []

        sorted_pop = sorted(population, key=calculate_route_distance)
        new_population.extend(sorted_pop[: config.elitism_size])

        current_best = sorted_pop[0]
        current_best_dist = calculate_route_distance(current_best)

        if current_best_dist < best_dist_global:
            best_route_global = current_best
            best_dist_global = current_best_dist

        while len(new_population) < config.population_size:
            parent1 = tournament_selection(population, config.tournament_size)
            parent2 = tournament_selection(population, config.tournament_size)

            if random.random() < config.crossover_rate:
                child = ordered_crossover(parent1, parent2)
            else:
                child = parent1[:]

            child = mutate(child, config.mutation_rate)
            new_population.append(child)

        population = new_population

    final_best = min(population, key=calculate_route_distance)
    final_dist = calculate_route_distance(final_best)

    return final_best, final_dist


# ---------------------------------------------------------------------------
# RS Puro (Pure Simulated Annealing)
# ---------------------------------------------------------------------------
def solve_tsp_sa_only(
    cities_list,
    config: GAConfig,
    seed: int = None,
):
    if seed is not None:
        random.seed(seed)

    route = create_route(cities_list)
    current_dist = calculate_route_distance(route)
    best_route = route[:]
    best_dist = current_dist

    temp = config.sa_initial_temp

    for _ in range(config.sa_only_iterations):
        new_route = route[:]
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
            route = new_route
            current_dist = new_dist

        if current_dist < best_dist:
            best_route = route[:]
            best_dist = current_dist

        temp *= config.sa_cooling_rate
        if temp < 1e-8:
            break

    return best_route, best_dist


# ---------------------------------------------------------------------------
# Híbrido mejorado (micro‑SA, Baldwiniano, élite‑SA, mutación dinámica)
# ---------------------------------------------------------------------------
def solve_tsp_hybrid(
    cities_list,
    config: GAConfig,
    seed: int = None,
):
    if seed is not None:
        random.seed(seed)

    def _fitness(indiv):
        if isinstance(indiv, tuple):
            return indiv[1]
        return calculate_route_distance(indiv)

    def _route(indiv):
        if isinstance(indiv, tuple):
            return indiv[0]
        return indiv

    pop_routes = [create_route(cities_list) for _ in range(config.population_size)]
    population = [(r, calculate_route_distance(r)) for r in pop_routes]

    best_route, best_dist = min(population, key=_fitness)
    best_route = _route(best_route)[:]

    current_mutation = config.min_mutation_rate

    for _ in range(config.generations):
        # --- mutación dinámica: diversidad baja → aumentar mutación ---
        if config.max_mutation_rate > config.min_mutation_rate:
            fitnesses = [f for _, f in population]
            cv = statistics.stdev(fitnesses) / statistics.mean(fitnesses)
            if cv < config.diversity_threshold:
                current_mutation = config.max_mutation_rate
            else:
                current_mutation = config.min_mutation_rate

        new_population = []

        population.sort(key=_fitness)
        new_population.extend(population[: config.elitism_size])

        current_best = population[0]
        cur_route, cur_fit = _route(current_best), _fitness(current_best)
        if cur_fit < best_dist:
            best_route = cur_route[:]
            best_dist = cur_fit

        while len(new_population) < config.population_size:
            parent1 = tournament_selection(
                population, config.tournament_size, key=_fitness
            )
            parent2 = tournament_selection(
                population, config.tournament_size, key=_fitness
            )

            if random.random() < config.crossover_rate:
                child_route = ordered_crossover(
                    _route(parent1), _route(parent2)
                )
            else:
                child_route = _route(parent1)[:]

            child_route = mutate(child_route, current_mutation)
            child_fit = calculate_route_distance(child_route)
            new_population.append((child_route, child_fit))

        # --- Micro‑SA solo sobre la fracción élite ---
        if config.sa_hybrid_elite_fraction > 0:
            new_population.sort(key=_fitness)
            elite_sa_count = max(
                1, int(len(new_population) * config.sa_hybrid_elite_fraction)
            )
            for i in range(elite_sa_count):
                original_route, _ = new_population[i]
                improved_route = simulated_annealing_improver(
                    original_route,
                    config.sa_hybrid_initial_temp,
                    config.sa_hybrid_cooling_rate,
                    config.sa_hybrid_iterations,
                )
                improved_dist = calculate_route_distance(improved_route)

                if improved_dist < best_dist:
                    best_route = improved_route[:]
                    best_dist = improved_dist

                if config.use_baldwinian:
                    new_population[i] = (original_route, improved_dist)
                else:
                    new_population[i] = (improved_route, improved_dist)

        population = new_population

    final_best_route, final_best_dist = min(population, key=_fitness)
    final_best_route = _route(final_best_route)

    if best_dist < final_best_dist:
        return best_route, best_dist
    return final_best_route, final_best_dist


# ---------------------------------------------------------------------------
# Original solve_tsp (backwards-compatible wrapper — delegates to hybrid)
# ---------------------------------------------------------------------------
def solve_tsp(
    cities_list,
    map_name,
    config=None,
    collect_history=False,
    history_interval=10,
    progress_callback: Optional[Callable[[int, float], None]] = None,
    verbose=True,
):
    config = config or GAConfig()

    if verbose:
        print(f"\nStarting Hybrid GA-SA solver for map: {map_name}")
        print(f"Population: {config.population_size}, Generations: {config.generations}")
        print("-" * 50)

    route, dist = solve_tsp_hybrid(cities_list, config)

    if verbose:
        print("-" * 50)
        print(f"Final Best Distance: {dist:.2f}")

    return route, dist, []
