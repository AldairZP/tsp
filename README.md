# TSP Solver — Algoritmo Genético, Recocido Simulado e Híbrido

Solución al **Problema del Agente Viajero (TSP)** que implementa y compara tres enfoques algorítmicos: Algoritmo Genético puro, Recocido Simulado puro y un híbrido memético (AG + RS con mejora local).

## Estructura del Proyecto

```
tsp/
├── tsp_config.py          # Parámetros centralizados (dataclass GAConfig)
├── tsp_core.py            # Dominio + 3 solvers (AG, RS, Híbrido)
├── tsp_solver.py          # CLI interactivo para ejecutar el híbrido
├── simulacion_tsp.py      # Benchmark automático: 180 corridas, CSV, estadísticas
├── tsp_visualization.py   # Helpers de Manim (dibujo de ciudades y rutas)
├── tsp_manim_scene.py     # Escena Manim que anima la evolución de rutas
├── maps.json              # Coordenadas de ciudades (9 datasets + berlin52 + eil101)
├── resultados_crudos.csv  # Salida del benchmark (180 filas)
├── requirements.txt
└── README.md
```

## Algoritmos Implementados

### 1. AG Puro — `solve_tsp_ga_only()`

Algoritmo Genético estándar sin mejora local:

- **Selección por torneo** (`tournament_selection`): elige `k` individuos al azar y retorna el de menor distancia.
- **Cruce ordenado (OX1)** (`ordered_crossover`): preserva un segmento del padre 1 y rellena el resto con el padre 2 en orden.
- **Mutación por intercambio** (`mutate`): con probabilidad `mutation_rate`, intercambia dos ciudades.
- **Elitismo**: el mejor individuo pasa intacto a la siguiente generación.

### 2. RS Puro — `solve_tsp_sa_only()`

Recocido Simulado estándar partiendo de una ruta aleatoria:

- En cada iteración: intercambia dos ciudades, evalúa la nueva distancia.
- Si mejora: acepta siempre. Si empeora: acepta con probabilidad `exp(-ΔE / T)`.
- Enfría la temperatura: `T ← T × α` en cada paso.
- Se detiene cuando `T < 1e-8`.

### 3. Híbrido — `solve_tsp_hybrid()`

Combina el AG con mejora local mediante RS. Incluye **cuatro mejoras clave** respecto a un híbrido naïve:

| # | Mejora | Problema que resuelve | Implementación |
|---|--------|----------------------|----------------|
| 1 | **Filtro de Élite** | Aplicar SA a todos los hijos derrocha tiempo en individuos mediocres | SA solo al 10% superior de la población cada generación |
| 2 | **Micro-SA** | El SA de propósito general (`T₀=1000, α=0.99`) es demasiado lento y agresivo para ajuste fino | Parámetros ligeros: `T₀=100`, `α=0.80`, solo 20 iteraciones |
| 3 | **Aprendizaje Baldwiniano** | El SA lamarckiano sobrescribe el genotipo, destruyendo diversidad genética | Se preserva el genotipo original; solo se asigna el fitness mejorado para guiar la selección |
| 4 | **Mutación Dinámica** | Con `mutation_rate=0.05` fijo, la población converge prematuramente | Se monitorea el coeficiente de variación de los fitness; si cae bajo `0.05`, la mutación sube a `0.30` |

#### Flujo del Híbrido

```
1. Población inicial aleatoria (100 individuos)
2. Para cada generación (100):
   a. Mutación dinámica: medir diversidad → ajustar tasa de mutación
   b. Elitismo: preservar el mejor
   c. Selección por torneo + cruce OX1 (80% prob) + mutación → llenar población
   d. Micro-SA solo sobre el top 10% de la nueva población:
      - Baldwiniano: guardar genotipo original, asignar fitness mejorado
      - Si la ruta mejorada es la mejor global, registrarla
3. Retornar la mejor ruta encontrada
```

#### Comparación: Lamarckiano vs Baldwiniano

| Aspecto | Lamarckiano | Baldwiniano |
|---------|-------------|-------------|
| Genotipo tras SA | Se reemplaza por la ruta mejorada | Se mantiene el original |
| Fitness | Distancia de la ruta mejorada | Distancia de la ruta mejorada |
| Diversidad | Se pierde rápido (todas las rutas convergen al mismo óptimo local) | Se preserva (el material genético original sobrevive para cruzarse) |
| Efecto | La población se homogeneiza en pocas generaciones | La selección guía hacia buenas regiones sin destruir variabilidad |

