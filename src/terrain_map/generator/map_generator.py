import numpy as np
import random
import noise
from terrain_map import TerrainMap
from .generator_config import generator_config

class MapGenerator:
    """
    Generates a TerrainMap by combining multiple layers of noise
    using the high-speed 'noise' (pynoise) C-accelerated library.
    """

    def __init__(self, config_override=None):
        self.config = generator_config
        if config_override:
            for key, value in config_override.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    print(f"Warning: Config override key '{key}' not found.")

        # 'noise' library is functional (no init needed)
        # Store a random base seed for this generator instance
        self.seed_x_offset = random.uniform(0, 1000)
        self.seed_y_offset = random.uniform(0, 1000)

    def generate(self, width, height):
        """
        The main public method. Generates and returns a new TerrainMap.
        """
        # 1. Create a coordinate grid
        xx, yy = np.meshgrid(
            np.linspace(-5, 5, width), np.linspace(-5, 5, height), indexing="ij"
        )

        # 2. Generate all noise layers
        wide_map = self._generate_wide_variations(xx, yy)
        traps_map = self._generate_traps(xx, yy, width, height)
        ridges_map = self._generate_ridges(xx, yy, width, height)
        detail_map = self._generate_detail_noise(xx, yy)

        # 3. Combine all layers
        total_map_float = wide_map + traps_map + ridges_map + detail_map

        # 4. Normalize the final map and create TerrainMap object
        normalized_map = self._normalize_to_255(total_map_float)

        return TerrainMap(normalized_map)

    def _generate_wide_variations(self, xx, yy):
        """Generates the base rolling hills."""
        noise_map = np.zeros_like(xx)
        freq = self.config.WIDE_VARIATION_FREQUENCY
        amp = self.config.WIDE_VARIATION_AMPLITUDE
        octaves = self.config.WIDE_VARIATION_OCTAVES

        it = np.nditer(
            [xx, yy, noise_map], op_flags=[["readonly"], ["readonly"], ["writeonly"]]
        )
        for x, y, z_out in it:
            z_out[...] = (
                noise.pnoise2(
                    float(x * freq) + self.seed_x_offset,
                    float(y * freq) + self.seed_y_offset,
                    octaves=octaves,
                )
                * amp
            )
        return noise_map

    def _create_warped_gaussian(self, xx, yy, cx, cy, amplitude, width):
        """
        Creates a single warped gaussian (positive or negative)
        using C-accelerated noise calculation.
        """
        warp_freq = self.config.BASIN_WARP_FREQUENCY
        warp_amp = self.config.BASIN_WARP_AMPLITUDE
        warp_octaves = self.config.BASIN_WARP_OCTAVES

        # --- Otimização: Pré-calcule coordenadas de ruído ---
        warp_points_x = xx * warp_freq
        warp_points_y = yy * warp_freq
        warp_points_x_offset = (xx + 10.0) * warp_freq  # Offset para ruído Y
        warp_points_y_offset = (yy + 10.0) * warp_freq

        x_warp_vals = np.zeros_like(xx)
        y_warp_vals = np.zeros_like(yy)

        it = np.nditer(
            [
                warp_points_x,
                warp_points_y,
                warp_points_x_offset,
                warp_points_y_offset,
                x_warp_vals,
                y_warp_vals,
            ],
            op_flags=[
                ["readonly"],
                ["readonly"],
                ["readonly"],
                ["readonly"],
                ["writeonly"],
                ["writeonly"],
            ],
        )

        # --- Loop é necessário, mas a função INTERNA é C-acelerada ---
        for wx, wy, wxo, wyo, x_out, y_out in it:
            x_out[...] = (
                noise.pnoise2(
                    float(wx) + self.seed_x_offset,
                    float(wy) + self.seed_y_offset,
                    octaves=warp_octaves,
                )
                * warp_amp
            )
            y_out[...] = (
                noise.pnoise2(
                    float(wxo) + self.seed_x_offset,
                    float(wyo) + self.seed_y_offset,
                    octaves=warp_octaves,
                )
                * warp_amp
            )

        xx_warped = xx + x_warp_vals
        yy_warped = yy + y_warp_vals

        safe_width_sq = max(width**2, 1e-6)
        return amplitude * np.exp(
            -((xx_warped - cx) ** 2 + (yy_warped - cy) ** 2) / safe_width_sq
        )

    def _generate_traps(self, xx, yy, width, height):
        """Generates the trap layer (negative features)."""
        area = width * height
        num_traps_base = int(area * self.config.TRAP_DENSITY)
        num_traps = max(1, random.randint(num_traps_base - 1, num_traps_base + 2))

        traps_map = np.zeros_like(xx)

        for _ in range(num_traps):
            trap_x, trap_y = random.uniform(-5, 5), random.uniform(-5, 5)
            depth = -random.uniform(
                self.config.TRAP_ABSOLUTE_DEPTH_MIN, self.config.TRAP_ABSOLUTE_DEPTH_MAX
            )
            width = random.uniform(
                self.config.TRAP_WIDTH_MIN, self.config.TRAP_WIDTH_MAX
            )

            traps_map += self._create_warped_gaussian(
                xx, yy, trap_x, trap_y, depth, width
            )
        return traps_map

    def _generate_ridges(self, xx, yy, width, height):
        """Generates the ridge layer (positive features)."""
        area = width * height
        num_ridges_base = int(area * self.config.RIDGE_DENSITY)
        num_ridges = max(1, random.randint(num_ridges_base - 1, num_ridges_base + 2))

        ridges_map = np.zeros_like(xx)

        for _ in range(num_ridges):
            ridge_x, ridge_y = random.uniform(-5, 5), random.uniform(-5, 5)
            height_val = random.uniform(
                self.config.RIDGE_ABSOLUTE_HEIGHT_MIN,
                self.config.RIDGE_ABSOLUTE_HEIGHT_MAX,
            )
            width = random.uniform(
                self.config.RIDGE_WIDTH_MIN, self.config.RIDGE_WIDTH_MAX
            )

            ridge_base = self._create_warped_gaussian(
                xx, yy, ridge_x, ridge_y, height_val, width
            )

            # --- Textura do cume ---
            ridge_texture_map = np.zeros_like(xx)
            freq = self.config.RIDGE_FREQUENCY
            amp = self.config.RIDGE_AMPLITUDE
            octaves = self.config.RIDGE_OCTAVES

            it = np.nditer(
                [xx, yy, ridge_texture_map],
                op_flags=[["readonly"], ["readonly"], ["writeonly"]],
            )
            for x, y, z_out in it:
                z_out[...] = noise.pnoise2(
                    float(x * freq) + self.seed_x_offset,
                    float(y * freq) + self.seed_y_offset,
                    octaves=octaves,
                )

            # Aplicar textura apenas onde o cume existe (valores > 0)
            ridge_mask = ridge_base > 0
            ridge_with_texture = ridge_base * (1.0 + ridge_texture_map * amp)
            ridges_map += np.where(ridge_mask, ridge_with_texture, ridge_base)

        return ridges_map

    def _generate_detail_noise(self, xx, yy):
        """Generates the fine-detail noise layer."""
        if self.config.DETAIL_NOISE_AMPLITUDE == 0:
            return 0.0

        noise_map = np.zeros_like(xx)
        freq = self.config.DETAIL_NOISE_FREQUENCY
        amp = self.config.DETAIL_NOISE_AMPLITUDE
        octaves = self.config.DETAIL_NOISE_OCTAVES

        it = np.nditer(
            [xx, yy, noise_map], op_flags=[["readonly"], ["readonly"], ["writeonly"]]
        )
        for x, y, z_out in it:
            z_out[...] = (
                noise.pnoise2(
                    float(x * freq) + self.seed_x_offset,
                    float(y * freq) + self.seed_y_offset,
                    octaves=octaves,
                )
                * amp
            )
        return noise_map

    def _normalize_to_255(self, data):
        """Normalizes the map to a 0-255 uint8 range."""
        min_val = np.min(data)
        max_val = np.max(data)

        scale = max_val - min_val
        if scale < 1e-9:
            return np.full_like(data, 128, dtype=np.uint8)

        normalized = 255 * (data - min_val) / scale
        return normalized.astype(np.uint8)
