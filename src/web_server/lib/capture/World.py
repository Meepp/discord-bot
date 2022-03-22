import random

import numpy as np
import scipy.signal
import scipy.ndimage
import scipy.stats


class DiamondSquare(object):
    def __init__(self, noise_factor=0.05):
        assert (0 <= noise_factor < 1)

        self.noise_multiplier = noise_factor

    def run(self, ground: np.array, step_size=None):
        if step_size is None:
            step_size = ground.shape[0] - 1

        while step_size > 1:
            random_value = step_size / 2
            self.diamond(ground, step_size, random_value)
            self.square(ground, step_size, random_value)
            step_size = step_size // 2
            random_value *= 2 ** -self.noise_multiplier
        return ground

    def diamond(self, ground, step_size, random_value):
        for x in range(0, ground.shape[0] - 1, step_size):
            for y in range(0, ground.shape[1] - 1, step_size):
                value = random.uniform(-random_value / 2, random_value / 2)
                value += (
                                 ground[x, y] +
                                 ground[x, y + step_size] +
                                 ground[x + step_size, y] +
                                 ground[x + step_size, y + step_size]
                         ) / 4
                ground[x + step_size // 2, y + step_size // 2] = value

    def square(self, ground, step_size, random_value):
        for x in range(0, ground.shape[0], step_size // 2):
            for y in range(0, ground.shape[1], step_size // 2):
                if x % step_size == y % step_size:
                    continue

                value = random.uniform(-random_value / 2, random_value / 2)
                div_value = 0

                # We have an offset at step 0, 2, 4, etc..
                if x - step_size // 2 >= 0:
                    value += ground[x - step_size // 2, y]
                    div_value += 1
                if y - step_size // 2 >= 0:
                    value += ground[x, y - step_size // 2]
                    div_value += 1
                if x + step_size // 2 < ground.shape[0]:
                    value += ground[x + step_size // 2, y]
                    div_value += 1
                if y + step_size // 2 < ground.shape[1]:
                    value += ground[x, y + step_size // 2]
                    div_value += 1

                ground[x, y] = value / div_value


class World(object):
    WATER_VALUE = 0
    GROUND_VALUE = 15
    MOUNTAIN_VALUE = 10

    def __init__(self, n=5, random_factor=4, noise_factor=0.1):
        self.size = 2 ** n + 1

        self.min_z = 0
        self.max_z = 1

        self.diamond_star = DiamondSquare(noise_factor=noise_factor)

        self.ground = np.zeros((self.size, self.size), dtype=float)
        self.capital_coordinates = []

        self.generate(random_factor)

    def generate(self, n=4):
        for i in range(0, self.size, self.size // (2 ** n)):
            for j in range(0, self.size, self.size // (2 ** n)):
                self.ground[i, j] = np.random.randint(self.min_z, self.max_z)

        self.ground = self.diamond_star.run(self.ground, step_size=self.ground.shape[0] // 4)
        self.ground = np.array(scipy.ndimage.gaussian_filter(self.ground, 1))

        ground_mean = np.mean(self.ground)
        ground_std = np.std(self.ground)

        water_percentile = 0.3
        mountain_percentile = 0.9

        water_threshold = scipy.stats.norm.ppf(water_percentile, loc=ground_mean, scale=ground_std)
        mountain_threshold = scipy.stats.norm.ppf(mountain_percentile, loc=ground_mean, scale=ground_std)

        water = self.ground < water_threshold
        mountain = self.ground > mountain_threshold
        ground = 1 - (water + mountain)

        self.ground = (
                water * self.WATER_VALUE +
                ground * self.GROUND_VALUE +
                mountain * self.MOUNTAIN_VALUE).astype(int)

        self.remove_islands(threshold=0.05)

        self.place_capitals(n_capitals=20)

        self.distribute_terrain()
        for capital in self.capital_coordinates:
            self.ground[capital] = 60

    def remove_islands(self, threshold=0.05, removal_type=GROUND_VALUE):
        processed = self.ground == removal_type

        def flood_fill(ground, x, y):
            frontier = [(x, y)]
            count = 0
            while len(frontier) > 0:
                x, y = frontier.pop(0)
                if not (0 <= x < ground.shape[0]):
                    continue
                if not (0 <= y < ground.shape[1]):
                    continue
                if processed[x, y] == 0:
                    continue

                count += 1
                blob[x, y] = 0
                processed[x, y] = 0
                frontier.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
            return count

        while True:
            start = None
            # Blob will become a negative mask over the flood-filled island
            blob = np.ones(processed.shape, dtype=bool)
            for x, col in enumerate(processed):
                for y, elem in enumerate(col):
                    if elem == 1:
                        blob[x, y] = 1
                        start = (x, y)

            if start is None:
                break

            island_size = flood_fill(blob, start[0], start[1])

            if island_size < blob.size * threshold:
                self.ground *= blob

    def place_capitals(self, n_capitals):
        valid_squares = self.ground == self.GROUND_VALUE

        coords = list(zip(*np.where(valid_squares == 1)))
        if len(coords) < n_capitals:
            return
        capitals = random.sample(coords, n_capitals)

        self.capital_coordinates = capitals

    def distribute_terrain(self):
        closest = np.zeros(self.ground.shape, dtype=int)
        distance = np.ones(self.ground.shape, dtype=int) * self.ground.size

        for capital_index, (x, y) in enumerate(self.capital_coordinates):
            frontier = [(x, y, 0)]
            print(capital_index)
            while len(frontier) != 0:
                x, y, dist = frontier.pop(0)

                if not (0 <= x < self.ground.shape[0]):
                    continue
                if not (0 <= y < self.ground.shape[1]):
                    continue
                # Distance does not go over water or mountains
                if self.ground[x, y] != self.GROUND_VALUE:
                    continue
                if dist >= distance[x, y]:
                    continue

                closest[x, y] = capital_index
                distance[x, y] = dist

                frontier.extend([
                    (x + 1, y, dist + 1),
                    (x - 1, y, dist + 1),
                    (x, y + 1, dist + 1),
                    (x, y - 1, dist + 1),
                    (x + 1, y + 1, dist + 1),
                    (x - 1, y - 1, dist + 1),
                    (x - 1, y + 1, dist + 1),
                    (x + 1, y - 1, dist + 1)])

        self.ground += closest


def t_value(x):
    return np.exp(-x ** 2 / 2) / np.sqrt(2 * np.pi)


import matplotlib.pyplot as plt

if __name__ == "__main__":
    for i in range(10):
        percent = (i + 0.0000001) / 10

        world = World(n=7, random_factor=1, noise_factor=0.1)

        plt.imshow(world.ground, interpolation='nearest')

        plt.title("2-D Heat Map")
        plt.show()
