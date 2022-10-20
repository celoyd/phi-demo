# gpx_sampler.py wonderland_trail.gpx phi ..10 32610
# Get 9 coordinates from the Wonderland Trail in EPSG:32610, spaced by phi

# Todo: sort out click commands v. arguments

import gpxpy
from dals import Linestring
from pyproj import Transformer
import click


@click.command()
@click.argument(
    "gpx_path", required=True, type=click.File("r")  # , help="GPX file to sample from."
)
@click.argument(
    "step",
    required=True,
    type=str,  # click.Choice((float, 'phi', 'φ', 'golden')),
)
@click.argument(
    "point-range",
    required=True,
    type=str,
    # help="Point range in the form n..m, inclusive.",
)
@click.argument(
    "epsg",
    required=True,
    type=int,
    # help="EPSG to project into, e.g., 3857 for spherical Mercator.",
)
@click.option(
    "-c",
    "--counter/--no-counter",
    default=False,
    help="Add a point counter before the x and y.",
)
@click.option(
    "-s",
    "--separator",
    default=", ",
    help="Separator between counter (if any), x, and y. Default: “, ”.",
)
def sample_gpx(gpx_path, step, epsg, point_range, counter, separator):
    gpx = gpxpy.parse(gpx_path)

    if step in ("phi", "φ", "golden"):
        step = (5**0.5 + 1) / 2
    else:
        try:
            step = float(step)
        except:
            raise ValueError(f"{step} must be a float, “phi”, “φ”, or “golden”")

    default_n = 0
    default_m = int(1e6)
    try:
        n, m = point_range.split("..")
        n = default_n if n == "" else int(n)
        m = default_m if m == "" else int(m)
    except:
        raise ValueError(f"Could not parse {point_range} as a numeric range like n..m.")
    if not 0 <= n <= m:
        raise ValueError(f"The range must start at 0 or above and end after it begins.")

    transformer = Transformer.from_crs(4326, epsg)

    points = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                projected = transformer.transform(point.latitude, point.longitude)
                points.append([*projected])

    ls = Linestring(points, lonlats=(epsg == 4326), wrap=True)

    for c in range(n, m + 1):
        x, y = ls.xy_at_proportion(c * step)

        if counter:
            print(f"{c}{separator}", end="")

        # .6f is μm precision in a meters CRS; see also https://xkcd.com/2170/
        print(f"{x:+.06f}{separator}{y:+.06f}")


if __name__ == "__main__":
    sample_gpx()