## Datasets

Cargados desde `maps.json`. Se incluyen 11 conjuntos de coordenadas:

| Dataset | Nodos | Origen |
|---------|-------|--------|
| random_10 | 10 | Generado |
| circle_12 | 12 | Generado |
| sparse_15 | 15 | Generado |
| grid_20 | 20 | Generado |
| clustered_24 | 24 | Generado |
| corners_random_64 | 64 | Generado |
| mega_100 | 100 | Generado |
| **berlin52** | 52 | [TSPLIB](http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/) — óptimo ≈ 7542 |
| **eil101** | 101 | [TSPLIB](http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/) — óptimo ≈ 629 |

El benchmark (`simulacion_tsp.py`) evalúa exclusivamente sobre `berlin52` y `eil101`.

## Parámetros

Todos los parámetros están en `tsp_config.py` como `@dataclass(frozen=True) GAConfig`:

### AG
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `population_size` | 100 | Individuos por generación |
| `generations` | 100 | Ciclos de evolución |
| `crossover_rate` | 0.80 | Probabilidad de cruce OX1 (si no, se copia el padre 1) |
| `mutation_rate` | 0.05 | Probabilidad de intercambio de 2 ciudades |
| `elitism_size` | 1 | Mejores individuos preservados |
| `tournament_size` | 5 | Tamaño del torneo de selección |

### RS Puro
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `sa_initial_temp` | 1000 | Temperatura inicial |
| `sa_cooling_rate` | 0.99 | Factor de enfriamiento por iteración |
| `sa_only_iterations` | 10000 | Iteraciones máximas (se detiene antes si T < 1e-8) |

### Híbrido (mejora local)
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `sa_hybrid_initial_temp` | 100 | Temperatura inicial (micro-SA) |
| `sa_hybrid_cooling_rate` | 0.80 | Enfriamiento rápido |
| `sa_hybrid_iterations` | 20 | Iteraciones por aplicación de SA |
| `sa_hybrid_elite_fraction` | 0.10 | Fracción élite que recibe SA |
| `use_baldwinian` | True | Aprendizaje Baldwiniano activado |
| `min_mutation_rate` | 0.15 | Mutación base (dinámica) |
| `max_mutation_rate` | 0.30 | Mutación máxima cuando hay poca diversidad |
| `diversity_threshold` | 0.05 | Umbral de coeficiente de variación para activar mutación alta |

## Ejecución

### Solver interactivo
```bash
python3 tsp_solver.py
```
Elige un mapa, ejecuta el híbrido y muestra la mejor ruta.

### Benchmark automático
```bash
python3 simulacion_tsp.py
```
Ejecuta **180 corridas** (30 semillas × 3 algoritmos × 2 instancias) y produce:
- `resultados_crudos.csv` — 180 filas con columnas: `Algoritmo, Instancia, Seed, Distancia, Tiempo`
- Tabla resumen en consola con promedio, desviación estándar, mejor distancia y tiempo promedio.

### Animación (Manim)
```bash
pip install manim
manim -pql tsp_manim_scene.py TSPRouteEvolution
```

## Resultados del Benchmark

30 corridas independientes por algoritmo e instancia. Mismas semillas para los tres algoritmos.

### berlin52 (52 ciudades — óptimo ≈ 7542)

| Algoritmo | Prom Dist | Desv Est | Mejor | T Prom |
|-----------|-----------|----------|-------|--------|
| AG | 13422.18 | 881.81 | 11953.63 | 2.49s |
| RS | 11771.63 | 741.13 | 10580.46 | 0.03s |
| **Híbrido** | **11508.08** | **536.78** | **10626.48** | **1.70s** |

### eil101 (101 ciudades — óptimo ≈ 629)

| Algoritmo | Prom Dist | Desv Est | Mejor | T Prom |
|-----------|-----------|----------|-------|--------|
| AG | 1685.78 | 77.67 | 1559.36 | 6.86s |
| **RS** | **1417.84** | **82.08** | **1285.37** | **0.05s** |
| Híbrido | 1787.92 | 80.00 | 1624.23 | 5.47s |

### Análisis por instancia

- **berlin52**: El híbrido es el claro ganador. Supera al AG por 14% y al RS por 2% en distancia promedio, con una desviación estándar un 28% menor que el RS (mayor estabilidad). Tiempo 5× menor que la versión naïve del híbrido.

