import matplotlib.pyplot as plt
from terrain_map.generator import MapGenerator

# terrain_map.py is also required, as MapGenerator imports it


def test_and_plot_map():
    """
    Generates a single terrain map and displays it using matplotlib
    for debugging and visualization.
    """
    MAP_WIDTH = 150
    MAP_HEIGHT = 150

    print(f"--- Generating Test Map ({MAP_WIDTH}x{MAP_HEIGHT}) ---")

    # 1. Initialize the generator
    generator = MapGenerator()

    # 2. Generate the map object
    terrain_map = generator.generate(width=MAP_WIDTH, height=MAP_HEIGHT)

    # 3. Get the data for plotting
    # We get the height_data, which is a simple 2D NumPy array
    height_data = terrain_map.height_data

    # Get shelter coordinates to mark it on the plot
    shelter_x, shelter_y = terrain_map.get_shelter_coords()

    print(f"Map generated. Shelter location: (x={shelter_x}, y={shelter_y})")

    # 4. Plot the map
    plt.figure(figsize=(12, 10))

    # imshow is the perfect tool to display a 2D array as an image
    # We use cmap='gray' for the altitude
    # We set origin='upper' to match image coordinates (0,0 at top-left)
    plt.imshow(height_data, cmap="gray", origin="upper", interpolation="nearest")

    plt.colorbar(label="Altitude (0=low, 255=high)")

    # 5. Mark the shelter's location
    # plt.plot uses (x, y) coordinates, which is what we have.
    plt.plot(
        shelter_x, shelter_y, "rx", markersize=12, mew=2, label="Shelter (Global Min)"
    )

    plt.title(f"Gradient Skier - Test Map Generation ({MAP_WIDTH}x{MAP_HEIGHT})")
    plt.xlabel("X Coordinate (pixels)")
    plt.ylabel("Y Coordinate (pixels)")
    plt.legend()

    # 6. Show the plot window
    print("Displaying plot. Close the plot window to exit.")
    plt.show()


if __name__ == "__main__":
    test_and_plot_map()
