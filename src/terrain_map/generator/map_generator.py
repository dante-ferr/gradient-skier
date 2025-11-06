import numpy as np
import random
from perlin_noise import PerlinNoise
from typing import Any, Dict, Optional, Tuple
from terrain_map import TerrainMap
from .generator_config import generator_config
from ._corridor_generator import CorridorGenerator


class MapGenerator:
    """
    Generates a TerrainMap with a smooth, safe corridor,
    featuring a central ravine, a trap-free shelf, and
    attenuated outer walls.
    """

    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        self.config: Any = generator_config
        if config_override:
            for key, value in config_override.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    print(f"Warning: Config override key '{key}' not found.")

        self.warp_noise_x = PerlinNoise(
            octaves=self.config.BASIN_WARP_OCTAVES, seed=random.randint(0, 10000)
        )
        self.warp_noise_y = PerlinNoise(
            octaves=self.config.BASIN_WARP_OCTAVES, seed=random.randint(0, 10000)
        )
        self.corridor_generator = CorridorGenerator(self.config)

    def generate(
        self, width: int, height: int
    ) -> Tuple[TerrainMap, np.ndarray[Any, np.dtype[np.float64]]]:
        """
        The main public method. Generates and returns a new TerrainMap and the trap mask.
        """
        xx, yy = np.meshgrid(
            np.linspace(-5, 5, width), np.linspace(-5, 5, height), indexing="xy"
        )
        shelter_coords_logical: Tuple[float, float] = self._find_shelter_location(
            width, height
        )

        # 1. Generate shelter map and detail noise
        shelter_map, detail_noise_map = self._generate_base_terrain(
            xx, yy, shelter_coords_logical
        )

        # 2. Generate the FULL strength trap map (will be used later)
        traps_map_full, _ = self._generate_traps(xx, yy, width, height)

        # --- FIX: Reverted to original logic ---
        # 3. Create the maps for the corridor generator

        # The pathfinding map is smooth (no traps)
        map_for_pathfinding = shelter_map
        # The start search map *only* uses the shelter basin and noise.
        # This correctly finds the "high ground" (0.0 plane) far from the shelter.
        map_for_start_search = shelter_map + detail_noise_map

        # 4. Generate corridor masks using the correct maps
        trap_attenuation_mask, ravine_carve_mask = self._generate_corridor_masks(
            width,
            height,
            xx,
            yy,
            shelter_coords_logical,
            map_for_pathfinding,
            map_for_start_search,  # <-- This map is now correct again
        )
        # --- END FIX ---

        # 5. Attenuate the traps using the mask
        attenuated_traps_map = traps_map_full * trap_attenuation_mask

        # 6. Combine map and carve ravine
        final_map, shelter_coords_pixel = self._combine_and_finalize_map(
            shelter_map,
            attenuated_traps_map,  # Pass the attenuated map
            detail_noise_map,
            shelter_coords_logical,
            width,
            height,
            ravine_carve_mask,  # Pass the ravine mask
        )

        # Return the map and the trap mask (useful for debug)
        return (
            final_map,
            trap_attenuation_mask,
        )

    def _find_shelter_location(self, width: int, height: int) -> Tuple[float, float]:
        """Finds a random location for the shelter, respecting border constraints."""
        border_dist_x_logical = (
            self.config.SHELTER_BORDER_MIN_DISTANCE / (width - 1)
        ) * 10.0
        border_dist_y_logical = (
            self.config.SHELTER_BORDER_MIN_DISTANCE / (height - 1)
        ) * 10.0

        while True:
            shelter_x = random.uniform(
                -5 + border_dist_x_logical, 5 - border_dist_x_logical
            )
            shelter_y = random.uniform(
                -5 + border_dist_y_logical, 5 - border_dist_y_logical
            )
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

        shelter_map = self._create_flat_shelter_basin(
            xx,
            yy,
            shelter_x,
            shelter_y,
            self.config.SHELTER_DEPTH,
            self.config.SHELTER_WIDTH,
        )

        detail_noise_map = self._generate_detail_noise(xx, yy)
        return shelter_map, detail_noise_map

    def _generate_corridor_masks(
        self,
        width: int,
        height: int,
        xx: np.ndarray,
        yy: np.ndarray,
        shelter_coords_logical: Tuple[float, float],
        map_for_pathfinding: np.ndarray,
        map_for_start_search: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates the corridor shape masks.
        """
        return self.corridor_generator.generate_corridor_masks(
            width,
            height,
            xx,
            yy,
            shelter_coords_logical,
            map_for_pathfinding,
            map_for_start_search,
        )

    # Note: _generate_and_attenuate_traps was removed as its logic
    # was correctly moved into the main generate() method.

    def _combine_and_finalize_map(
        self,
        shelter_map: np.ndarray,
        traps_map: np.ndarray,
        detail_noise_map: np.ndarray,
        shelter_coords_logical: Tuple[float, float],
        width: int,
        height: int,
        ravine_carve_mask: np.ndarray,  # Receives the carve mask
    ) -> Tuple[TerrainMap, Tuple[int, int]]:
        """
        Combines all map layers, smoothly carves the ravine, and normalizes.
        """
        ravine_depth = getattr(self.config, "CORRIDOR_RAVINE_DEPTH", 0.0)

        ravine_map = ravine_carve_mask * ravine_depth

        shelter_min_depth = -self.config.SHELTER_DEPTH

        shelter_wall_mask = np.where(shelter_map > shelter_min_depth + 1e-9, 1.0, 0.0)

        safe_ravine_map = ravine_map * shelter_wall_mask

        total_map_float = shelter_map + traps_map + detail_noise_map - safe_ravine_map

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

    def _create_flat_shelter_basin(
        self,
        xx: np.ndarray,
        yy: np.ndarray,
        cx: float,
        cy: float,
        depth: float,
        width: float,  # This 'width' is treated as the total radius of the basin
    ) -> np.ndarray:
        """
        Creates a negative basin with a flat bottom and smooth walls,
        using the same logic as the corridor generator.
        """
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
        safe_depth = max(0, depth)

        flat_ratio = getattr(self.config, "SHELTER_FLAT_BOTTOM_RATIO", 0.1)
        sharpness = getattr(self.config, "SHELTER_WALL_SHARPNESS", 2.0)
        total_radius = max(width, 1e-6)

        distance = np.sqrt((xx_warped - cx) ** 2 + (yy_warped - cy) ** 2)
        flat_radius = total_radius * flat_ratio

        wall_width = total_radius * (1.0 - flat_ratio)
        denominator = wall_width if wall_width > 1e-9 else 1.0

        numerator = np.clip(distance - flat_radius, 0.0, wall_width)
        t_remapped = numerator / denominator

        strength_factor = 1.0 - (1.0 - t_remapped) ** sharpness

        final_map = -safe_depth * (1.0 - strength_factor)

        return final_map

    def _create_warped_gaussian_basin(
        self,
        xx: np.ndarray,
        yy: np.ndarray,
        cx: float,
        cy: float,
        depth: float,
        width: float,
    ) -> np.ndarray:
        """Creates a negative gaussian with irregular edges (for traps)."""
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

        if amp == 0.0 or freq == 0.0:
            return noise_map

        points = np.stack([xx.ravel() * freq, yy.ravel() * freq], axis=1)

        noise_vals = np.array([noise_base(p.tolist()) for p in points]).reshape(
            xx.shape
        )

        noise_map = noise_vals * amp
        return noise_map

    def _normalize_to_255(
        self, data: np.ndarray, shelter_idx: Tuple[int, int]
    ) -> np.ndarray[Any, np.dtype[np.uint8]]:
        """
        Normalizes data, **forcing** the shelter_idx to be the minimum value (0).
        """
        shelter_idx = (
            np.clip(shelter_idx[0], 0, data.shape[0] - 1),
            np.clip(shelter_idx[1], 0, data.shape[1] - 1),
        )

        min_val = data[shelter_idx]
        max_val = np.max(data)

        if max_val <= min_val:
            if np.allclose(data, min_val):
                return np.full_like(data, 128, dtype=np.uint8)
            min_val, max_val = max_val, min_val

        scale = max_val - min_val
        if scale < 1e-9:
            return np.full_like(data, 128, dtype=np.uint8)

        normalized = 255 * (data - min_val) / scale
        normalized = np.clip(normalized, 0, 255)
        return normalized.astype(np.uint8)
