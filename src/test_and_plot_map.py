import argparse
import matplotlib.pyplot as plt
from matplotlib import cm
from terrain_map.generator import MapGenerator
import numpy as np
import plotly.graph_objects as go
from config import config

def _plot_map_2d_on_ax(ax, terrain_map):
    """
    Plots the 2D terrain map on a given matplotlib Axes object.
    """
    height_data = terrain_map.height_data
    width, height = terrain_map.width, terrain_map.height

    im = ax.imshow(
        height_data, cmap=cm.terrain, origin="upper", interpolation="nearest"
    )

    ax.set_title(f"2D Map View ({width}x{height})")
    ax.set_xlabel("X Coordinate (pixels)")
    ax.set_ylabel("Y Coordinate (pixels)")
    return im  # Return image for colorbar


def plot_plotly_3d(terrain_map, z_scale=1.0):
    """
    Generates and displays a 3D terrain map using Plotly, which leverages GPU.
    """
    height_data = terrain_map.height_data.astype(float) * z_scale
    width, height = terrain_map.width, terrain_map.height

    # Create the 3D surface plot
    fig = go.Figure(
        data=[
            go.Surface(
                z=height_data,
                colorscale="earth",
                cmin=np.min(height_data),
                cmax=np.max(height_data),
                showscale=False,
            )
        ]
    )

    fig.update_layout(
        title=f"3D Map View with Plotly ({width}x{height}, Z-scale: {z_scale}) - GPU Accelerated",
        scene=dict(
            xaxis_title="X Coordinate",
            yaxis_title="Y Coordinate",
            zaxis_title="Altitude",
            camera=dict(eye=dict(x=-1.5, y=-1.5, z=1.5)),
            aspectratio=dict(x=1, y=1, z=0.5),
        ),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    fig.show()


def _plot_2d_views(terrain_map):
    """
    Generates and displays 2D Map using Matplotlib.
    """
    MAP_WIDTH = config.MAP_WIDTH
    MAP_HEIGHT = config.MAP_HEIGHT

    fig = plt.figure(figsize=(12, 10))

    ax1 = fig.add_subplot(1, 1, 1)
    im1 = _plot_map_2d_on_ax(ax1, terrain_map)
    fig.colorbar(
        im1, ax=ax1, label="Altitude (0=low, 255=high)", fraction=0.046, pad=0.04
    )

    fig.suptitle(
        f"Gradient Engineer - 2D Map ({MAP_WIDTH}x{MAP_HEIGHT})",
        fontsize=16,
    )
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and plot a terrain map.")
    parser.add_argument(
        "--plot3d",
        action="store_true",
        help="Display a 3D plot of the map (using Plotly/GPU).",
    )
    parser.add_argument(
        "--plot-all",
        action="store_true",
        help="Display 2D map (Matplotlib) AND 3D plot (Plotly/GPU).",
    )
    args = parser.parse_args()

    MAP_WIDTH = config.MAP_WIDTH
    MAP_HEIGHT = config.MAP_HEIGHT
    Z_SCALE = 0.5

    print(f"--- Generating Test Map ({MAP_WIDTH}x{MAP_HEIGHT}) ---")
    generator = MapGenerator()

    # generate() now only returns the map (and a None mask, which we ignore)
    terrain_map = generator.generate(width=MAP_WIDTH, height=MAP_HEIGHT)
    print("Map generated successfully.")

    if args.plot_all:
        plot_plotly_3d(terrain_map, z_scale=Z_SCALE)
        _plot_2d_views(terrain_map)
        plt.show()
    elif args.plot3d:
        print("Displaying 3D plot with Plotly (GPU accelerated)...")
        plot_plotly_3d(terrain_map, z_scale=Z_SCALE)
    else:
        # Default action is to show the 2D map
        _plot_2d_views(terrain_map)
        print("Displaying 2D plot with Matplotlib. Close the window to exit.")
        plt.show()

    print("\nScript finished.")
