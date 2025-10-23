import numpy as np
import random
from perlin_noise import PerlinNoise
from terrain_map import TerrainMap
from .config_loader import generator_config

class MapGenerator:
    """
    Procedurally generates a more natural-looking TerrainMap.
    It uses coordinate warping for basins and noise masking for ridges
    to create organic, mountain-like features.
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

    def generate(self, width, height):
        """
        The main public method. Generates and returns a new TerrainMap.
        """
        # 1. Create a coordinate grid
        xx, yy = np.meshgrid(np.linspace(-5, 5, width), np.linspace(-5, 5, height))

        # 2. Layer 1: Dominant Basin (The Shelter) - now warped and irregular
        shelter_x = random.uniform(-3, 3)
        shelter_y = random.uniform(-3, 3)
        shelter_map = self._create_warped_gaussian_basin(
            xx,
            yy,
            shelter_x,
            shelter_y,
            self.config.SHELTER_DEPTH,
            self.config.SHELTER_WIDTH,
        )

        # 3. Layer 2: Traps (also warped for a natural look)
        traps_map, trap_coords = self._generate_traps(
            xx, yy, (shelter_x, shelter_y), width, height
        )

        # 4. Layer 3: Ridges (New noise-based method)
        ridge_map = self._generate_ridge_noise_layer(xx, yy)

        # 5. Layer 4: Fine Detail Noise (Reduced amplitude)
        detail_noise_map = self._generate_detail_noise(xx, yy)

        # 6. Combine all layers
        total_map_float = shelter_map + traps_map + ridge_map + detail_noise_map

        # 7. Find the true global minimum of the final combined map
        shelter_idx = np.unravel_index(
            np.argmin(total_map_float), total_map_float.shape
        )
        shelter_px_y, shelter_px_x = shelter_idx

        # 8. Normalize the final map
        normalized_map = self._normalize_to_255(total_map_float)

        # 9. Create and return the final TerrainMap object
        return TerrainMap(
            normalized_map,
            (shelter_px_x, shelter_px_y),
            self.config.START_ALTITUDE_THRESHOLD,
        )

    def _create_warped_gaussian_basin(self, xx, yy, cx, cy, depth, width):
        """
        Creates a negative gaussian (a valley) with irregular edges by
        warping the coordinates with Perlin noise before calculation.
        """
        # --- NEW: Coordinate Warping ---
        warp_freq = self.config.BASIN_WARP_FREQUENCY
        warp_amp = self.config.BASIN_WARP_AMPLITUDE

        # Generate warp values from noise
        x_warp_vals = np.zeros_like(xx)
        y_warp_vals = np.zeros_like(yy)

        # Vectorized noise calculation for performance
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

        # Apply the warp to the input coordinates
        xx_warped = xx + x_warp_vals
        yy_warped = yy + y_warp_vals
        # --- END NEW ---

        # Calculate the gaussian using the new warped coordinates
        return -depth * np.exp(
            -((xx_warped - cx) ** 2 + (yy_warped - cy) ** 2) / width**2
        )

    def _generate_ridge_noise_layer(self, xx, yy):
        """
        Generates mountain ranges using a noise-masking technique.
        A broad, smooth mask defines the location of ranges, and a detailed,
        sharp noise function creates the actual mountain texture within the mask.
        """
        ridge_map = np.zeros_like(xx)

        # --- 1. Generate the detailed mountain noise that will be masked ---
        ridge_noise = PerlinNoise(
            octaves=self.config.RIDGE_OCTAVES, seed=random.randint(0, 10000)
        )

        ridge_detail_map = np.zeros_like(xx)
        freq = self.config.RIDGE_FREQUENCY
        amp = self.config.RIDGE_AMPLITUDE

        # Vectorized noise calculation
        points = np.stack([xx.ravel() * freq, yy.ravel() * freq], axis=1)
        # Use abs() to create sharp "crests"
        # CORRECTED LINE: Added .tolist() to the noise call
        noise_vals = np.abs(
            np.array([ridge_noise(p.tolist()) for p in points])
        ).reshape(xx.shape)
        ridge_detail_map = noise_vals * amp

        # --- 2. Generate a smooth mask to control where mountains appear ---
        num_ranges = random.randint(
            self.config.RIDGE_RANGES_MIN, self.config.RIDGE_RANGES_MAX
        )
        ridge_mask = np.zeros_like(xx)

        for _ in range(num_ranges):
            cx, cy = random.uniform(-4, 4), random.uniform(-4, 4)
            length = random.uniform(
                self.config.RIDGE_MASK_LENGTH_MIN, self.config.RIDGE_MASK_LENGTH_MAX
            )
            width = random.uniform(
                self.config.RIDGE_MASK_WIDTH_MIN, self.config.RIDGE_MASK_WIDTH_MAX
            )
            angle = random.uniform(0, np.pi)  # No need for full 2*pi for ellipses

            cos_a, sin_a = np.cos(angle), np.sin(angle)
            x_rot = (xx - cx) * cos_a + (yy - cy) * sin_a
            y_rot = -(xx - cx) * sin_a + (yy - cy) * cos_a

            # Add a gentle, wide gaussian to the mask
            ridge_mask += np.exp(-((x_rot**2 / length**2) + (y_rot**2 / width**2)))

        # Clamp the mask so it acts as a multiplier from 0.0 to 1.0
        ridge_mask = np.clip(ridge_mask, 0, 1)

        # --- 3. Apply the mask to the detail noise ---
        return ridge_detail_map * ridge_mask

    def _generate_traps(self, xx, yy, shelter_coords, width, height):
        """
        Generates the trap layer, now using the warped basin function
        for more natural-looking traps.
        """
        area = width * height
        num_traps_base = int(area * self.config.TRAP_DENSITY)
        num_traps = max(1, random.randint(num_traps_base - 1, num_traps_base + 2))

        traps_map, trap_coords = np.zeros_like(xx), []
        shelter_x, shelter_y = shelter_coords

        empty_sector_1 = random.randint(0, 7)
        empty_sector_2 = (empty_sector_1 + 1) % 8

        for _ in range(num_traps):
            while True:
                trap_x, trap_y = random.uniform(-5, 5), random.uniform(-5, 5)
                angle = np.arctan2(trap_y - shelter_y, trap_x - shelter_x)
                sector = int((angle + np.pi) / (np.pi / 4)) % 8

                if sector != empty_sector_1 and sector != empty_sector_2:
                    break

            trap_depth = random.uniform(
                self.config.SHELTER_DEPTH * self.config.TRAP_DEPTH_MIN_RATIO,
                self.config.SHELTER_DEPTH * self.config.TRAP_DEPTH_MAX_RATIO,
            )
            trap_width = random.uniform(
                self.config.TRAP_WIDTH_MIN, self.config.TRAP_WIDTH_MAX
            )
            # Use the NEW warped function for natural traps
            traps_map += self._create_warped_gaussian_basin(
                xx, yy, trap_x, trap_y, trap_depth, trap_width
            )
            trap_coords.append((trap_x, trap_y))

        return traps_map, trap_coords

    def _generate_detail_noise(self, xx, yy):
        """
        Generates the fine-detail noise layer. This is the old _generate_noise
        but can be used with a lower amplitude for subtle texturing.
        """
        seed = random.randint(0, 100000)
        noise_base = PerlinNoise(octaves=self.config.DETAIL_NOISE_OCTAVES, seed=seed)

        noise_map = np.zeros_like(xx)
        freq = self.config.DETAIL_NOISE_FREQUENCY
        amp = self.config.DETAIL_NOISE_AMPLITUDE

        # Vectorized calculation is much faster
        points = np.stack([xx.ravel() * freq, yy.ravel() * freq], axis=1)
        # CORRECTED LINE: Added .tolist() to the noise call
        noise_vals = np.array([noise_base(p.tolist()) for p in points]).reshape(
            xx.shape
        )

        # Turbulence (absolute value) can be applied here too if desired
        noise_map = np.abs(noise_vals) * amp

        return noise_map

    def _normalize_to_255(self, data):
        """Normalizes a float array to a uint8 array (0-255)."""
        min_val, max_val = np.min(data), np.max(data)
        if max_val == min_val:
            return np.full_like(data, 128, dtype=np.uint8)
        normalized = 255 * (data - min_val) / (max_val - min_val)
        return normalized.astype(np.uint8)
