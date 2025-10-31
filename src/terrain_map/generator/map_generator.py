import numpy as np
import random
from perlin_noise import PerlinNoise
from typing import Any, Dict, Optional, Tuple

from terrain_map import TerrainMap
from .generator_config import generator_config
from ._corridor_generator import CorridorGenerator


class MapGenerator:
    """
    Procedurally generates a more natural-looking TerrainMap.
    Hides the corridor by applying a uniform detail noise globally
    and only attenuating the traps within the corridor.
    """

    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        self.config: Any = generator_config
        if config_override:
            for key, value in config_override.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    print(f"Warning: Config override key '{key}' not found.")

        # Noise for warping basins
        self.warp_noise_x = PerlinNoise(
            octaves=self.config.BASIN_WARP_OCTAVES, seed=random.randint(0, 10000)
        )
        self.warp_noise_y = PerlinNoise(
            octaves=self.config.BASIN_WARP_OCTAVES, seed=random.randint(0, 10000)
        )
        # Corridor generator
        self.corridor_generator = CorridorGenerator(self.config)

    def generate(
        self, width: int, height: int
    ) -> Tuple[TerrainMap, np.ndarray[Any, np.dtype[np.float64]]]:
        """
        The main public method. Generates and returns a new TerrainMap and attenuation mask.
        """
        xx, yy = np.meshgrid(
            np.linspace(-5, 5, width), np.linspace(-5, 5, height), indexing="xy"
        )
        shelter_coords_logical: Tuple[float, float] = self._find_shelter_location(
            width, height
        )

        # 1. Generate base terrain (shelter + detail noise)
        shelter_map, detail_noise_map = self._generate_base_terrain(
            xx, yy, shelter_coords_logical
        )

        # 2. Generate the safe corridor mask (pathfinding on smooth map)
        attenuation_mask = self._generate_corridor_mask(
            width, height, xx, yy, shelter_coords_logical, shelter_map, detail_noise_map
        )

        # 3. Generate traps (full strength) and apply corridor attenuation
        attenuated_traps_map = self._generate_and_attenuate_traps(
            xx, yy, width, height, attenuation_mask
        )

        # 4. Combine all layers (Shelter + Attenuated Traps + Global Detail Noise)
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

    def _find_shelter_location(self, width: int, height: int) -> Tuple[float, float]:
        """Finds a random location for the shelter, respecting border constraints."""
        # Convert pixel distance to logical distance
        # The logical space is 10 units wide/high (-5 to 5)
        border_dist_x_logical = (
            self.config.SHELTER_BORDER_MIN_DISTANCE / (width - 1)
        ) * 10.0
        border_dist_y_logical = (
            self.config.SHELTER_BORDER_MIN_DISTANCE / (height - 1)
        ) * 10.0

        while True:
            # Generate coordinates within the allowed logical range
            shelter_x = random.uniform(
                -5 + border_dist_x_logical, 5 - border_dist_x_logical
            )
            shelter_y = random.uniform(
                -5 + border_dist_y_logical, 5 - border_dist_y_logical
            )
            # Also ensure shelter is somewhat near an edge (away from the center)
            if abs(shelter_x) + abs(shelter_y) > self.config.SHELTER_MIN_EDGE_DISTANCE:
                return shelter_x, shelter_y

    def _generate_base_terrain(
        self,
        xx: np.ndarray,
        yy: np.ndarray,
        shelter_coords_logical: Tuple[float, float],
    ) -> Tuple[np.ndarray, np.ndarray]:
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
        width: int,
        height: int,
        xx: np.ndarray,
        yy: np.ndarray,
        shelter_coords_logical: Tuple[float, float],
        shelter_map: np.ndarray,
        detail_noise_map: np.ndarray,
    ) -> np.ndarray:
        """Generates the attenuation mask for the safe corridor."""
        map_for_pathfinding = shelter_map  # Pathfind on smooth map
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

    def _generate_and_attenuate_traps(
        self,
        xx: np.ndarray,
        yy: np.ndarray,
        width: int,
        height: int,
        attenuation_mask: np.ndarray,
    ) -> np.ndarray:
        """Generates the trap map and applies the corridor attenuation."""
        # Generate traps at their full, original depth
        traps_map, _ = self._generate_traps(xx, yy, width, height)
        # Apply attenuation element-wise
        return traps_map * attenuation_mask

    def _combine_and_finalize_map(
        self,
        shelter_map: np.ndarray,
        traps_map: np.ndarray,
        detail_noise_map: np.ndarray,
        shelter_coords_logical: Tuple[float, float],
        width: int,
        height: int,
    ) -> Tuple[TerrainMap, Tuple[int, int]]:
        """Combines all map layers and normalizes them into a TerrainMap object."""
        # Simple summation: Base Sink + Weakened Traps + Global Noise Texture
        total_map_float = shelter_map + traps_map + detail_noise_map

        shelter_x_logical, shelter_y_logical = shelter_coords_logical
        shelter_px_x = int((shelter_x_logical + 5) / 10.0 * (width - 1))
        shelter_px_y = int((shelter_y_logical + 5) / 10.0 * (height - 1))
        shelter_px_x = np.clip(shelter_px_x, 0, width - 1)
        shelter_px_y = np.clip(shelter_px_y, 0, height - 1)
        shelter_idx = (shelter_px_y, shelter_px_x)

        normalized_map = self._normalize_to_255(total_map_float, shelter_idx)
        start_alt_abs = int(self.config.START_ALTITUDE_THRESHOLD_PERCENT * 255)

        terrain_map = TerrainMap(
            normalized_map, (shelter_px_x, shelter_px_y), start_alt_abs
        )
        return terrain_map, (shelter_px_x, shelter_px_y)

    def _create_warped_gaussian_basin(
        self,
        xx: np.ndarray,
        yy: np.ndarray,
        cx: float,
        cy: float,
        depth: float,
        width: float,
    ) -> np.ndarray:
        """Creates a negative gaussian with irregular edges."""
        warp_freq = self.config.BASIN_WARP_FREQUENCY
        warp_amp = self.config.BASIN_WARP_AMPLITUDE
        points = np.stack([xx.ravel() * warp_freq, yy.ravel() * warp_freq], axis=1)

        # Use loops as fallback for perlin-noise library
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
        safe_depth = max(0, depth)
        safe_width_sq = max(width**2, 1e-6)
        return -safe_depth * np.exp(
            -((xx_warped - cx) ** 2 + (yy_warped - cy) ** 2) / safe_width_sq
        )

    def _generate_traps(
        self, xx: np.ndarray, yy: np.ndarray, width: int, height: int
    ) -> Tuple[np.ndarray, list[Tuple[float, float]]]:
        """Generates the trap layer at FULL strength."""
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
            safe_trap_width = max(trap_width, 1e-6)
            traps_map += self._create_warped_gaussian_basin(
                xx, yy, trap_x, trap_y, base_trap_depth, safe_trap_width
            )
            trap_coords.append((trap_x, trap_y))
        return traps_map, trap_coords

    def _generate_detail_noise(self, xx: np.ndarray, yy: np.ndarray) -> np.ndarray:
        """Generates the fine-detail noise layer."""
        seed = random.randint(0, 100000)
        noise_base = PerlinNoise(octaves=self.config.DETAIL_NOISE_OCTAVES, seed=seed)
        noise_map = np.zeros_like(xx)
        freq = self.config.DETAIL_NOISE_FREQUENCY
        amp = self.config.DETAIL_NOISE_AMPLITUDE
        points = np.stack([xx.ravel() * freq, yy.ravel() * freq], axis=1)

        # Use loops as fallback for perlin-noise library
        noise_vals = np.array([noise_base(p.tolist()) for p in points]).reshape(
            xx.shape
        )

        noise_map = noise_vals * amp
        return noise_map

    def _normalize_to_255(
        self, data: np.ndarray, shelter_idx: Tuple[int, int]
    ) -> np.ndarray[Any, np.dtype[np.uint8]]:
        """Normalizes data ensuring the shelter is the minimum value."""
        shelter_idx = (
            np.clip(shelter_idx[0], 0, data.shape[0] - 1),
            np.clip(shelter_idx[1], 0, data.shape[1] - 1),
        )
        min_val = data[shelter_idx]
        max_val = np.max(data)

        if max_val <= min_val:
            if np.allclose(data, min_val):
                return np.full_like(data, 128, dtype=np.uint8)
            else:
                max_val, min_val = (
                    min_val,
                    max_val,
                )  # Swap if max is slightly lower due to noise

        scale = max_val - min_val
        if scale < 1e-9:
            return np.full_like(data, 128, dtype=np.uint8)

        normalized = 255 * (data - min_val) / scale
        normalized = np.clip(normalized, 0, 255)
        return normalized.astype(np.uint8)
