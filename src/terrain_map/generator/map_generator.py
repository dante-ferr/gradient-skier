import numpy as np
import random
from perlin_noise import PerlinNoise
from terrain_map import TerrainMap
from .generator_config import generator_config
from ._corridor_generator import CorridorGenerator

class MapGenerator:
    """
    Procedurally generates a more natural-looking TerrainMap.
    The corridor path is now generated on a smooth map to guarantee convergence.
    """

    def __init__(self, config_override=None):
        self.config = generator_config
        if config_override:
            for key, value in config_override.items():
                setattr(self.config, key, value)

        self.warp_noise_x = PerlinNoise(
            octaves=self.config.BASIN_WARP_OCTAVES, seed=random.randint(0, 10000)
        )
        self.warp_noise_y = PerlinNoise(
            octaves=self.config.BASIN_WARP_OCTAVES, seed=random.randint(0, 10000)
        )
        self.corridor_generator = CorridorGenerator(self.config)

    def generate(self, width, height):
        """
        The main public method. Generates and returns a new TerrainMap.
        """
        xx, yy = np.meshgrid(np.linspace(-5, 5, width), np.linspace(-5, 5, height))
        shelter_coords_logical = self._find_shelter_location()

        # 1. Generate the base layers of the map
        shelter_map, detail_noise_map = self._generate_base_terrain(
            xx, yy, shelter_coords_logical
        )

        # 2. Generate the safe corridor based on the base terrain
        attenuation_mask = self._generate_corridor_mask(
            width, height, xx, yy, shelter_coords_logical, shelter_map, detail_noise_map
        )

        # 3. Generate traps and apply the corridor's attenuation
        attenuated_traps_map = self._generate_and_attenuate_traps(
            xx, yy, width, height, attenuation_mask
        )

        # 4. Combine all layers and normalize the final map
        final_map, shelter_coords_pixel = self._combine_and_finalize_map(
            shelter_map,
            attenuated_traps_map,
            detail_noise_map,
            shelter_coords_logical,
            width,
            height,
        )

        return (
            final_map,
            attenuation_mask,
        )

    def _find_shelter_location(self):
        """Finds a random location for the shelter, ensuring it's not too central."""
        while True:
            shelter_x = random.uniform(-5, 5)
            shelter_y = random.uniform(-5, 5)
            # Ensure the shelter is somewhat near an edge for a longer path
            if abs(shelter_x) + abs(shelter_y) > 5:
                return shelter_x, shelter_y

    def _generate_base_terrain(self, xx, yy, shelter_coords_logical):
        """Generates the main shelter basin and the fine detail noise."""
        shelter_x, shelter_y = shelter_coords_logical
        shelter_map = self._create_warped_gaussian_basin(
            xx,
            yy,
            shelter_x,
            shelter_y,
            self.config.SHELTER_DEPTH,
            self.config.SHELTER_WIDTH,
        )
        detail_noise_map = self._generate_detail_noise(xx, yy)
        return shelter_map, detail_noise_map

    def _generate_corridor_mask(
        self,
        width,
        height,
        xx,
        yy,
        shelter_coords_logical,
        shelter_map,
        detail_noise_map,
    ):
        """Generates the attenuation mask for the safe corridor."""
        map_for_pathfinding = shelter_map  # Pathfind on the smooth main basin
        map_for_start_search = (
            shelter_map + detail_noise_map
        )  # Find start on detailed map
        return self.corridor_generator.generate_attenuation_mask(
            width,
            height,
            xx,
            yy,
            shelter_coords_logical,
            map_for_pathfinding,
            map_for_start_search,
        )

    def _generate_and_attenuate_traps(self, xx, yy, width, height, attenuation_mask):
        """Generates the trap map and applies the corridor attenuation."""
        traps_map, _ = self._generate_traps(xx, yy, width, height)
        return traps_map * attenuation_mask

    def _combine_and_finalize_map(
        self,
        shelter_map,
        traps_map,
        detail_noise_map,
        shelter_coords_logical,
        width,
        height,
    ):
        """Combines all map layers and normalizes them into a TerrainMap object."""
        total_map_float = shelter_map + traps_map + detail_noise_map

        shelter_x_logical, shelter_y_logical = shelter_coords_logical
        shelter_px_x = int((shelter_x_logical + 5) / 10.0 * (width - 1))
        shelter_px_y = int((shelter_y_logical + 5) / 10.0 * (height - 1))
        shelter_idx = (shelter_px_y, shelter_px_x)

        normalized_map = self._normalize_to_255(total_map_float, shelter_idx)
        start_alt_abs = int(self.config.START_ALTITUDE_THRESHOLD_PERCENT * 255)

        terrain_map = TerrainMap(
            normalized_map, (shelter_px_x, shelter_px_y), start_alt_abs
        )
        return terrain_map, (shelter_px_x, shelter_px_y)

    def _create_warped_gaussian_basin(self, xx, yy, cx, cy, depth, width):
        warp_freq = self.config.BASIN_WARP_FREQUENCY
        warp_amp = self.config.BASIN_WARP_AMPLITUDE
        points = np.stack([xx.ravel() * warp_freq, yy.ravel() * warp_freq], axis=1)
        x_warp_vals = (
            np.array([self.warp_noise_x(p.tolist()) for p in points]).reshape(xx.shape)
            * warp_amp
        )
        y_warp_vals = (
            np.array([self.warp_noise_y(p.tolist()) for p in points]).reshape(yy.shape)
            * warp_amp
        )
        xx_warped = xx + x_warp_vals
        yy_warped = yy + y_warp_vals
        return -depth * np.exp(
            -((xx_warped - cx) ** 2 + (yy_warped - cy) ** 2) / width**2
        )

    def _generate_traps(self, xx, yy, width, height):
        area = width * height
        num_traps_base = int(area * self.config.TRAP_DENSITY)
        num_traps = max(1, random.randint(num_traps_base - 1, num_traps_base + 2))
        traps_map, trap_coords = np.zeros_like(xx), []
        for _ in range(num_traps):
            trap_x, trap_y = random.uniform(-5, 5), random.uniform(-5, 5)
            base_trap_depth = random.uniform(
                self.config.TRAP_ABSOLUTE_DEPTH_MIN, self.config.TRAP_ABSOLUTE_DEPTH_MAX
            )
            trap_width = random.uniform(
                self.config.TRAP_WIDTH_MIN, self.config.TRAP_WIDTH_MAX
            )
            traps_map += self._create_warped_gaussian_basin(
                xx, yy, trap_x, trap_y, base_trap_depth, trap_width
            )
            trap_coords.append((trap_x, trap_y))
        return traps_map, trap_coords

    def _generate_detail_noise(self, xx, yy):
        seed = random.randint(0, 100000)
        noise_base = PerlinNoise(octaves=self.config.DETAIL_NOISE_OCTAVES, seed=seed)
        noise_map = np.zeros_like(xx)
        freq = self.config.DETAIL_NOISE_FREQUENCY
        amp = self.config.DETAIL_NOISE_AMPLITUDE
        points = np.stack([xx.ravel() * freq, yy.ravel() * freq], axis=1)
        noise_vals = np.array([noise_base(p.tolist()) for p in points]).reshape(
            xx.shape
        )
        noise_map = noise_vals * amp
        return noise_map

    def _normalize_to_255(self, data, shelter_idx):
        min_val = data[shelter_idx]
        max_val = np.max(data)
        if max_val <= min_val:
            return np.full_like(data, 128, dtype=np.uint8)
        normalized = 255 * (data - min_val) / (max_val - min_val)
        normalized[normalized < 0] = 0
        return normalized.astype(np.uint8)
