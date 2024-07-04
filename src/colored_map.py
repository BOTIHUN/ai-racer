import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def generate_colored_map(f_score_map, grid_shape, output_file):
    # Initialize the 2D array with NaN values for non-visited nodes
    f_score_array = np.full(grid_shape, np.nan)

    # Fill the array with f_score values from the map
    for (x, y), f_score in f_score_map.items():
        f_score_array[x, y] = f_score

    # Normalize the f_score values to the range [0, 1]
    min_f_score = np.nanmin(f_score_array)
    max_f_score = np.nanmax(f_score_array)
    normalized_f_score_array = (f_score_array - min_f_score) / (max_f_score - min_f_score)

    # Create a color map
    cmap = plt.get_cmap('viridis')
    norm = mcolors.Normalize(vmin=0, vmax=1)

    # Plot the color map
    plt.figure(figsize=(8, 8))
    plt.imshow(normalized_f_score_array, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(label='Normalized f_score')
    plt.title('f_score Map')
    plt.xlabel('First')
    plt.ylabel('Second')

    plt.savefig(output_file)
