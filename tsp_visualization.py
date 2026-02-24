from manim import Dot, Line, VGroup, WHITE


def normalize_city_positions(cities, width=10.0, height=6.0):
    min_x = min(city.x for city in cities)
    max_x = max(city.x for city in cities)
    min_y = min(city.y for city in cities)
    max_y = max(city.y for city in cities)

    x_span = max(max_x - min_x, 1)
    y_span = max(max_y - min_y, 1)

    city_points = {}
    for city in cities:
        nx = (city.x - min_x) / x_span
        ny = (city.y - min_y) / y_span

        sx = (nx - 0.5) * width
        sy = (ny - 0.5) * height
        city_points[city] = (sx, sy, 0)

    return city_points


def build_cities_group(city_points, radius=0.05, color=WHITE):
    return VGroup(*[Dot(point=point, radius=radius, color=color) for point in city_points.values()])


def build_route_group(route, city_points, color, stroke_width=2):
    if not route:
        return VGroup()

    segments = VGroup()
    for i in range(len(route)):
        from_city = route[i]
        to_city = route[(i + 1) % len(route)]
        segments.add(
            Line(
                city_points[from_city],
                city_points[to_city],
                color=color,
                stroke_width=stroke_width,
            )
        )
    return segments


def pick_route_samples(history, samples=5):
    if not history:
        return []

    if len(history) <= samples:
        return history

    picked = []
    max_index = len(history) - 1
    for i in range(samples):
        index = round(i * max_index / (samples - 1))
        picked.append(history[index])

    return picked
