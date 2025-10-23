import numpy as np
import random
from perlin_noise import PerlinNoise
from terrain_map import TerrainMap
from .config_loader import generator_config


class MapGenerator:
    """
    Procedurally generates a new TerrainMap based on a set of rules
    to ensure the challenge is solvable but complex.
    """

    def __init__(self, config=None):
        """
        Initializes the generator with a configuration.
        """
        # Load the default configuration
        self.config = generator_config
        # Allow for overrides passed during instantiation
        if config:
            self.config.update(config)

    def generate(self, width, height):
        """
        The main public method. Generates and returns a new TerrainMap.
        """
        # 1. Create a coordinate grid (from -5 to 5, independent of pixel size)
        xx, yy = np.meshgrid(np.linspace(-5, 5, width), np.linspace(-5, 5, height))

        # 2. Layer 1: Dominant Basin (The Shelter)
        shelter_x = random.uniform(-3, 3)
        shelter_y = random.uniform(-3, 3)
        shelter_map = self._create_gaussian_basin(
            xx,
            yy,
            shelter_x,
            shelter_y,
            self.config.SHELTER_DEPTH,
            self.config.SHELTER_WIDTH,
        )

        # The shelter's pixel coordinate is the lowest point of its *own* basin
        shelter_idx = np.unravel_index(np.argmin(shelter_map), shelter_map.shape)
        shelter_px_y, shelter_px_x = shelter_idx

        # 3. Layer 2: Traps (with Empty Sector logic)
        traps_map = self._generate_traps(xx, yy, (shelter_x, shelter_y), width, height)

        # 4. Layer 3: Noise (Turbulence & Domain Warping)
        noise_map = self._generate_noise(xx, yy)

        # 5. Combine all layers
        total_map_float = shelter_map + traps_map + noise_map

        # 6. Normalize the final map to a 0-255 scale
        normalized_map = self._normalize_to_255(total_map_float)

        # 7. Create and return the final TerrainMap object
        return TerrainMap(
            normalized_map,
            (shelter_px_x, shelter_px_y),
            self.config.START_ALTITUDE_THRESHOLD,
        )

    def _create_gaussian_basin(self, xx, yy, cx, cy, depth, width):
        """Helper to create a single negative gaussian (a valley)."""
        return -depth * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / width**2)

    def _generate_traps(self, xx, yy, shelter_coords, width, height):
        """Generates the trap layer, respecting the empty sector rule."""
        area = width * height
        num_traps_base = int(area * self.config.TRAP_DENSITY)
        num_traps = max(1, random.randint(num_traps_base - 1, num_traps_base + 2))

        traps_map = np.zeros_like(xx)
        shelter_x, shelter_y = shelter_coords

        # Define the 1 or 2 empty sectors (out of 8)
        empty_sector_1 = random.randint(0, 7)
        empty_sector_2 = (empty_sector_1 + 1) % 8

        for _ in range(num_traps):
            while True:
                # Find a valid position for the trap
                trap_x = random.uniform(-5, 5)
                trap_y = random.uniform(-5, 5)

                # Check if it's in the empty sector
                angle_to_shelter = np.arctan2(trap_y - shelter_y, trap_x - shelter_x)
                # Map angle from (-pi, pi) to (0, 2pi), then to sector (0-7)
                sector = int((angle_to_shelter + np.pi) / (np.pi / 4)) % 8

                if sector != empty_sector_1 and sector != empty_sector_2:
                    break  # Valid position found

            # Add the trap to the map
            trap_depth = random.uniform(
                self.config.SHELTER_DEPTH * self.config.TRAP_DEPTH_MIN_RATIO,
                self.config.SHELTER_DEPTH * self.config.TRAP_DEPTH_MAX_RATIO,
            )
            trap_width = random.uniform(
                self.config.TRAP_WIDTH_MIN, self.config.TRAP_WIDTH_MAX
            )
            traps_map += self._create_gaussian_basin(
                xx, yy, trap_x, trap_y, trap_depth, trap_width
            )

        return traps_map

    def _generate_noise(self, xx, yy):
        """Generates the complex, turbulent noise layer."""
        seed = random.randint(0, 100000)

        # Noise for the base terrain
        noise_base = PerlinNoise(octaves=self.config.NOISE_OCTAVES, seed=seed)

        # Noise for domain warping (if enabled)
        noise_warp_x = PerlinNoise(
            octaves=self.config.DOMAIN_WARP_OCTAVES, seed=seed + 1
        )
        noise_warp_y = PerlinNoise(
            octaves=self.config.DOMAIN_WARP_OCTAVES, seed=seed + 2
        )

        noise_map = np.zeros_like(xx)
        height, width = xx.shape

        freq = self.config.NOISE_FREQUENCY
        amp = self.config.NOISE_AMPLITUDE
        warp_enabled = self.config.DOMAIN_WARP_ENABLED
        warp_freq = self.config.DOMAIN_WARP_FREQUENCY
        warp_amp = self.config.DOMAIN_WARP_AMPLITUDE

        for y in range(height):
            for x in range(width):
                # Base coordinates
                nx = xx[y, x] * freq
                ny = yy[y, x] * freq

                # Apply domain warping (distort the coordinates)
                if warp_enabled:
                    warp_x_val = (
                        noise_warp_x([nx * warp_freq, ny * warp_freq]) * warp_amp
                    )
                    warp_y_val = (
                        noise_warp_y([nx * warp_freq, ny * warp_freq]) * warp_amp
                    )
                    nx += warp_x_val
                    ny += warp_y_val

                # Apply turbulence (absolute value of noise)
                # This creates the sharp ridges
                noise_val = abs(noise_base([nx, ny]))
                noise_map[y, x] = noise_val * amp

        return noise_map

    def _normalize_to_255(self, data):
        """Normalizes a float array to a uint8 array (0-255)."""
        min_val = np.min(data)
        max_val = np.max(data)

        if max_val == min_val:
            return np.full_like(data, 128, dtype=np.uint8)  # Avoid division by zero

        normalized = 255 * (data - min_val) / (max_val - min_val)
        return normalized.astype(np.uint8)
