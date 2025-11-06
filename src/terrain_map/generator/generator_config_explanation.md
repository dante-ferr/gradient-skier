# Configuration Parameter Guide - Gradient Skier

This file explains each constant in `config.json`, allowing for fine-tuning of the procedural terrain generation.

---

## 1. Main Basin (Shelter) Parameters

These parameters control the main "sink" of the map, which defines the overall slope and ensures the shelter is the lowest point.

### `SHELTER_DEPTH`
* **What it does:** The maximum depth of the basin's "drain," in logical units. It's the main force pulling the skier down the map.
* **Tuning:** A larger value creates a stronger contrast between the edges and the center, making the descent faster.

### `SHELTER_WIDTH`
* **What it does:** The width of the main basin. It controls how gentle the slope is.
* **Tuning:**
    * **High value:** Creates a very wide and gentle "sink," covering almost the entire map.
    * **Low value:** Creates a more localized and steep hole.

### `SHELTER_BORDER_MIN_DISTANCE`
* **What it does:** The minimum distance (in pixels) that the shelter is allowed to spawn from the X and Y edges of the map.
* **Tuning:** Increase this to force the shelter further away from the map border.

### `SHELTER_MIN_EDGE_DISTANCE`
* **What it does:** A logical value to ensure the shelter doesn't spawn too close to the center. The sum of the absolute logical X and Y values (`abs(x) + abs(y)`) must be greater than this.
* **Tuning:** A larger value forces the shelter into the "corners" of the map. A low value allows it to spawn anywhere (except the exact center).

---

## 2. Trap Parameters

Control the generation of local minima (the holes that are not the shelter).

### `TRAP_DENSITY`
* **What it does:** The number of traps generated per area.
* **Tuning:**
    * **High value:** A more dangerous and rugged map with many holes.
    * **Low value:** A more open map with fewer obstacles.

### `TRAP_ABSOLUTE_DEPTH_MIN / MAX`
* **What it does:** The depth of the traps, in logical units. These are absolute values and should always be less than `SHELTER_DEPTH`.
* **Tuning:** Increasing these values makes the traps more dangerous and harder to escape.

### `TRAP_WIDTH_MIN / MAX`
* **What it does:** The width of the trap holes.
* **Tuning:**
    * **Low values:** Small, point-like holes.
    * **High values:** Large depressions in the terrain.

---

## 3. Basin Warping Parameters

Control the irregular and organic shape of *all* basins (shelter and traps).

### `BASIN_WARP_OCTAVES`
* **What it does:** The level of detail in the distortion of the basin's edge.
* **Tuning:** Higher values create edges with more "noise" and irregularities.

### `BASIN_WARP_FREQUENCY`
* **What it does:** The scale of the curves on the basin's edge.
* **Tuning:**
    * **Low value:** Long, smooth curves with few "branches."
    * **High value:** Many small curves, creating a jagged edge.

### `BASIN_WARP_AMPLITUDE`
* **What it does:** The strength of the distortion. How far the basin edges are "pulled" from their original circular shape.
* **Tuning:**
    * **Low value:** Almost circular basins.
    * **High value:** Very stretched and winding basins.

---

## 4. Detail Noise Parameters

Controls the fine texture and roughness of the entire terrain.

### `DETAIL_NOISE_OCTAVES`
* **What it does:** The level of detail of the noise.
* **Tuning:** Higher values create a richer, more realistic texture.

### `DETAIL_NOISE_FREQUENCY`
* **What it does:** The "scale" of the noise.
* **Tuning:**
    * **High value:** Fine-grained texture with many small ripples.
    * **Low value:** Coarse-grained texture with larger ripples.

### `DETAIL_NOISE_AMPLITUDE`
* **What it does:** The height of the noise ripples. This value should be **very low** compared to the trap depth, so the noise is just an aesthetic detail and does not create obstacles.

---

## 5. Safe Corridor Parameters

Control the generation of the winding path that guarantees the map is solvable. This is a complex "trench" structure with three levels: an inner ravine, a safe shelf, and outer walls.

### 5.1. Path Simulation (The "Walker")

These parameters control the forces that guide a simulated "walker" to define the *centerline* of the corridor.

### `CORRIDOR_GRAVITY_STRENGTH`
* **What it does:** The strength of the "gravity" force, which pulls the walker down the steepest local slope (the gradient of the main basin). This makes the path follow the terrain's contours.
* **Tuning:** A higher value makes the path more "natural" and terrain-aware.

