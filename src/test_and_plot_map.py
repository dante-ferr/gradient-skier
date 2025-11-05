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
    shelter_x, shelter_y = terrain_map.get_shelter_coords()

    im = ax.imshow(
        height_data, cmap=cm.terrain, origin="upper", interpolation="nearest"
    )

    ax.plot(
        shelter_x,
        shelter_y,
        "rx",
        markersize=12,
        mew=2,
        label="Shelter (Global Min)",
    )

    ax.set_title(f"2D Map View ({width}x{height})")
    ax.set_xlabel("X Coordinate (pixels)")
    ax.set_ylabel("Y Coordinate (pixels)")
    ax.legend()
    return im  # Return image for colorbar


def _plot_mask_2d_on_ax(ax, mask, terrain_map):
    """
    Plots the attenuation mask on a given matplotlib Axes object.
    """
    shelter_x, shelter_y = terrain_map.get_shelter_coords()

    im = ax.imshow(
        mask,
        cmap=cm.viridis,
        origin="upper",
        interpolation="nearest",
        vmin=0.0,
        vmax=1.0,
    )

    ax.plot(
        shelter_x,
        shelter_y,
        "rx",
        markersize=12,
        mew=2,
        label="Shelter Location",
    )

    ax.set_title(f"Attenuation Mask (Corridor)")
    ax.set_xlabel("X Coordinate (pixels)")
    ax.set_ylabel("Y Coordinate (pixels)")
    ax.legend()
    return im


# REMOVED: _plot_map_3d_on_ax(ax, terrain_map, z_scale=1.0)
# This function is removed because we will use Plotly for 3D rendering.


def plot_plotly_3d(terrain_map, z_scale=1.0):
    """
    Generates and displays a 3D terrain map using Plotly, which leverages GPU.
    This will open a new tab/window in your web browser.
    """
    height_data = terrain_map.height_data.astype(float) * z_scale
    width, height = terrain_map.width, terrain_map.height

    shelter_x, shelter_y = terrain_map.get_shelter_coords()
    shelter_z = terrain_map.get_height_at(shelter_x, shelter_y) * z_scale

    # Create the 3D surface plot
    fig = go.Figure(
        data=[
            go.Surface(
                z=height_data,
                colorscale="earth",
                cmin=np.min(
                    height_data
                ),  # Ensure color scale aligns with actual height data
                cmax=np.max(height_data),
                showscale=False,  # Hide default color scale as we will add a custom one if needed
            ),
            go.Scatter3d(
                x=[shelter_x],
                y=[shelter_y],
                z=[shelter_z + (15 * z_scale)],
                mode="markers",
                marker=dict(size=10, color="red", symbol="x"),
                name="Shelter (Global Min)",
            ),
        ]
    )

    # Customize layout and camera view
    fig.update_layout(
        title=f"3D Map View with Plotly ({width}x{height}, Z-scale: {z_scale}) - GPU Accelerated",
        scene=dict(
            xaxis_title="X Coordinate",
            yaxis_title="Y Coordinate",
            zaxis_title="Altitude",
            camera=dict(
                eye=dict(
                    x=-1.5, y=-1.5, z=1.5
                ),  # Initial camera position (elev=60, azim=-65 approximation)
                up=dict(x=0, y=0, z=1),
            ),
            aspectratio=dict(
                x=1, y=1, z=0.5
            ),  # Adjust aspect ratio for Z axis for better visualization
        ),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    fig.show()


def _plot_2d_views(terrain_map, attenuation_mask):
    """
    Generates and displays 2D Map and Attenuation Mask using Matplotlib.
    """
    MAP_WIDTH = config.MAP_WIDTH
    MAP_HEIGHT = config.MAP_HEIGHT

    fig = plt.figure(figsize=(20, 10))

    # 2D Plot
    ax1 = fig.add_subplot(1, 2, 1)
    im1 = _plot_map_2d_on_ax(ax1, terrain_map)
    fig.colorbar(
        im1, ax=ax1, label="Altitude (0=low, 255=high)", fraction=0.046, pad=0.04
    )

    # Attenuation Mask Plot
    ax2 = fig.add_subplot(1, 2, 2)
    im2 = _plot_mask_2d_on_ax(ax2, attenuation_mask, terrain_map)
    fig.colorbar(
        im2, ax=ax2, label="Trap Strength (0=weak, 1=strong)", fraction=0.046, pad=0.04
    )

    fig.suptitle(
        f"Gradient Skier - 2D Map & Corridor Mask ({MAP_WIDTH}x{MAP_HEIGHT})",
        fontsize=16,
    )
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])


def plot_all_views(terrain_map, attenuation_mask, z_scale=1.0):
    """
    Generates and displays 2D Map and Attenuation Mask using Matplotlib,
    and a 3D Map using Plotly (GPU accelerated).
    """
    plot_plotly_3d(terrain_map, z_scale=z_scale)

    # Display the 2D Matplotlib plots
    _plot_2d_views(terrain_map, attenuation_mask)
    plt.show()


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
        help="Display 2D map, Attenuation mask (Matplotlib) AND 3D plot (Plotly/GPU).",
    )
    args = parser.parse_args()

    MAP_WIDTH = config.MAP_WIDTH
    MAP_HEIGHT = config.MAP_HEIGHT
    Z_SCALE = 0.5  # Increased default Z_SCALE for better 3D visualization

    print(f"--- Generating Test Map ({MAP_WIDTH}x{MAP_HEIGHT}) ---")
    generator = MapGenerator()
    terrain_map, attenuation_mask = generator.generate(
        width=MAP_WIDTH, height=MAP_HEIGHT
    )
    print(
        f"Map generated. Shelter location: (x={terrain_map.get_shelter_coords()[0]}, y={terrain_map.get_shelter_coords()[1]})"
    )

    if args.plot_all:
        plot_all_views(terrain_map, attenuation_mask, z_scale=Z_SCALE)
    elif args.plot3d:
        print(
            "Displaying 3D plot with Plotly (GPU accelerated). This will open in your browser."
        )
        plot_plotly_3d(terrain_map, z_scale=Z_SCALE)
    else:
        # Default action is to show the 2D map and the mask (Matplotlib)
        _plot_2d_views(terrain_map, attenuation_mask)
        print("Displaying 2D plots with Matplotlib. Close the window to exit.")
        plt.show()

    print("\nScript finished.")
