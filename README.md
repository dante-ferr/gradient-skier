# Gradient Engineer

Gradient Engineer is a strategic puzzle game where you modify a procedurally generated terrain to find the most efficient path from the start point to the end. The goal is to carve a path from the starting point to the finish line that is significantly "cheaper" (less strenuous) than the original, automatically calculated route.

## Table of Contents

- [Educational Purpose: Visualizing Gradients](#educational-purpose-visualizing-gradients)
- [Gameplay](#gameplay)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Controls](#controls)
- [Available Commands](#available-commands)
- [Terrain Generation](#terrain-generation)
- [Project Structure](#project-structure)

## Educational Purpose: Visualizing Gradients

This project serves as an interactive tool to explain the concept of **gradients** from multivariable calculus.

*   **The Terrain as a Function**: The 3D terrain can be thought of as a function `z = f(x, y)`, where `(x, y)` are the coordinates on the map and `z` is the elevation.
*   **The Gradient Vector**: At any point on the map, the gradient, `∇f = (∂f/∂x, ∂f/∂y)`, is a vector that points in the direction of the steepest ascent. In the game, this is calculated numerically using a Sobel filter.
*   **Gradient Magnitude**: The length (magnitude) of the gradient vector, `||∇f||`, tells you *how steep* that ascent is. You can see this value displayed as "Map Gradient" when you hover over the terrain.
*   **Path Cost**: The "cost" of moving between two points on the path is directly related to the gradient. The A* pathfinding algorithm seeks to find a path that minimizes the total cost, which is conceptually similar to integrating the gradient's effect along the path. By terraforming, you are locally changing the function `f(x, y)` to reduce the gradient along the desired path, thus making it "cheaper" to traverse.

## Gameplay

The core objective is to reduce the traversal cost of the path from the start point (🏠) to the end point (🏁).

1.  **Initial State**: When the game starts, a random terrain map is generated, and an initial path is calculated. The cost of this path is your benchmark.
2.  **Terraforming**: You are given a limited number of "tool charges." Use your tools (selected from the sidebar) to raise or lower the terrain by clicking on the map.
3.  **Recalculation**: At the end of your modification, the path and its cost are recalculated.
4.  **Winning**: To win, you must reduce the path cost to a certain percentage of the initial cost (e.g., 80% or less) before you run out of tool charges.
5.  **Map Information**: You can hover your mouse over any part of the map to see its "gradient" or steepness. Steeper uphill climbs have a much higher movement cost.

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/dante-ferr/gradient-engineer.git
    cd gradient-engineer
    ```

2.  **Install dependencies:**
    ```bash
    make build
    ```

## How to Run

To start the game, run the following command from the project's root directory:

```bash
make run
```

## Controls

*   **Left-Click and Drag**: Pan the map.
*   **Scroll Wheel**: Zoom in and out.
*   **Right-Click (on map)**: Use the currently selected terraforming tool on the clicked location.

## Available Commands

The `Makefile` provides several convenient commands for managing and testing the application.

*   `make build`: Installs all project dependencies.
*   `make run`: Runs the main game application.
*   `make generate-and-save-map`: Generates a new random map and saves it to `data/terrain_map.json`.
*   `make test-map`: Runs a 2D visual test of the map generation algorithm.
*   `make test-map-3d`: Runs a 3D visual test of the map generation algorithm.
*   `make test-map-all`: Runs both the 2D and 3D visual tests side-by-side.

## Terrain Generation

The terrain is procedurally generated using a combination of noise algorithms. You can customize the generation process by modifying the parameters in `src/terrain_map/generator/generator_config.json`.

For a detailed explanation of what each parameter does, please refer to the Terrain Generator Configuration Guide.
