from dataclasses import dataclass


# Mapa que usará la animación por defecto (debe existir en maps.json).
ANIMATION_MAP_NAME = "corners_random_64"
# Cantidad de rutas intermedias que se mostrarán en la animación.
ANIMATION_SAMPLES = 100


@dataclass(frozen=True)
class GAConfig:
    # Número de individuos (rutas) por generación.
    population_size: int = 50
    # Cuántos mejores individuos pasan intactos a la siguiente generación.
    elitism_size: int = 1
    # Tamaño del torneo para seleccionar padres.
    tournament_size: int = 5
    # Probabilidad de mutación de cada hijo (0.1 = 10%).
    mutation_rate: float = 0.1
    # Número total de generaciones del algoritmo genético.
    generations: int = 100

    # Temperatura inicial del Simulated Annealing (exploración inicial).
    sa_initial_temp: float = 100.0
    # Factor de enfriamiento por iteración de SA (más bajo = enfría más rápido).
    sa_cooling_rate: float = 0.90
    # Iteraciones de SA aplicadas para refinar cada hijo.
    sa_iterations: int = 50
