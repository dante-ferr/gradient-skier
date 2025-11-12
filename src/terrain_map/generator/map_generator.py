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
            map_for_pathfinding,
        )

        # 5. Attenuate the traps using the mask
        attenuated_traps_map = traps_map_full * trap_attenuation_mask

        # 6. Combine map and carve ravine
        final_map, shelter_coords_pixel = self._combine_and_finalize_map(
            shelter_map,
            traps_map_full,
            trap_attenuation_mask,
            detail_noise_map,
            shelter_coords_logical,
            width,
            height,
            ravine_carve_mask,  # Pass the ravine mask
        )

        final_map.attenuation_mask = trap_attenuation_mask

        # Return the map and the trap mask (useful for debug)
        return (
            final_map,
            trap_attenuation_mask,
        )

    def _find_shelter_location(self, width: int, height: int) -> Tuple[float, float]:
        """
        Finds a shelter location in one of the four corner areas, respecting a
        minimum distance from the map borders, without using loops.
        """
        # Calculate a logical border distance from the pixel-based config value.
        # This creates a "padding" from the absolute edges of the map.
        border_dist_x = (self.config.SHELTER_BORDER_MIN_DISTANCE / (width - 1)) * 10.0
        border_dist_y = (self.config.SHELTER_BORDER_MIN_DISTANCE / (height - 1)) * 10.0

        # Define the logical space limits, inset by the border distance.
        max_x = 5.0 - border_dist_x
        max_y = 5.0 - border_dist_y

        # The four corners of the logical map (-5 to 5)
        corners = [(5.0, 5.0), (-5.0, 5.0), (-5.0, -5.0), (5.0, -5.0)]
        # Choose one of the four corner regions randomly
        corner_x, corner_y = random.choice(corners)

        # Generate a random point within a unit triangle to ensure uniform distribution.
        u, v = random.random(), random.random()
        if u + v > 1.0:
            u = 1.0 - u
            v = 1.0 - v

        # Map the point to the chosen corner area.
        # This places the point within the diamond defined by (0,0) and the corner.
        # We then scale it to respect the border constraints.
        shelter_x = (corner_x - u * corner_x) * (max_x / 5.0)
        shelter_y = (corner_y - v * corner_y) * (max_y / 5.0)

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
            self.config.SHELTER_WIDTH,  # This param is now ignored
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
        traps_map_full: np.ndarray,  # <-- ADICIONE (mapa de armadilhas 100%)
        trap_attenuation_mask: np.ndarray,  # <-- ADICIONE (máscara da forma do corredor)
        detail_noise_map: np.ndarray,
        shelter_coords_logical: Tuple[float, float],
        width: int,
        height: int,
        ravine_carve_mask: np.ndarray,
    ) -> Tuple[TerrainMap, Tuple[int, int]]:
        """
        Combines all map layers, smoothly carves the ravine, and normalizes.
        """
        ravine_depth = getattr(self.config, "CORRIDOR_RAVINE_DEPTH", 0.0)
        ravine_map = ravine_carve_mask * ravine_depth

        max_height_ratio = np.clip(
            getattr(self.config, "CORRIDOR_RAVINE_MAX_HEIGHT_RATIO", 1.0), 0.0, 1.0
        )
        feather_height = getattr(
            self.config, "CORRIDOR_RAVINE_FEATHER_HEIGHT", 1.0
        )  # Novo parâmetro

        shelter_floor = -self.config.SHELTER_DEPTH  # ex: -10.0
        shelter_total_height = self.config.SHELTER_DEPTH  # ex: 10.0

        # Calcula a altitude máxima onde a ravina ainda tem força total (100%)
        # Ex: se ratio = 0.4 (-6.0), a ravina é total até -6.0
        max_altitude_full_ravine = shelter_floor + (
            shelter_total_height * max_height_ratio
        )

        # Calcula a altitude onde a ravina começa a desvanecer
        # Ex: se feather_height = 1.0, começa a desvanecer 1 unidade acima de max_altitude_full_ravine
        # então se max_altitude_full_ravine = -6.0, feather_start_altitude = -5.0
        feather_start_altitude = max_altitude_full_ravine + feather_height

        # Garante que feather_start_altitude não passe de 0.0 (o plano superior)
        feather_start_altitude = min(
            feather_start_altitude, -1e-9
        )  # Mantenha abaixo de 0 para não afetar o plano superior

        # --- NOVA LÓGICA DE SUAVIZAÇÃO ---
        # Calculamos um 't' que vai de 0.0 a 1.0 na zona de transição

        # Clipa a altura do abrigo para a zona de desvanecimento
        # t = 0.0 na altura de inicio do desvanecimento (feather_start_altitude)
        # t = 1.0 na altura máxima da ravina (max_altitude_full_ravine)
        transition_factor = (shelter_map - feather_start_altitude) / (
            max_altitude_full_ravine - feather_start_altitude + 1e-9
        )

        # Garante que t esteja entre 0 e 1, e que seja 1.0 abaixo da max_altitude_full_ravine
        transition_factor = np.clip(transition_factor, 0.0, 1.0)

        # Aplica uma função de suavização (smoothstep)
        # smoothstep(t) = t*t*(3 - 2*t)
        # Isso cria uma curva "S" para o desvanecimento
        # Ou simplesmente use `transition_factor` diretamente se quiser uma atenuação linear
        smooth_transition_mask = (
            transition_factor * transition_factor * (3 - 2 * transition_factor)
        )

        # A máscara final para a ravina agora é essa transição suave
        shelter_wall_mask = smooth_transition_mask

        # 1. A ravina é atenuada pela altitude (como antes)
        safe_ravine_map = ravine_map * shelter_wall_mask

        # 2. A REMOÇÃO de armadilhas também é atenuada pela altitude
        # trap_attenuation_mask é 0.0 no caminho, 1.0 fora.
        # (1.0 - trap_attenuation_mask) é 1.0 no caminho, 0.0 fora.
        # Este é o "poder de remoção de armadilha" do corredor.
        trap_removal_power = 1.0 - trap_attenuation_mask

        # Agora, faça esse poder de remoção desvanecer com a altitude
        altitude_adjusted_trap_removal = trap_removal_power * shelter_wall_mask

        # A máscara final de armadilha: 1.0 (total) menos a remoção ajustada
        # Fora do caminho: 1.0 - (0.0 * ...) = 1.0 (Armadilhas 100%)
        # No caminho (baixo): 1.0 - (1.0 * 1.0) = 0.0 (Armadilhas 0%)
        # No caminho (alto):  1.0 - (1.0 * 0.0) = 1.0 (Armadilhas 100%)
        # No caminho (meio):  1.0 - (1.0 * 0.5) = 0.5 (Armadilhas 50%)
        final_trap_mask = 1.0 - altitude_adjusted_trap_removal

        # 3. Aplique a máscara final de armadilhas
        final_attenuated_traps_map = traps_map_full * final_trap_mask

        # 4. Combine o mapa
        total_map_float = (
            shelter_map
            + final_attenuated_traps_map  # <-- Use o novo mapa de armadilhas
            + detail_noise_map
            - safe_ravine_map
        )

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
        width: float,  # This 'width' (config.SHELTER_WIDTH) is now IGNORED
    ) -> np.ndarray:
        """
        Creates a negative basin with a flat bottom and smooth, sigmoid-like walls.
        The basin spans the ENTIRE map, with walls scaling
        from the shelter to the map's furthest corner.
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

        # --- MODIFIED LOGIC ---
        # Calculate the distance from the shelter (cx, cy) to the
        # 4 corners of the logical map (which is from -5 to 5).
        corners_logical = [(-5.0, -5.0), (5.0, -5.0), (-5.0, 5.0), (5.0, 5.0)]

        max_dist_sq = 0.0
        for corner_x, corner_y in corners_logical:
            dist_sq = (cx - corner_x) ** 2 + (cy - corner_y) ** 2
            if dist_sq > max_dist_sq:
                max_dist_sq = dist_sq

        # This is the new total_radius, spanning the whole map
        # from the shelter to the furthest corner.
        total_radius = max(np.sqrt(max_dist_sq), 1e-6)
        # The original 'width' parameter (from config.SHELTER_WIDTH) is now ignored.
        # --- END MODIFIED LOGIC ---

        distance = np.sqrt((xx_warped - cx) ** 2 + (yy_warped - cy) ** 2)

        # The flat bottom radius is a small fraction of the new total_radius
        flat_radius = total_radius * flat_ratio

        # The wall width is the remaining 90% (or so) of the radius
        wall_width = total_radius * (1.0 - flat_ratio)
        denominator = wall_width if wall_width > 1e-9 else 1.0

        # Map distance from 0 (start of wall) to 1 (end of wall)
        numerator = np.clip(distance - flat_radius, 0.0, wall_width)
        t_remapped = numerator / denominator

        # This power function creates the "sigmoid-like" S-curve
        # strength_factor = 0.0 at t_remapped=0
        # strength_factor = 1.0 at t_remapped=1
        strength_factor = 1.0 - (1.0 - t_remapped) ** sharpness

        # The final map is flat (-depth) inside flat_radius,
        # then curves up to 0.0 at total_radius.
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
