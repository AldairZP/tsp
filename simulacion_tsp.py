import csv
import math
import random
import time

from tsp_config import GAConfig
from tsp_core import (
    build_cities,
    load_maps,
    solve_tsp_ga_only,
    solve_tsp_hybrid,
    solve_tsp_sa_only,
)

# ---------------------------------------------------------------------------
# 0. Configuración de parámetros — valores estrictos del enunciado
# ---------------------------------------------------------------------------
config = GAConfig(
    population_size=100,
    crossover_rate=0.80,
    mutation_rate=0.05,
    sa_initial_temp=1000.0,
    sa_cooling_rate=0.99,
    generations=100,
    sa_iterations=50,
    sa_only_iterations=10000,
    # --- Híbrido mejorado ---
    sa_hybrid_initial_temp=100.0,
    sa_hybrid_cooling_rate=0.80,
    sa_hybrid_iterations=20,
    sa_hybrid_elite_fraction=0.10,
    use_baldwinian=True,
    min_mutation_rate=0.15,
    max_mutation_rate=0.30,
    diversity_threshold=0.05,
)

INSTANCIAS = ["berlin52", "eil101"]
NUM_SEMILLAS = 30

# ---------------------------------------------------------------------------
# 1. Generar lista de semillas (compartida por todos los algoritmos)
# ---------------------------------------------------------------------------
semilla_base = random.randint(0, 2**31 - 1)
random.seed(semilla_base)
semillas = [random.randint(0, 2**31 - 1) for _ in range(NUM_SEMILLAS)]

print(f"Semilla base: {semilla_base}")
print(f"Semillas generadas: {NUM_SEMILLAS}")
print()

# ---------------------------------------------------------------------------
# 2. Cargar mapas y crear configuraciones de algoritmos
# ---------------------------------------------------------------------------
maps = load_maps()

algoritmos = {
    "AG": solve_tsp_ga_only,
    "RS": solve_tsp_sa_only,
    "Hibrido": solve_tsp_hybrid,
}

# ---------------------------------------------------------------------------
# 3. Ejecutar las 180 corridas
# ---------------------------------------------------------------------------
resultados = []

total_corridas = len(algoritmos) * len(INSTANCIAS) * NUM_SEMILLAS
corrida_actual = 0

for instancia in INSTANCIAS:
    cities = build_cities(maps[instancia])
    print(f"--- {instancia} ({len(cities)} ciudades) ---")

    for nombre_algo, solver in algoritmos.items():
        for seed in semillas:
            corrida_actual += 1

            t0 = time.perf_counter()
            _, distancia = solver(cities, config, seed=seed)
            t1 = time.perf_counter()

            tiempo = t1 - t0
            resultados.append(
                {
                    "Algoritmo": nombre_algo,
                    "Instancia": instancia,
                    "Seed": seed,
                    "Distancia": round(distancia, 2),
                    "Tiempo": round(tiempo, 4),
                }
            )

            print(
                f"  [{corrida_actual}/{total_corridas}] "
                f"{nombre_algo:7s} | {instancia:8s} | seed {seed:10d} "
                f"| dist {distancia:10.2f} | t {tiempo:7.2f}s"
            )

print()

# ---------------------------------------------------------------------------
# 4. Exportar CSV de datos crudos
# ---------------------------------------------------------------------------
csv_path = "resultados_crudos.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=["Algoritmo", "Instancia", "Seed", "Distancia", "Tiempo"]
    )
    writer.writeheader()
    writer.writerows(resultados)

print(f"CSV exportado: {csv_path}")
print()

# ---------------------------------------------------------------------------
# 5. Tablas resumen — estadísticas agrupadas por Algoritmo e Instancia
# ---------------------------------------------------------------------------
print("=" * 95)
print("RESULTADOS — Estadísticas agrupadas por Algoritmo e Instancia")
print("=" * 95)

for instancia in INSTANCIAS:
    print(f"\n{'─' * 70}")
    print(f"  Instancia: {instancia}")
    print(f"{'─' * 70}")
    print(
        f"{'Algoritmo':10s} {'Prom Dist':>10s} {'Desv Est':>10s} "
        f"{'Mejor':>10s} {'T Prom (s)':>10s}"
    )
    print("-" * 55)

    for nombre_algo in ["AG", "RS", "Hibrido"]:
        distancias = [
            r["Distancia"]
            for r in resultados
            if r["Algoritmo"] == nombre_algo and r["Instancia"] == instancia
        ]
        tiempos = [
            r["Tiempo"]
            for r in resultados
            if r["Algoritmo"] == nombre_algo and r["Instancia"] == instancia
        ]

        n = len(distancias)
        media_dist = sum(distancias) / n
        varianza = sum((d - media_dist) ** 2 for d in distancias) / (n - 1)
        desv_est = math.sqrt(varianza)
        mejor_dist = min(distancias)
        media_tiempo = sum(tiempos) / n

        print(
            f"{nombre_algo:10s} {media_dist:10.2f} {desv_est:10.2f} "
            f"{mejor_dist:10.2f} {media_tiempo:10.4f}"
        )

print()