### `CORRIDOR_MAGNET_STRENGTH`
* **What it does:** The base strength of the "magnet" force, which pulls the walker in a straight line toward the shelter. This guarantees progress.
* **Tuning:**
    * **High value:** The path becomes straighter and less interesting.
    * **Low value:** The path is more influenced by gravity and wobble.

### `CORRIDOR_WOBBLE_STRENGTH`
* **What it does:** The strength of the lateral "wind" force (noise) that pushes the walker to the side. This is the primary source of sinuosity.
* **Tuning:**
    * **High value:** Creates dramatic, wide curves.
    * **Low value:** Creates subtle deviations.

### `CORRIDOR_WOBBLE_FREQUENCY`
* **What it does:** The frequency of the "wind's" curves.
* **Tuning:**
    * **Low value:** Long, smooth curves.
    * **High value:** Fast, short zig-zags.

### `CORRIDOR_WOBBLE_OCTAVES`
* **What it does:** The level of detail of the "wind," making the deviation more organic. Lower values produce smoother curves.

### `CORRIDOR_LOCKON_RANGE`
* **What it does:** The distance (in logical units) from the shelter where the "funnel" effect begins. Inside this range, the magnet gets stronger and the wobble gets weaker.
* **Tuning:** A larger value means the path will start straightening out earlier.

### `CORRIDOR_LOCKON_STRENGTH`
* **What it does:** The extra strength added to the "magnet" force when the walker is inside the lock-on range, ensuring it converges on the target.

### `CORRIDOR_STEP_SIZE`
* **What it does:** The length of each step in the corridor simulation. Generally doesn't need to be changed.

### `CORRIDOR_MAX_STEPS`
* **What it does:** A safety limit to prevent infinite loops in the simulation.

---

### 5.2. Corridor Structure (The "Shape")

These parameters use the walker's path as a centerline to build the physical "trench" into the terrain.

### `CORRIDOR_WIDTH`
* **What it does:** The *total* width of the entire corridor structure, from one outer edge to the other, in logical units.
* **Tuning:** Defines the overall size of the safe/attenuated zone.

### `CORRIDOR_FLAT_BOTTOM_RATIO`
* **What it does:** Defines the width of the **safe platform** (the inner area that is completely flat and has 0% trap strength) as a ratio of the total `CORRIDOR_WIDTH`.
* **Tuning:** A ratio of `1.0` removes the outer walls, making the entire corridor a flat, trap-free zone (not recommended if you want a smooth transition). A lower ratio creates a narrower platform and wider, sloping walls.

### `CORRIDOR_WALL_SHARPNESS`
* **What it does:** Controls the steepness of the **outer walls** (the transition from the trap-free platform to the main, trap-filled terrain).
* **Tuning:**
    * **High value:** A steep, cliff-like edge.
    * **Low value:** A gentle, sloping transition.

### `CORRIDOR_RAVINE_DEPTH`
* **What it does:** The maximum depth of the **inner ravine** that is carved *inside* the safe platform, in logical units.
* **Tuning:** Increase to create a deeper, more obvious guiding channel. Set to `0.0` to disable the ravine, leaving only the flat, safe platform.

### `CORRIDOR_RAVINE_SHELF_RATIO`
* **What it does:** Defines the width of the inner ravine as a ratio of the `CORRIDOR_FLAT_BOTTOM_RATIO`. This creates the "safe shelf" between the ravine wall and the outer wall.
* **Tuning:**
    * **Ratio of `1.0`:** The ravine takes up the *entire* flat bottom (no shelf).
    * **Lower ratios:** The ravine takes up a percentage of the flat bottom, leaving shelf space on each side.
    * **Ratio of `0.0`:** The ravine has zero width (disables it).

### `CORRIDOR_RAVINE_WALL_SHARPNESS`
* **What it does:** Controls the steepness of the **inner ravine walls** (the transition from the safe shelf down into the ravine).
* **Tuning:**
    * **High value:** Creates a deep "U" or "V" shaped channel.
    * **Low value:** Creates a very gentle, "spoon-like" depression.

---

## 6. General Game Parameters

### `START_ALTITUDE_THRESHOLD_PERCENT`
* **What it does:** Defines the minimum relative altitude for a point to be a valid starting location for both the **player** and the **safe corridor**. A value of `0.0` to `1.0` (representing 0% to 100%) of the map's maximum altitude.
* **Tuning:** A high value ensures starts are always at the "top of the mountain." A low value allows for starts closer to the middle.