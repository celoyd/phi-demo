# A linestring object that can be sampled at a given fraction of its length.
# I think I meant dals to stand for dot along linestring? I wrote this a while ago.

# Todo: tests

from math import atan2, cos, radians


def xy_to_rθ(x, y):
    r = (x**2 + y**2) ** 0.5
    θ = atan2(y, x)
    return r, θ


class Linestring:
    def __init__(self, xys, lonlats=False, wrap=False):
        self.xys = xys
        self.wrap = wrap
        self.lonlats = lonlats
        self.csum = self.csum()
        self.length = self.csum[-1]

    def normalize_length(self, length):
        return self.normalize_proportion(length / self.length) * self.length

    def normalize_proportion(self, prop):
        if self.wrap:
            prop %= 1
        elif not 0 <= prop <= 1:
            raise ValueError("Length or proportion is out of bounds (try wrapping)")

        return prop

    def csum(self):
        csum = [0]
        for i in range(1, len(self.xys)):
            csum.append(self.segment_length(self.xys[i - 1], self.xys[i]) + csum[i - 1])
        return csum

    def segment_length(self, a, b):
        longitude_factor = 1
        if self.lonlats:
            longitude_factor = cos(radians((a[1] + b[1]) / 2))
        Δx = (a[0] - b[0]) * longitude_factor
        Δy = a[1] - b[1]
        return (Δx**2 + Δy**2) ** 0.5

    def index_before_length(self, length):
        length = self.normalize_length(length)

        left = 0
        right = len(self.csum)

        while right - left > 1:
            sample = (left + right) // 2
            if length == self.csum[sample]:
                left = self.csum[sample]
                right = self.csum[sample]
            elif length <= self.csum[sample]:
                right = sample
            else:
                left = sample
        return left

    def lerp_proportion(self, a, b, prop):
        """Linearly interpolate prop of the way from a to b"""
        return a + ((b - a) * prop)

    def xy_at_proportion(self, prop):
        prop = self.normalize_proportion(prop)
        length = self.length * prop
        return self.xy_at_distance(length)

    def xy_at_distance(self, length):
        start_idx = self.index_before_length(length)
        start, end = self.xys[start_idx : start_idx + 2]
        dist = self.segment_length(start, end)
        length_remainder = length - self.csum[start_idx]
        proportion_of_segment = length_remainder / dist

        x = self.lerp_proportion(start[0], end[0], proportion_of_segment)
        y = self.lerp_proportion(start[1], end[1], proportion_of_segment)

        return x, y
