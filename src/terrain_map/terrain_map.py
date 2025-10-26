import numpy as np
from PIL import Image


class TerrainMap:
    """
    Holds all data for a single generated map, including height and gradient fields.
    This class is "read-only" after creation.
    """

    def __init__(self, height_data, shelter_coords, start_altitude_threshold):
        """
        Initializes the map with all necessary data.
        Gradients are pre-calculated here for performance.

        Args:
            height_data (np.array): 2D NumPy array (uint8) representing map altitude (0-255).
            shelter_coords (tuple): (x, y) pixel coordinates of the global minimum (shelter).
            start_altitude_threshold (int): The minimum altitude (0-255) to be a valid start point.
        """
        self.height_data = height_data
        self.shelter_coords = shelter_coords
        self.start_altitude_threshold = start_altitude_threshold

        self.width = self.height_data.shape[1]
        self.height = self.height_data.shape[0]

        map_float = self.height_data.astype(np.float32)

    def get_gradient_at(self, x, y):
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

    def get_height_at(self, x, y):
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
            return self.height_data[y, x]
        else:
            return 0  # Out of bounds is "low"

    def is_valid_start_point(self, x, y):
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

    def get_shelter_coords(self):
        """
        Returns the (x, y) pixel coordinates of the shelter.
        """
        return self.shelter_coords

    def get_as_image(self):
        """
        Converts the height data into a PIL Image object for the UI.

        Returns:
            PIL.Image: A grayscale ('L') image.
        """
        # The data is already uint8 (0-255), so this is a simple conversion.
        return Image.fromarray(self.height_data, "L")
