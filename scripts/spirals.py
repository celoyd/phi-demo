# spirals.py [options] [start point number]..[end point number]
# Print coordinates for points in phyllotactic spirals.
# See docs in --help

import click
from math import sin, cos, pi

φ = (5 ** 0.5 + 1) / 2
φ2π = φ * 2 * pi


def rθ_to_xy(r, θ):
    x = r * cos(θ)
    y = r * sin(θ)
    return x, y


def nth_point(n, radius_scale=1.0, step_angle=φ2π, base_angle=-φ2π):
    r = radius_scale * (n ** 0.5)
    θ = base_angle + (n * step_angle)
    return rθ_to_xy(r, θ)


@click.command()
@click.argument("point-range", required=True, type=str)
@click.option(
    "-r",
    "--radius-scale",
    default=1.0,
    help=(
        "Base size of radii: the 1st point’s radius will be this big, and successive"
        " radii will be scaled accordingly."
    ),
)
@click.option(
    "-a",
    "--step-angle",
    default=φ2π,
    help=(
        "Fraction of the circle to step by (radians / 2π or degrees / 360). Default: φ"
        " = 1.618... (although φ-1 = 0.618... would be equivalent other than overall"
        " rotation)."
    ),
)
@click.option(
    "-b",
    "--base-angle",
    default=-φ2π,
    help=(
        "The hypothetical angle of the 0th point. Default: -φ × 2π (see ‘Angle"
        " convention’ section above)."
    ),
)
@click.option(
    "-s", "--separator", default=", ", help="Separator between point number (if any), x, and y. Default: “, ”."
)
@click.option(
    "-p",
    "--prefix/--no-prefix",
    default=False,
    help=(
        "Prefix points with their point number. Handy for debugging and manual copying."
    ),
)
@click.option(
    "-x",
    "--x-offset",
    default=0.0,
    help="Set x origin (where the spiral will center on the x axis). Default: 0.",
)
@click.option("-y", "--y-offset", default=0.0, help="Same as -x but for the y axis.")
def cli(
    point_range,
    radius_scale,
    step_angle,
    base_angle,
    separator,
    prefix,
    x_offset,
    y_offset,
):
    """
    Print the x, y coordinates of the nth point or the or n..mth points
    (inclusive) in a phyllotactic spiral. Designed to make inputs for drawing
    or sampling scripts, and to be easy to port.

    POINT_RANGE has a grammar like n|[n]..[m] where n and m are positive
    integers and n <= m. The cases are:

    n (e.g., 20): print only point n.

    n..m (e.g., 10..30): print points from n through m, inclusive
    (1..3 means 1, 2, 3).

    n.. or ..m (e.g., 20.. or ..20): replace a missing n with 0 and a missing
    m with 1e6, then treat it as above. Note that since we start at 0 and
    ranges are inclusive, ..20 prints 21 points.

    The default endpoint at 1e6 is to protect against terminal spam and
    unintentional infinite loops beyond the author’s idea of a plausible
    upper limit of usefulness. But you can manually specify a million-digit
    number if your system can handle it.

    Angle convention: Assuming no x or y offset, the 0th point is at x=0, y=0
    and the 1st is at x=<radius-scale>, y=0 (so, by default, x=1, y=0). This
    is meant as a simple implicit test to show that things are working as
    expected. To make it work, we set the 0th’s point’s “angle” (which is
    moot, since it has radius 0) to -φ × 2π, which is the angle that the
    -1st point would have if it existed. To get a spiral that is rotated as
    in most demos you can find on the web, override this with --base-angle=0.
    """

    n = 0
    m = int(1e6)

    splitted = point_range.split("..")
    if point_range == "..":
        pass
    elif point_range.endswith(".."):
        n = int(splitted[0])
    elif point_range.startswith(".."):
        m = int(splitted[1])
    elif len(splitted) == 1:
        n = int(splitted[0])
        m = n
    elif len(splitted) == 2:
        n, m = map(int, splitted)
    else:
        raise ValueError(f"Could not parse the point range.")

    assert 0 <= n <= m, f"{n}..{m} does not satisfy 0 <= n <= m."

    for pt in range(n, m + 1):
        x, y = nth_point(pt, radius_scale, step_angle, base_angle)

        x += x_offset
        y += y_offset

        if prefix:
            print(f"{pt}{separator}", end="")

        # .6f is μm precision in a meters CRS; see also https://xkcd.com/2170/
        print(f"{x:+.06f}{separator}{y:+.06f}")


if __name__ == "__main__":
    cli()
