import numpy as np
import json
import os
from typing import Any, Tuple
from PIL import Image
from scipy.ndimage import sobel

class TerrainMap:
    """
    Holds all data for a single generated map, including height and gradient fields.
    This class is "read-only" after creation.
    """

    def __init__(
        self,
        height_data: np.ndarray[Any, np.dtype[np.uint8]],
        shelter_coords: Tuple[int, int],
        start_altitude_threshold: int,
    ):
        """
        Initializes the map with all necessary data.
        Gradients are pre-calculated here for performance.

        Args:
            height_data (np.array): 2D NumPy array (uint8) representing map altitude (0-255).
            shelter_coords (tuple): (x, y) pixel coordinates of the global minimum (shelter).
            start_altitude_threshold (int): The minimum altitude (0-255) to be a valid start point.
        """
        self.height_data: np.ndarray[Any, np.dtype[np.uint8]] = height_data
        self.shelter_coords: Tuple[int, int] = shelter_coords
        self.start_altitude_threshold: int = start_altitude_threshold

        self.width: int = self.height_data.shape[1]
        self.height: int = self.height_data.shape[0]

        map_float: np.ndarray[Any, np.dtype[np.float32]] = self.height_data.astype(
            np.float32
        )

        # self.gradient_y corresponds to df/dy (changes along axis 0)
        self.gradient_y: np.ndarray = sobel(map_float, axis=0)
        # self.gradient_x corresponds to df/dx (changes along axis 1)
        self.gradient_x: np.ndarray = sobel(map_float, axis=1)

    def get_gradient_at(self, x: int, y: int) -> np.ndarray:
        """
        Gets the pre-calculated gradient vector [df/dx, df/dy] at a specific pixel.
        Assumes integer coordinates.

        Args:
            x (int): The x-coordinate (column).
            y (int): The y-coordinate (row).

        Returns:
            np.array: The gradient vector [df/dx, df/dy]. Returns [0, 0] if out of bounds.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            gx = self.gradient_x[y, x]
            gy = self.gradient_y[y, x]
            return np.array([gx, gy])
        else:
            return np.array([0.0, 0.0])  # No gradient outside the map

    def get_height_at(self, x: int, y: int) -> int:
        """
        Gets the altitude at a specific pixel.
        Assumes integer coordinates.

        Args:
            x (int): The x-coordinate (column).
            y (int): The y-coordinate (row).

        Returns:
            int: The altitude (0-255). Returns 0 if out of bounds.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return int(self.height_data[y, x])
        else:
            return 0  # Out of bounds is "low"

    def is_valid_start_point(self, x: int, y: int) -> bool:
        """
        Checks if a given coordinate is a valid starting point based on altitude.

        Args:
            x (int): The x-coordinate (column).
            y (int): The y-coordinate (row).

        Returns:
            bool: True if the point is high enough to start, False otherwise.
        """
        height = self.get_height_at(x, y)
        return height >= self.start_altitude_threshold

    def get_shelter_coords(self) -> Tuple[int, int]:
        """
        Returns the (x, y) pixel coordinates of the shelter.
        """
        return self.shelter_coords

    def get_as_image(self) -> Image.Image:
        """
        Converts the height data into a PIL Image object for the UI.

        Returns:
            PIL.Image: A grayscale ('L') image.
        """
        # The data is already uint8 (0-255), so this is a simple conversion.
        return Image.fromarray(self.height_data, "L")

    def save_to_json(self, filename: str):
        """
        Saves the terrain map data to a JSON file.
        """
        map_data: dict[str, Any] = {
            "height_data": self.height_data.tolist(),
            "width": int(self.width),
            "height": int(self.height),
            "shelter_coords": (
                int(self.shelter_coords[0]),
                int(self.shelter_coords[1]),
            ),
            "start_altitude_threshold": int(self.start_altitude_threshold),
        }
        # Ensure the directory exists before saving
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            json.dump(map_data, f, indent=4)
        print(f"Terrain map saved to {filename}")
