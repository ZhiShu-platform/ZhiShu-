import os
import numpy as np

def parse_asc_header(filepath):
    """Parses the header of an ESRI ASCII raster file."""
    header = {}
    with open(filepath, 'r') as f:
        for _ in range(6):  # Read the first 6 lines for header info
            line = f.readline().strip().split()
            header[line[0].lower()] = float(line[1]) if '.' in line[1] else int(line[1])
    return header

def generate_custom_asc(reference_asc_path, output_filename, value, nodata_value=-9999):
    """
    Generates an ESRI ASCII raster file with a custom value based on a reference .asc file.

    Args:
        reference_asc_path (str): Path to an existing .asc file (e.g., elevation.asc)
                                  to get header information (ncols, nrows, etc.).
        output_filename (str): The desired name for the output .asc file.
        value (int/float): The custom value to fill the raster with.
        nodata_value (int/float): The NODATA value for the raster.
    """
    if not os.path.exists(reference_asc_path):
        print(f"Error: Reference file '{reference_asc_path}' not found. Cannot generate custom .asc.")
        return

    # Parse header from the reference file
    header = parse_asc_header(reference_asc_path)

    ncols = int(header['ncols'])
    nrows = int(header['nrows'])
    xllcorner = header['xllcorner']
    yllcorner = header['yllcorner']
    cellsize = header['cellsize']

    # Create the data array
    # Fill with the custom value, excluding NODATA areas from the reference file if possible
    # For simplicity here, we'll just fill everything with the value or nodata.
    # To truly mimic nodata areas, you'd need to read the reference file's data.
    # For 'cur.asc', usually it's filled with values, not many nodata areas if it's for the whole landscape.
    data = np.full((nrows, ncols), value, dtype=np.int32) # Using int32 as FFMC is usually integer

    # Write the new .asc file
    with open(output_filename, 'w') as f:
        f.write(f"ncols         {ncols}\n")
        f.write(f"nrows         {nrows}\n")
        f.write(f"xllcorner     {xllcorner}\n")
        f.write(f"yllcorner     {yllcorner}\n")
        f.write(f"cellsize      {cellsize}\n")
        f.write(f"NODATA_value  {nodata_value}\n")

        # Write data rows
        for row in data:
            f.write(" ".join(map(str, row)) + "\n")

    print(f"Successfully generated '{output_filename}' with value {value}.")

# Example usage for generating a drier 'cur.asc'
if __name__ == "__main__":
    # Define your reference file (e.g., elevation.asc, which you have uploaded)
    reference_file = "/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/Input_Landscape/elevation.asc" # Or "Forest.asc" or any other landscape .asc file

    # --- Scenario 1: Generate a drier 'cur.asc' (e.g., FFMC 90) ---
    output_filename_dry = "cur_dry.asc"
    dry_ffmc_value = 90  # A higher FFMC value indicates drier conditions
    generate_custom_asc(reference_file, output_filename_dry, dry_ffmc_value)

    # --- Scenario 2: Generate an extremely dry 'cur.asc' (e.g., FFMC 95) ---
    output_filename_extreme_dry = "cur_extreme_dry.asc"
    extreme_dry_ffmc_value = 95 # Even higher FFMC for extremely dry
    generate_custom_asc(reference_file, output_filename_extreme_dry, extreme_dry_ffmc_value)

    # Note: If you want to replace the original 'cur.asc' for your Cell2Fire run,
    # you would manually rename one of the generated files to 'cur.asc' before running Cell2Fire.
    # For example:
    # os.rename("cur_dry.asc", "cur.asc")
    # This script will not do that automatically to avoid accidental overwrites.