# Terrain Generator Configuration Guide

This document explains each of the parameters found in `generator_config.json`. These values control the procedural generation of the terrain map. Tweaking them can lead to a wide variety of landscapes.

## Base Terrain Shape (`wide_variation_*`)

These parameters define the large-scale features of the map, like the main mountain ranges and valleys.

*   `"wide_variation_octaves"`: Number of noise layers (octaves) for the base terrain shape. More octaves add more detail and complexity to the large-scale mountains and valleys.
*   `"wide_variation_frequency"`: Controls the "zoom" of the base terrain noise. A lower value creates larger, more spread-out features.
*   `"wide_variation_amplitude"`: The maximum height influence of the base terrain noise. Higher values result in taller mountains and deeper valleys.

---

## Terrain Features (`trap_*` and `ridge_*`)

These parameters control the placement and shape of smaller, more distinct features on top of the base terrain.
*   `"feature_center_bias_strength"`: Controls how strongly features (ridges and traps) are biased towards the center of the map. A value of `0.0` means no bias (uniform distribution). A value of `1.0` provides a linear bias. Values greater than `1.0` create a much stronger concentration of features at the center, with the effect becoming more pronounced as the number increases.

### Traps (Pits/Holes)

*   `"trap_density"`: The probability of a "trap" (a pit or hole) being placed at any given point on the map.
*   `"trap_absolute_depth_min"`: The minimum depth a trap will be carved into the terrain.
*   `"trap_absolute_depth_max"`: The maximum depth a trap will be carved into the terrain.
*   `"trap_width_min"`: The minimum radius of a trap.
*   `"trap_width_max"`: The maximum radius of a trap.

### Ridges (Hills/Sharp Mountains)

*   `"ridge_density"`: The probability of a "ridge" (a sharp hill or mountain) being placed at any given point.
*   `"ridge_absolute_height_min"`: The minimum height a ridge will be raised from the terrain.
*   `"ridge_absolute_height_max"`: The maximum height a ridge will be raised from the terrain.
*   `"ridge_width_min"`: The minimum radius of a ridge.
*   `"ridge_width_max"`: The maximum radius of a ridge.
*   `"ridge_octaves"`: Number of noise layers used to add detail and texture to the ridges themselves, making them look less uniform.
*   `"ridge_frequency"`: The frequency of the noise applied to ridges, controlling how rough they appear.
*   `"ridge_amplitude"`: The intensity of the noise applied to ridges.

---

## Warping and Detail (`basin_warp_*` and `detail_noise_*`)

These parameters add final touches to the terrain, creating more organic and detailed shapes.

### Basin Warping

*   `"basin_warp_octaves"`: Number of noise layers for the domain warping effect that creates large, basin-like depressions.
*   `"basin_warp_frequency"`: The frequency of the basin warping noise. Lower values create larger, smoother basins.
*   `"basin_warp_amplitude"`: The strength of the domain warping effect. Higher values create more significant distortion and deeper basins.

### Fine Detail

*   `"detail_noise_octaves"`: Number of noise layers for the final, high-frequency detail pass over the entire terrain.
*   `"detail_noise_frequency"`: The frequency of the detail noise. Higher values add finer, grainier texture to the ground.
*   `"detail_noise_amplitude"`: The height influence of the final detail noise. This should be a small value to avoid making the terrain too noisy.