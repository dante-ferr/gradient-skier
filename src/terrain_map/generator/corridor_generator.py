import numpy as np
import random
from perlin_noise import PerlinNoise
from .config_loader import generator_config


class CorridorGenerator:
    """
    Generates a winding "safe corridor" attenuation mask.
    The mask values range from a minimum (inside the corridor) to 1.0 (outside).
    This mask is used by the MapGenerator to weaken the depth of traps
    that fall within the safe path, ensuring a solvable map.
    """

    def __init__(self, config=None):
        self.config = config if config else generator_config

        # Initialize the 1D noise generator for the path
        self.path_noise = PerlinNoise(
            octaves=self.config.CORRIDOR_NOISE_OCTAVES, seed=random.randint(0, 100000)
        )

    def _generate_path_polyline(self, start_point, end_point, num_steps=50):
        """
        Generates a list of points representing the winding path
        using 1D Perlin noise perpendicular to the main axis.
        """
        path_points = []

        # 1. Define the main axis (straight line)
        start_vec = np.array(start_point)
        end_vec = np.array(end_point)
        main_axis_vec = end_vec - start_vec

        # 2. Define the perpendicular vector
        # V = (x, y) -> V_perp = (-y, x)
        perp_vec = np.array([-main_axis_vec[1], main_axis_vec[0]])
        perp_vec = perp_vec / (np.linalg.norm(perp_vec) + 1e-6)  # Normalize

        freq = self.config.CORRIDOR_FREQUENCY
        amp = self.config.CORRIDOR_AMPLITUDE

        for i in range(num_steps + 1):
            t = i / num_steps

            # 3. Get the point on the straight line
            current_point_on_axis = start_vec + main_axis_vec * t

            # 4. Get the 1D noise value based on progress 't'
            # We multiply t by frequency to control the "waviness"
            noise_val = self.path_noise(t * freq)

            # 5. Calculate the displacement along the perpendicular vector
            displacement = perp_vec * noise_val * amp

            # 6. The final point is the line point + displacement
            final_point = current_point_on_axis + displacement
            path_points.append(final_point)

        return path_points

    def _find_min_distance_to_polyline(self, xx, yy, polyline):
        """
        Calculates the minimum distance from each point in the grid (xx, yy)
        to the generated polyline (the corridor's centerline).
        This is a performance-intensive operation.
        """
        height, width = xx.shape
        # Flatten the coordinate grids for easier iteration
        points = np.stack([xx.ravel(), yy.ravel()], axis=1)

        min_dists_sq = np.full(points.shape[0], np.inf)

        # Iterate over each line segment in the polyline
        for i in range(len(polyline) - 1):
            p1 = polyline[i]
            p2 = polyline[i + 1]

            # Calculate segment vector and its squared length
            seg_vec = p2 - p1
            seg_len_sq = np.dot(seg_vec, seg_vec)

            if seg_len_sq < 1e-6:
                # Segment is a point, calculate distance to p1
                dists_sq = np.sum((points - p1) ** 2, axis=1)
            else:
                # Project all grid points onto the line defined by the segment
                # t = dot(P - P1, P2 - P1) / |P2 - P1|^2
                vec_p1_to_points = points - p1
                t = np.dot(vec_p1_to_points, seg_vec) / seg_len_sq

                # Clamp t to [0, 1] to stay within the segment
                t_clamped = np.clip(t, 0, 1)

                # Calculate the closest point on the segment
                closest_points = p1 + t_clamped[:, np.newaxis] * seg_vec

                # Calculate squared distance from grid points to closest points
                dists_sq = np.sum((points - closest_points) ** 2, axis=1)

            # Update the minimum distance found so far for each point
            min_dists_sq = np.minimum(min_dists_sq, dists_sq)

        # Reshape the distances back to the grid shape
        return np.sqrt(min_dists_sq).reshape(xx.shape)

    def _get_best_start_point(self, width, height, preliminary_map, xx, yy):
        """
        Finds a suitable start point by scanning the entire map border for points
        that exceed the altitude threshold.
        """
        # 1. Normalize the preliminary map to a 0-1 range for threshold comparison
        map_min, map_max = np.min(preliminary_map), np.max(preliminary_map)
        if map_max <= map_min:
            # Flat map, any point is fine. Pick a random one.
            return self._get_random_border_point()

        norm_map = (preliminary_map - map_min) / (map_max - map_min)
        altitude_threshold = self.config.CORRIDOR_START_ALTITUDE_THRESHOLD

        # 2. Find all border pixels that are above the threshold
        valid_border_pixels = []
        # Top and Bottom edges
        for y in [0, height - 1]:
            for x in range(width):
                if norm_map[y, x] >= altitude_threshold:
                    valid_border_pixels.append((y, x))
        # Left and Right edges (excluding corners already checked)
        for x in [0, width - 1]:
            for y in range(1, height - 1):
                if norm_map[y, x] >= altitude_threshold:
                    valid_border_pixels.append((y, x))

        # 3. Choose a start point
        if valid_border_pixels:
            # We found suitable points, pick one randomly
            chosen_y, chosen_x = random.choice(valid_border_pixels)
            # Convert pixel coordinates back to logical coordinates
            start_point = (xx[chosen_y, chosen_x], yy[chosen_y, chosen_x])
            return start_point
        else:
            # Fallback: No points met the threshold.
            # Pick a random point on the border as a last resort.
            # This ensures a path is always generated.
            return self._get_random_border_point()

    def _pixel_to_logical(self, px_x, px_y, width, height):
        """Converts pixel coordinates (0 to width-1) to logical coordinates (-5 to 5)."""
        logic_x = (px_x / (width - 1)) * 10.0 - 5.0
        logic_y = (px_y / (height - 1)) * 10.0 - 5.0
        return (logic_x, logic_y)

    def _get_random_border_point(self):
        """Generates a single random point on the logical border."""
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            return (random.uniform(-4, 4), 5.0)
        elif edge == "bottom":
            return (random.uniform(-4, 4), -5.0)
        elif edge == "left":
            return (-5.0, random.uniform(-4, 4))
        else:  # 'right'
            return (5.0, random.uniform(-4, 4))

    def generate_attenuation_mask(
        self, width, height, xx, yy, shelter_coords, preliminary_map
    ):
        """
        Public method to generate the full attenuation mask.
        """
        start_point = self._get_best_start_point(width, height, preliminary_map, xx, yy)
        end_point = shelter_coords  # The logical (x, y) of the shelter

        # 2. Generate the winding path
        polyline = self._generate_path_polyline(start_point, end_point)

        # 3. Calculate distance from every pixel to this path
        distance_map = self._find_min_distance_to_polyline(xx, yy, polyline)

        # 4. Convert distance map to attenuation mask
        # Use a smooth transition (e.g., sigmoid or smoothstep)
        # Here, we use a simple linear ramp with clipping

        corridor_width = self.config.CORRIDOR_WIDTH
        min_strength = self.config.CORRIDOR_MIN_STRENGTH

        # Scale distances by the corridor width
        # t = 0 inside corridor, t = 1 at edge, t > 1 outside
        t = distance_map / corridor_width

        # Apply linear interpolation: val = min_strength + (1.0 - min_strength) * t
        mask = min_strength + (1.0 - min_strength) * t

        # Clamp the mask to a maximum of 1.0
        np.clip(mask, min_strength, 1.0, out=mask)

        return mask
