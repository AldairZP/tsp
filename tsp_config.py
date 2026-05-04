from dataclasses import dataclass


@dataclass(frozen=True)
class GAConfig:
    population_size: int = 100
    elitism_size: int = 1
    tournament_size: int = 5
    generations: int = 100

    mutation_rate: float = 0.05
    crossover_rate: float = 0.80

    sa_initial_temp: float = 1000.0
    sa_cooling_rate: float = 0.99
    sa_iterations: int = 50

    sa_only_iterations: int = 10000

    # --- Híbrido: Micro-SA (ajuste fino local, rápido) ---
    sa_hybrid_initial_temp: float = 100.0
    sa_hybrid_cooling_rate: float = 0.80
    sa_hybrid_iterations: int = 20

    # --- Híbrido: aplicar SA solo al top X% de la población ---
    sa_hybrid_elite_fraction: float = 0.10

    # --- Híbrido: aprendizaje Baldwiniano (no sobrescribe genotipo) ---
    use_baldwinian: bool = True

    # --- Híbrido: mutación dinámica ---
    min_mutation_rate: float = 0.15
    max_mutation_rate: float = 0.30
    diversity_threshold: float = 0.05


# Mapa que usará la animación por defecto (debe existir en maps.json).
ANIMATION_MAP_NAME = "corners_random_64"
# Cantidad de rutas intermedias que se mostrarán en la animación.
ANIMATION_SAMPLES = 50
