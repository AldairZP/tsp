import os
import sys

from manim import BLUE_D, Create, DOWN, FadeIn, Scene, Text, Transform, UP, YELLOW

from tsp_config import ANIMATION_MAP_NAME, ANIMATION_SAMPLES, GAConfig
from tsp_core import build_cities, load_maps, solve_tsp
from tsp_visualization import (
    build_cities_group,
    build_route_group,
    normalize_city_positions,
    pick_route_samples,
)


def read_cli_arg(flag, default):
    if flag not in sys.argv:
        return default
    idx = sys.argv.index(flag)
    if idx + 1 >= len(sys.argv):
        return default
    return sys.argv[idx + 1]


def read_runtime_arg(flag, env_var, default):
    env_value = os.getenv(env_var)
    if env_value is not None and str(env_value).strip() != "":
        return env_value
    return read_cli_arg(flag, default)


class TSPRouteEvolution(Scene):
    def construct(self):
        map_name = read_runtime_arg("--map", "TSP_MAP", ANIMATION_MAP_NAME)
        samples = int(read_runtime_arg("--samples", "TSP_SAMPLES", str(ANIMATION_SAMPLES)))

        maps = load_maps()
        if map_name not in maps:
            map_name = next(iter(maps.keys()))

        cities = build_cities(maps[map_name])
        city_points = normalize_city_positions(cities)

        config = GAConfig()

        final_route, final_distance, history = solve_tsp(
            cities,
            map_name,
            config=config,
            collect_history=True,
            history_interval=max(1, config.generations // max(samples, 1)),
            verbose=False,
        )

        sampled_routes = pick_route_samples(history, samples=samples)

        title = Text(f"TSP - {map_name}", font_size=36).to_edge(UP)
        city_group = build_cities_group(city_points)

        self.play(FadeIn(title), FadeIn(city_group), run_time=1.2)

        if sampled_routes:
            current_route = build_route_group(sampled_routes[0], city_points, color=BLUE_D, stroke_width=2)
            self.play(Create(current_route), run_time=1.2)

            for route in sampled_routes[1:]:
                next_route = build_route_group(route, city_points, color=BLUE_D, stroke_width=2)
                self.play(Transform(current_route, next_route), run_time=0.9)

            final_route_group = build_route_group(final_route, city_points, color=YELLOW, stroke_width=3)
            self.play(Transform(current_route, final_route_group), run_time=1.4)

        distance_label = Text(f"Final distance: {final_distance:.2f}", font_size=28).to_edge(DOWN)
        self.play(FadeIn(distance_label), run_time=0.8)
        self.wait(2)
