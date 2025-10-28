import argparse
from terrain_map.generator import MapGenerator
from config import config

if __name__ == "__main__":
    # Define the default save path relative to the project root
    default_save_path = config.TERRAIN_SAVES_PATH / "terrain_map.json"

    parser = argparse.ArgumentParser(
        description="Generate a terrain map and save it to a JSON file."
    )
    parser.add_argument(
        "filename",
        nargs="?",
        default=str(default_save_path),
        help=f"The path to the output JSON file. Defaults to: {default_save_path}",
    )
    args = parser.parse_args()

    MAP_WIDTH = config.MAP_WIDTH
    MAP_HEIGHT = config.MAP_HEIGHT

    print(f"--- Generating Terrain Map ({MAP_WIDTH}x{MAP_HEIGHT}) ---")
    generator = MapGenerator()
    # We only need the terrain_map object for saving, so we ignore the attenuation_mask
    terrain_map, _ = generator.generate(width=MAP_WIDTH, height=MAP_HEIGHT)
    print(
        f"Map generated. Shelter location: (x={terrain_map.get_shelter_coords()[0]}, y={terrain_map.get_shelter_coords()[1]})"
    )

    terrain_map.save_to_json(
        args.filename
    )  # Now calls the method on the TerrainMap object

    print("\nScript finished.")
