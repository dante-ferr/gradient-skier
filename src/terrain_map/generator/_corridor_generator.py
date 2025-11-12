import numpy as np
import random
from perlin_noise import PerlinNoise
from .generator_config import generator_config


class CorridorGenerator:
    """
    Generates a winding "safe corridor" attenuation mask using a
    simplified and robust "Drunk Walker" algorithm. It prioritizes
    reaching the target while adding controlled lateral wobble.
    """

    def __init__(self, config=None):
        self.config = config if config else generator_config
        self.wobble_noise = PerlinNoise(
            octaves=self.config.CORRIDOR_WOBBLE_OCTAVES, seed=random.randint(0, 100000)
        )

    def _get_gradient_at_point(self, terrain_map, px, py):
        """Calculates the gradient (df/dx, df/dy) at a single pixel."""
        height, width = terrain_map.shape
        px = np.clip(px, 0, width - 1)
        py = np.clip(py, 0, height - 1)
        px_plus_1 = min(px + 1, width - 1)
        px_minus_1 = max(px - 1, 0)
        py_plus_1 = min(py + 1, height - 1)
        py_minus_1 = max(py - 1, 0)
        dx = px_plus_1 - px_minus_1
        dy = py_plus_1 - py_minus_1
        grad_x_val_plus = terrain_map[py, px_plus_1]
        grad_x_val_minus = terrain_map[py, px_minus_1]
        grad_y_val_plus = terrain_map[py_plus_1, px]
        grad_y_val_minus = terrain_map[py_minus_1, px]
        grad_x = (grad_x_val_plus - grad_x_val_minus) / (dx if dx > 1e-6 else 1.0)
        grad_y = (grad_y_val_plus - grad_y_val_minus) / (dy if dy > 1e-6 else 1.0)
        return np.array([grad_x, grad_y])

    def _normalize_vec(self, vec, epsilon=1e-9):
        """Helper to safely normalize a vector."""
        norm = np.linalg.norm(vec)
        if norm < epsilon:
            return np.array([0.0, 0.0])
        return vec / norm

    def _logical_to_pixel(self, logical_point, width, height):
        """Converts a logical coordinate (-5 to 5) to a pixel coordinate."""
        px = int((logical_point[0] + 5) / 10.0 * (width - 1))
        py = int((logical_point[1] + 5) / 10.0 * (height - 1))
        px = np.clip(px, 0, width - 1)
        py = np.clip(py, 0, height - 1)
        return px, py

    def _calculate_dynamic_weights(self, distance_to_target):
        """
        Calculates the dynamic strengths of the forces acting on the walker
        based on its distance to the target.
        """
        falloff_factor = np.clip(
            distance_to_target / self.config.CORRIDOR_LOCKON_RANGE, 0.0, 1.0
        )
        wobble_strength = self.config.CORRIDOR_WOBBLE_STRENGTH * falloff_factor
        magnet_strength = self.config.CORRIDOR_MAGNET_STRENGTH + (
            self.config.CORRIDOR_LOCKON_STRENGTH * (1.0 - falloff_factor)
        )
        gravity_strength = self.config.CORRIDOR_GRAVITY_STRENGTH
        return wobble_strength, magnet_strength, gravity_strength

    def _calculate_forces(self, current_point, target_point, preliminary_map, px, py):
        """Calculates the gravity, magnet, and wobble force vectors."""
        gravity_vec = self._normalize_vec(
            -self._get_gradient_at_point(preliminary_map, px, py)
        )
        magnet_vec = self._normalize_vec(target_point - current_point)
        wob_freq = self.config.CORRIDOR_WOBBLE_FREQUENCY
        noise_val = self.wobble_noise(
            [current_point[0] * wob_freq, current_point[1] * wob_freq]
        )
        wobble_direction = np.array([magnet_vec[1], -magnet_vec[0]])
        wobble_vec = wobble_direction * noise_val
        return gravity_vec, magnet_vec, wobble_vec

    def _update_walker_position(self, current_point, forces, weights):
        """Combines forces and moves the walker one step."""
        gravity_vec, magnet_vec, wobble_vec = forces
        wobble_strength, magnet_strength, gravity_strength = weights
        primary_direction = (gravity_vec * gravity_strength) + (
            magnet_vec * magnet_strength
        )
        combined_force = self._normalize_vec(
            self._normalize_vec(primary_direction) + (wobble_vec * wobble_strength)
        )
        move_direction = (
            combined_force if np.linalg.norm(combined_force) > 1e-9 else magnet_vec
        )
        return current_point + move_direction * self.config.CORRIDOR_STEP_SIZE

    def _generate_gradient_path(
        self, start_point, end_point, preliminary_map, width, height
    ):
        """
        Simulates the path using a robust approach combining base direction and wobble.
        """
        path_points = [np.array(start_point)]
        current_point = np.array(start_point)
        target_point = np.array(end_point)

        for step in range(self.config.CORRIDOR_MAX_STEPS):
            distance_to_target = np.linalg.norm(target_point - current_point)
            if distance_to_target < self.config.CORRIDOR_STEP_SIZE:
                path_points.append(target_point.copy())
                break

            px, py = self._logical_to_pixel(current_point, width, height)
            weights = self._calculate_dynamic_weights(distance_to_target)
            forces = self._calculate_forces(
                current_point, target_point, preliminary_map, px, py
            )
            current_point = self._update_walker_position(current_point, forces, weights)
            current_point = np.clip(current_point, -5.0, 5.0)
            path_points.append(current_point.copy())

        if step == self.config.CORRIDOR_MAX_STEPS - 1:
            print(
                f"Warning: Corridor generation reached max steps ({self.config.CORRIDOR_MAX_STEPS})."
            )
            if not np.allclose(path_points[-1], target_point):
                path_points.append(target_point.copy())
        return path_points

    def _find_min_distance_to_polyline(self, xx, yy, polyline):
        points = np.stack([xx.ravel(), yy.ravel()], axis=1)
        min_dists_sq = np.full(points.shape[0], np.inf)
        if len(polyline) < 2:
            return np.sqrt(min_dists_sq).reshape(xx.shape)

        for i in range(len(polyline) - 1):
            p1, p2 = polyline[i], polyline[i + 1]
            seg_vec = p2 - p1
            seg_len_sq = np.dot(seg_vec, seg_vec)
            if seg_len_sq < 1e-9:
                continue

            vec_p1_to_points = points - p1
            t = np.dot(vec_p1_to_points, seg_vec) / seg_len_sq
            t_clamped = np.clip(t, 0.0, 1.0)
            closest_points = p1 + t_clamped[:, np.newaxis] * seg_vec
            dists_sq = np.sum((points - closest_points) ** 2, axis=1)
            min_dists_sq = np.minimum(min_dists_sq, dists_sq)
        return np.sqrt(min_dists_sq).reshape(xx.shape)

    def _find_best_start_point(self, preliminary_map, width, height):
        """
        Finds a suitable starting point for the corridor path, prioritizing high-altitude
        points on the map's border.
        """
        lower_threshold = (
            np.max(preliminary_map) * self.config.START_ALTITUDE_THRESHOLD_PERCENT
        )
        upper_threshold = (
            np.max(preliminary_map) * self.config.CORRIDOR_MAX_START_THRESHOLD
        )

        candidate_pixels = np.argwhere(
            (
                preliminary_map >= lower_threshold
            )  # & (preliminary_map <= upper_threshold)
        )

        if candidate_pixels.size > 0:
            py, px = random.choice(candidate_pixels)
        else:
            py, px = np.unravel_index(np.argmax(preliminary_map), preliminary_map.shape)

        logical_x = (px / (width - 1)) * 10.0 - 5.0
        logical_y = (py / (height - 1)) * 10.0 - 5.0
        return logical_x, logical_y

    def generate_corridor_masks(
        self,
        width,
        height,
        xx,
        yy,
        shelter_coords,
        map_for_pathfinding,
        map_for_start_search,
    ):
        """
        Generates two masks based on the corridor path:
        1. trap_attenuation_mask: (0.0 on flat bottom, 0-1 on walls, 1.0 outside)
        2. ravine_carve_mask: (1.0 on ravine bottom, 1-0 on ravine walls, 0.0 on shelf/outside)
        """
        start_point = self._find_best_start_point(map_for_start_search, width, height)
        polyline = self._generate_gradient_path(
            start_point, shelter_coords, map_for_pathfinding, width, height
        )
        distance_map = self._find_min_distance_to_polyline(xx, yy, polyline)

        t = distance_map / self.config.CORRIDOR_WIDTH

        # --- 1. Calculate Trap Attenuation Mask (Wide) ---

        trap_sharpness = getattr(self.config, "CORRIDOR_WALL_SHARPNESS", 3.0)
        trap_flat_t = np.clip(
            getattr(self.config, "CORRIDOR_FLAT_BOTTOM_RATIO", 0.4), 0.0, 0.999
        )

        denominator_trap = 1.0 - trap_flat_t

        # --- FIX IS HERE ---
        # We must clip the remapped 't' to be between 0.0 and 1.0
        # to avoid taking a fractional power of a negative number.
        numerator_trap = np.clip(t - trap_flat_t, 0.0, denominator_trap)
        t_remapped_trap = numerator_trap / (
            denominator_trap if denominator_trap > 1e-9 else 1.0
        )
        # --- END FIX ---

        strength_factor_trap = 1.0 - (1.0 - t_remapped_trap) ** trap_sharpness
        trap_attenuation_mask = np.clip(strength_factor_trap, 0.0, 1.0)

        # --- 2. Calculate Ravine Carve Mask (Narrow) ---

        ravine_sharpness = getattr(
            self.config, "CORRIDOR_RAVINE_WALL_SHARPNESS", trap_sharpness
        )
        ravine_shelf_ratio = np.clip(
            getattr(self.config, "CORRIDOR_RAVINE_SHELF_RATIO", 0.6), 0.0, 1.0
        )

        ravine_flat_t = trap_flat_t * ravine_shelf_ratio

        denominator_ravine = trap_flat_t - ravine_flat_t

        # --- FIX IS HERE ---
        # Same fix as above, for the ravine wall.
        numerator_ravine = np.clip(t - ravine_flat_t, 0.0, denominator_ravine)
        t_remapped_ravine = numerator_ravine / (
            denominator_ravine if denominator_ravine > 1e-9 else 1.0
        )
        # --- END FIX ---

        strength_factor_ravine = 1.0 - (1.0 - t_remapped_ravine) ** ravine_sharpness
        strength_factor_ravine = np.clip(strength_factor_ravine, 0.0, 1.0)

        # Force values outside the safe platform to be 1.0 (no carving)
        strength_factor_ravine = np.where(t >= trap_flat_t, 1.0, strength_factor_ravine)

        # Invert to create the carve mask
        ravine_carve_mask = 1.0 - strength_factor_ravine

        return trap_attenuation_mask, ravine_carve_mask
