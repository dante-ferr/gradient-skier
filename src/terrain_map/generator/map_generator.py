import numpy as np
import random
from perlin_noise import PerlinNoise
from terrain_map import TerrainMap
from .config_loader import generator_config
from .corridor_generator import CorridorGenerator  # Import the new class

class MapGenerator:
    """
    Procedurally generates a more natural-looking TerrainMap.
    It uses coordinate warping for basins and noise masking for ridges
    to create organic, mountain-like features.
    It also uses a CorridorGenerator to ensure a solvable path.
    """

    def __init__(self, config_override=None):
        self.config = generator_config
        if config_override:
            for key, value in config_override.items():
                setattr(self.config, key, value)

        # Initialize noise generators for warping to reuse them
        self.warp_noise_x = PerlinNoise(
            octaves=self.config.BASIN_WARP_OCTAVES, seed=random.randint(0, 10000)
        )
        self.warp_noise_y = PerlinNoise(
            octaves=self.config.BASIN_WARP_OCTAVES, seed=random.randint(0, 10000)
        )

        # Initialize the corridor generator
        self.corridor_generator = CorridorGenerator(self.config)

    def generate(self, width, height):
        """
        The main public method. Generates and returns a new TerrainMap.
        """
        # 1. Create a coordinate grid
        xx, yy = np.meshgrid(np.linspace(-5, 5, width), np.linspace(-5, 5, height))

        # 2. Layer 1: Dominant Basin (The Shelter "Sink")
        while True:
            shelter_x_logical = random.uniform(-5, 5)
            shelter_y_logical = random.uniform(-5, 5)
            if abs(shelter_x_logical) + abs(shelter_y_logical) > 5:
                break

        shelter_map = self._create_warped_gaussian_basin(
            xx,
            yy,
            shelter_x_logical,
            shelter_y_logical,
            self.config.SHELTER_DEPTH,
            self.config.SHELTER_WIDTH,
        )

        # 3. Layer 3: Fine Detail Noise (generated early to help find a good start point)
        detail_noise_map = self._generate_detail_noise(xx, yy)

        # 4. Generate the Safe Corridor Attenuation Mask
        shelter_coords_logical = (shelter_x_logical, shelter_y_logical)
        # We pass a preliminary map so the corridor can find a high start point
        preliminary_map = shelter_map + detail_noise_map
        attenuation_mask = self.corridor_generator.generate_attenuation_mask(
            width, height, xx, yy, shelter_coords_logical, preliminary_map
        )

        # 5. Layer 2: Traps (now attenuated by the mask)
        traps_map, trap_coords = self._generate_traps(
            xx, yy, shelter_coords_logical, width, height, attenuation_mask
        )

        # 6. Combine all layers
        total_map_float = shelter_map + traps_map + detail_noise_map

        # 7. DEFINE the shelter, don't FIND it.
        shelter_px_x = int((shelter_x_logical + 5) / 10.0 * (width - 1))
        shelter_px_y = int((shelter_y_logical + 5) / 10.0 * (height - 1))
        shelter_idx = (shelter_px_y, shelter_px_x)  # (row, col) format

        # 8. Normalize the final map, FIXING the shelter as the lowest point
        normalized_map = self._normalize_to_255(total_map_float, shelter_idx)

        # 9. Create and return the final TerrainMap object AND the mask for debugging
        return (
            TerrainMap(
                normalized_map,
                (shelter_px_x, shelter_px_y),
                self.config.START_ALTITUDE_THRESHOLD,
            ),
            attenuation_mask,
        )

    def _create_warped_gaussian_basin(self, xx, yy, cx, cy, depth, width):
        """
        Creates a negative gaussian (a valley) with irregular edges by
        warping the coordinates with Perlin noise before calculation.
        """
        warp_freq = self.config.BASIN_WARP_FREQUENCY
        warp_amp = self.config.BASIN_WARP_AMPLITUDE

        points = np.stack([xx.ravel() * warp_freq, yy.ravel() * warp_freq], axis=1)
        x_warp_vals = (
            np.array([self.warp_noise_x([p[0], p[1]]) for p in points]).reshape(
                xx.shape
            )
            * warp_amp
        )
        y_warp_vals = (
            np.array([self.warp_noise_y([p[0], p[1]]) for p in points]).reshape(
                yy.shape
            )
            * warp_amp
        )

        xx_warped = xx + x_warp_vals
        yy_warped = yy + y_warp_vals

        return -depth * np.exp(
            -((xx_warped - cx) ** 2 + (yy_warped - cy) ** 2) / width**2
        )

    def _generate_traps(self, xx, yy, shelter_coords, width, height, attenuation_mask):
        """
        Generates the trap layer, applying the attenuation mask to trap depth.
        """
        area = width * height
        num_traps_base = int(area * self.config.TRAP_DENSITY)
        num_traps = max(1, random.randint(num_traps_base - 1, num_traps_base + 2))

        traps_map, trap_coords = np.zeros_like(xx), []
        shelter_x, shelter_y = shelter_coords

        for _ in range(num_traps):
            # No need for the empty sector logic anymore,
            # as the corridor handles solvability.
            trap_x, trap_y = random.uniform(-5, 5), random.uniform(-5, 5)

            # Use ABSOLUTE depth, not RATIO
            base_trap_depth = random.uniform(
                self.config.TRAP_ABSOLUTE_DEPTH_MIN,
                self.config.TRAP_ABSOLUTE_DEPTH_MAX,
            )

            # --- CRITICAL FIX: Apply attenuation mask ---
            # 1. Convert logical trap coords to pixel coords
            trap_px_x = int((trap_x + 5) / 10.0 * (width - 1))
            trap_px_y = int((trap_y + 5) / 10.0 * (height - 1))

            # 2. Get the strength multiplier from the mask
            multiplier = attenuation_mask[trap_px_y, trap_px_x]

            # 3. Calculate final attenuated depth
            final_trap_depth = base_trap_depth * multiplier
            # --- End Fix ---

            trap_width = random.uniform(
                self.config.TRAP_WIDTH_MIN, self.config.TRAP_WIDTH_MAX
            )

            traps_map += self._create_warped_gaussian_basin(
                xx, yy, trap_x, trap_y, final_trap_depth, trap_width
            )
            trap_coords.append((trap_x, trap_y))

        return traps_map, trap_coords

    def _generate_detail_noise(self, xx, yy):
        """
        Generates the fine-detail noise layer.
        """
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
        """
        This method is intended to normalize the heightmap data to the 0-255 range.

        The normalization logic here ensures that the shelter,
        which is the logical lowest point,
        is always mapped to 0 (black), and all other terrain,
        including traps, is scaled relative to it.
        """

        # The minimum value is DEFINED as the shelter's value.
        min_val = data[shelter_idx]
        max_val = np.max(data)

        if max_val <= min_val:
            return np.full_like(data, 128, dtype=np.uint8)

        normalized = 255 * (data - min_val) / (max_val - min_val)

        normalized[normalized < 0] = 0

        return normalized.astype(np.uint8)