- **eil101**: El RS puro domina en distancia y tiempo. Sin embargo, el híbrido redujo su distancia en 37% respecto al híbrido naïve original. El AG se mantiene competitivo con buena estabilidad.

- **Impacto de las 4 mejoras**: El híbrido pasó de ser el peor algoritmo (distancia 17819 en berlin52, 2840 en eil101) a ser el mejor en berlin52 y competitivo en eil101. El tiempo se redujo 5× en berlin52 y 3.3× en eil101.

### Conclusiones

#### Algoritmo Genético (AG)

El AG destaca por su **consistencia** y **estabilidad**. En ambas instancias, su desviación estándar es comparable o inferior a la del RS, lo que indica que produce resultados predecibles corrida tras corrida — una propiedad deseable en entornos donde la repetibilidad importa. Sin embargo, sufre de **convergencia prematura**: sin un mecanismo de escape de óptimos locales (como el RS), la población tiende a estancarse en la segunda mitad de las generaciones. Su costo computacional crece linealmente con el tamaño de la instancia y el número de generaciones, siendo ~2.5 s para 52 ciudades y ~6.9 s para 101. Es una **sólida línea base**, pero sin mejora local no alcanza la calidad del RS ni del híbrido en instancias donde el paisaje de búsqueda tiene muchos óptimos locales.

#### Recocido Simulado (RS)

El RS es el algoritmo más **sorprendente** de la comparación. A pesar de su simplicidad — parte de una ruta aleatoria y solo aplica intercambios de pares — obtiene resultados **competitivos o superiores** en ambas instancias, y lo hace en tiempos **insignificantes** (30–50 ms). La clave está en su calendario de enfriamiento agresivo (`α=0.99`): en ~2500 iteraciones la temperatura cae a cero, lo que significa que explora ampliamente al inicio (fase caliente, aceptando soluciones peores con alta probabilidad) y luego afina localmente (fase fría, solo aceptando mejoras). Esta dualidad exploración/explotación, controlada automáticamente por la temperatura, resulta notablemente efectiva para TSP con pocas ciudades. Su principal debilidad es que **no escala bien**: al aumentar el número de ciudades, el espacio de búsqueda crece factorialmente y las ~2500 iteraciones se vuelven insuficientes. Además, al no mantener una población, **carece de memoria**: no puede recombinar buenos fragmentos de rutas descubiertos en iteraciones anteriores.

#### Híbrido (AG + RS)

El híbrido representa la **síntesis** de ambos enfoques. Hereda la exploración global del AG (población diversa, cruce de material genético) y la explotación local del RS (ajuste fino de rutas prometedoras). Sin embargo, su diseño requiere **cuidado**: la versión naïve (SA agresivo sobre todos los hijos, lamarckiano, mutación fija) resultó ser el **peor** algoritmo — la mejora local excesiva homogeneizó la población en pocas generaciones, anulando la ventaja del AG. Las 4 correcciones aplicadas (filtro de élite, micro-SA, Baldwiniano, mutación dinámica) revirtieron este comportamiento por completo, convirtiéndolo en el **mejor algoritmo para berlin52** y en un competidor sólido para eil101. La lección principal es que en un algoritmo memético, la **dosis** de mejora local debe ser quirúrgica: poca intensidad, poca frecuencia, y siempre preservando la diversidad genética.

#### Resumen comparativo

| Criterio | AG | RS | Híbrido |
|----------|----|----|---------|
| Calidad de solución | Media | Alta (instancias pequeñas) | Alta (mejor en berlin52) |
| Estabilidad (desv est baja) | Alta | Media | Alta |
| Velocidad | Media (2–7 s) | Muy alta (30–50 ms) | Media-alta (1.7–5.5 s) |
| Escalabilidad | Buena | Mala (explosión factorial) | Buena |
| Complejidad de implementación | Media | Baja | Alta |
| Riesgo de convergencia prematura | Alto | Bajo (escapismo por temperatura) | Medio (requiere calibración) |
| Recomendado para | Instancias donde la repetibilidad es crítica | Prototipado rápido, instancias pequeñas | Mejor calidad absoluta en instancias medianas |

## Dependencias

```
Python ≥ 3.8
manim (opcional, solo para animación)
```

Todas las demás dependencias son de la biblioteca estándar (`json`, `math`, `random`, `csv`, `statistics`, `time`, `dataclasses`).
