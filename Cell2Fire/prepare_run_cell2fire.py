import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import shutil
import subprocess
import warnings
import pyproj
from osgeo import gdal, osr

# Suppress all warnings for cleaner output
warnings.filterwarnings("ignore")

# --- Helper to read ASC header values ---
def get_asc_header_info(asc_filepath):
    """
    Reads ncols, nrows, xllcorner, yllcorner, cellsize, and NODATA_value
    from an ASC file's header. It will standardize keys to lowercase internally.
    """
    header_info = {}
    
    with open(asc_filepath, 'r') as f:
        for i, line in enumerate(f):
            if i >= 6: # Only read the first 6 lines for the header
                break
            
            line = line.strip()
            parts = line.split(maxsplit=1)
            
            if len(parts) == 2:
                key = parts[0].lower() # Convert key to lowercase for robust parsing
                value_str = parts[1]
                
                try:
                    if key == "ncols" or key == "nrows":
                        header_info[key] = int(value_str)
                    elif key == "xllcorner" or key == "yllcorner" or key == "cellsize":
                        header_info[key] = float(value_str)
                    elif key == "nodata_value" or key == "NODATA_value".lower(): # Handle both 'nodata_value' and 'NODATA_value' on read
                        header_info['nodata_value'] = float(value_str) # Standardize key to lowercase 'nodata_value' internally
                except ValueError:
                    # If conversion fails, store as string, but only for expected keys
                    if key in ["ncols", "nrows", "xllcorner", "yllcorner", "cellsize", "nodata_value"]:
                        header_info[key] = value_str
    
    # Ensure all standard keys are present, set to None if not found
    for k in ["ncols", "nrows", "xllcorner", "yllcorner", "cellsize", "nodata_value"]:
        if k not in header_info:
            header_info[k] = None
            
    return header_info

# --- Converts a GeoTIFF file to an ESRI ASCII Grid (.asc) format ---
def convert_tif_to_asc(input_tif_path, output_asc_path, nodata_value=-9999.0):
    print(f"Converting {os.path.basename(input_tif_path)} to {os.path.basename(output_asc_path)}...")
    try:
        dataset = gdal.Open(input_tif_path)
        if dataset is None:
            raise Exception(f"Failed to open GeoTIFF file: {input_tif_path}")

        geo_transform = dataset.GetGeoTransform()
        
        # Explicitly writing header for control over formatting
        with open(output_asc_path, 'w') as f:
            f.write(f"ncols         {dataset.RasterXSize}\n")
            f.write(f"nrows         {dataset.RasterYSize}\n")
            # 格式化浮点数为统一精度 (例如，坐标小数点后4位，cellsize和nodata_value小数点后1位)
            f.write(f"xllcorner     {geo_transform[0]:.4f}\n")
            # yllcorner calculation for AAIGrid (bottom-left corner)
            f.write(f"yllcorner     {geo_transform[3] + dataset.RasterYSize * geo_transform[5]:.4f}\n")
            f.write(f"cellsize      {geo_transform[1]:.1f}\n")
            f.write(f"NODATA_value  {nodata_value:.1f}\n") # 确保 NODATA_value 使用大写且格式统一

            # Read raster data and write to file
            band = dataset.GetRasterBand(1)
            data_array = band.ReadAsArray()
            
            # Replace numpy's nan with nodata_value before writing
            data_array[np.isnan(data_array)] = nodata_value

            for row in range(dataset.RasterYSize):
                # Convert array row to space-separated string
                # 对于某些栅格 (如高程、燃料模型)，数据可能应为整数
                if 'fuel' in output_asc_path or 'elevation' in output_asc_path:
                    row_str = " ".join(map(str, data_array[row].astype(int)))
                else:
                    # 对于其他栅格 (坡度、坡向)，保留浮点数或根据需要格式化
                    row_str = " ".join(map(lambda x: f"{x:.1f}" if isinstance(x, float) else str(x), data_array[row]))

                f.write(row_str + "\n")
        
        dataset = None # Close dataset
        print(f"Successfully converted {os.path.basename(input_tif_path)} to {os.path.basename(output_asc_path)}")
        return output_asc_path
    except Exception as e:
        print(f"Error converting {os.path.basename(input_tif_path)}: {e}")
        raise


# --- Validates if an ASC file exists and has content (basic check) ---
def validate_asc_file(filepath):
    if not os.path.exists(filepath):
        print(f"验证失败: 文件不存在 - {filepath}")
        return False
    if os.path.getsize(filepath) == 0:
        print(f"验证失败: 文件为空 - {filepath}")
        return False
    # More robust check could involve reading header
    try:
        header = get_asc_header_info(filepath)
        if not all(key in header and header[key] is not None for key in ["ncols", "nrows", "xllcorner", "yllcorner", "cellsize", "nodata_value"]):
            print(f"验证失败: {filepath} 头部信息不完整。")
            return False
    except Exception as e:
        print(f"验证失败: 读取 {filepath} 头部信息出错: {e}")
        return False
    print(f"验证成功: {filepath}")
    return True

# --- Clips a raster (GeoTIFF or ASC) to a specified extent and saves as ASC ---
def clip_raster_to_extent(input_path, output_path, xmin, ymin, xmax, ymax, output_format="AAIGrid", nodata_value=-9999.0):
    print(f"Clipping {os.path.basename(input_path)} to extent [{xmin}, {ymin}, {xmax}, {ymax}]...")
    try:
        # Use gdal.Warp for clipping and format conversion
        # GDAL Warp will generate its own header based on the input and output options.
        # Ensure the input TIFs already have good precision, which is handled by convert_tif_to_asc.
        gdal.Warp(output_path, input_path,
                  format=output_format,
                  outputBounds=[xmin, ymin, xmax, ymax],
                  dstNodata=nodata_value) # Set nodata value for output

        print(f"Successfully clipped {os.path.basename(input_path)} to {os.path.basename(output_path)}")
        return output_path
    except Exception as e:
        print(f"Error clipping {os.path.basename(input_path)}: {e}")
        raise

# --- Reclassifies fuel model raster in memory ---
def reclassify_fuel_model_in_memory(input_fuel_path, output_fuel_path, fbp_lookup_table_path, nodata_value=-9999.0):
    print(f"Reclassifying fuel model from {os.path.basename(input_fuel_path)}...")
    try:
        # Load the lookup table
        lookup_df = pd.read_csv(fbp_lookup_table_path)
        mapping_dict = dict(zip(lookup_df['grid_value'], lookup_df['export_value']))

        # Open the input fuel raster
        src_ds = gdal.Open(input_fuel_path)
        if src_ds is None:
            raise Exception(f"Failed to open input fuel file: {input_fuel_path}")

        src_band = src_ds.GetRasterBand(1)
        fuel_array = src_band.ReadAsArray()

        # Apply reclassification
        reclassified_array = np.vectorize(mapping_dict.get)(fuel_array)

        # Handle NoData values: ensure they are preserved or set to the specified nodata_value
        # If the original array had its own NoData, this should be handled by mapping_dict.get or post-processing
        reclassified_array[np.isnan(reclassified_array)] = nodata_value # Map NaNs (from non-mapped values) to nodata_value

        # Create output raster
        driver = gdal.GetDriverByName('AAIGrid')
        # CreateCopy preserves geo-transform and header from src_ds
        dst_ds = driver.CreateCopy(output_fuel_path, src_ds)
        dst_band = dst_ds.GetRasterBand(1)
        dst_band.WriteArray(reclassified_array)
        dst_band.SetNoDataValue(nodata_value) # Set NoDataValue for the band metadata
        
        dst_ds = None # Close dataset
        src_ds = None
        
        print(f"Successfully reclassified fuel model to {os.path.basename(output_fuel_path)}")
        return output_fuel_path
    except Exception as e:
        print(f"Error reclassifying fuel model: {e}")
        raise


# --- Process NOAA data to FWI Stream ---
def process_noaa_to_fwi_stream(noaa_csv_path, output_weather_csv_path, start_date_sim, sim_years=1):
    print("Processing NOAA data and generating Weather.csv...")
    try:
        df_noaa = pd.read_csv(noaa_csv_path)
        df_noaa['datetime'] = pd.to_datetime(df_noaa['datetime'])

        # Filter for the simulation period
        end_date_sim = pd.to_datetime(start_date_sim) + timedelta(days=sim_years * 365) # Approx. for sim_years
        df_filtered = df_noaa[(df_noaa['datetime'] >= start_date_sim) & (df_noaa['datetime'] < end_date_sim)].copy()

        if df_filtered.empty:
            print(f"警告：在 {start_date_sim} 至 {end_date_sim.strftime('%Y-%m-%d')} 期间未找到天气数据。")
            return None

        # Ensure required columns are present. If not, fill with placeholder/default.
        required_cols = ['APCP', 'TMP', 'RH', 'WS', 'WD', 'FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']
        for col in required_cols:
            if col not in df_filtered.columns:
                print(f"警告: 缺失天气数据列 '{col}'，将填充默认值 0。")
                df_filtered[col] = 0.0 # Or appropriate default/calculated value

        # Prepare for Cell2Fire's Weather.csv format
        df_output = df_filtered[['datetime', 'APCP', 'TMP', 'RH', 'WS', 'WD', 'FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']].copy()
        df_output['Scenario'] = 'JCB' # Example scenario name

        # Reorder columns to match example (Scenario, datetime, APCP, TMP, RH, WS, WD, FFMC, DMC, DC, ISI, BUI, FWI)
        df_output = df_output[['Scenario', 'datetime', 'APCP', 'TMP', 'RH', 'WS', 'WD', 'FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']]
        
        df_output.to_csv(output_weather_csv_path, index=False)
        print(f"Successfully generated Weather.csv: {output_weather_csv_path}")
        return output_weather_csv_path
    except FileNotFoundError:
        print(f"错误：未找到NOAA文件：{noaa_csv_path}。请检查路径。")
        raise
    except Exception as e:
        print(f"处理NOAA数据时发生错误：{e}")
        raise

# --- FIRMS 数据处理与点火点文件生成 ---
def prepare_ignition_file(firms_csv_path, start_date_sim, input_instance_folder, transformer, crop_xmin, crop_xmax, crop_ymin, crop_ymax, landscape_asc_path):
    print("开始处理FIRMS数据并生成点火点文件...")
    try:
        firms_df = pd.read_csv(firms_csv_path)
    except FileNotFoundError:
        print(f"错误：未找到FIRMS文件：{firms_csv_path}。请检查路径。")
        raise
    except Exception as e:
        print(f"读取FIRMS文件时发生错误：{e}")
        raise

    # Get landscape grid info from one of the ASC files
    try:
        landscape_header = get_asc_header_info(landscape_asc_path)
        ncols = landscape_header['ncols']
        nrows = landscape_header['nrows']
        xllcorner = landscape_header['xllcorner']
        yllcorner = landscape_header['yllcorner']
        cellsize = landscape_header['cellsize']
        print(f"  从 {os.path.basename(landscape_asc_path)} 读取栅格信息: ncols={ncols}, nrows={nrows}, xll={xllcorner}, yll={yllcorner}, cellsize={cellsize}")
    except Exception as e:
        print(f"错误：无法读取景观ASC文件的头信息以计算点火点Ncell：{e}")
        raise

    firms_df['acq_date'] = pd.to_datetime(firms_df['acq_date'])
    ignition_date = pd.to_datetime(start_date_sim)
    
    daily_ignitions = firms_df[firms_df['acq_date'] == ignition_date].copy()

    if daily_ignitions.empty:
        print(f"警告：在 {ignition_date.strftime('%Y-%m-%d')} 未找到点火点。请检查FIRMS数据。")
        return None

    daily_ignitions['acq_time_hhmm'] = daily_ignitions['acq_time'].astype(str).str.zfill(4)
    daily_ignitions['time_str'] = daily_ignitions['acq_date'].dt.strftime('%Y-%m-%d') + ' ' + \
                                   daily_ignitions['acq_time_hhmm'].str[0:2] + ':' + \
                                   daily_ignitions['acq_time_hhmm'].str[2:4]
    daily_ignitions['ignition_datetime'] = pd.to_datetime(daily_ignitions['time_str'])
    
    # 'Time' is in hours from start of simulation day
    daily_ignitions['Time'] = (daily_ignitions['ignition_datetime'] - datetime.combine(ignition_date.date(), datetime.min.time())).dt.total_seconds() / 3600

    daily_ignitions['X_proj'], daily_ignitions['Y_proj'] = transformer.transform(
        daily_ignitions['longitude'].values, 
        daily_ignitions['latitude'].values
    )
    
    # 筛选只在裁剪范围内的点火点
    filtered_ignitions = daily_ignitions[
        (daily_ignitions['X_proj'] >= crop_xmin) &
        (daily_ignitions['X_proj'] <= crop_xmax) &
        (daily_ignitions['Y_proj'] >= crop_ymin) &
        (daily_ignitions['Y_proj'] <= crop_ymax)
    ].copy()

    if filtered_ignitions.empty:
        print(f"警告：在 {ignition_date.strftime('%Y-%m-%d')} 的指定裁剪范围内未找到点火点。请调整裁剪范围或检查火点数据。")
        return None

    # --- Convert X, Y to Ncell ---
    filtered_ignitions['col'] = np.floor((filtered_ignitions['X_proj'] - xllcorner) / cellsize).astype(int)
    filtered_ignitions['row_from_bottom'] = np.floor((filtered_ignitions['Y_proj'] - yllcorner) / cellsize).astype(int)
    
    # Convert row from bottom to row from top (standard raster convention)
    filtered_ignitions['row'] = nrows - 1 - filtered_ignitions['row_from_bottom']

    # Filter out points that might fall outside due to precision or being exactly on edge
    filtered_ignitions = filtered_ignitions[
        (filtered_ignitions['col'] >= 0) & (filtered_ignitions['col'] < ncols) &
        (filtered_ignitions['row'] >= 0) & (filtered_ignitions['row'] < nrows)
    ].copy()

    if filtered_ignitions.empty:
        print(f"警告：所有点火点在转换为栅格单元后，均不在有效范围内。请检查坐标转换和栅格参数。")
        return None

    # Calculate Ncell (Cell2Fire often expects 1-indexed Ncell)
    filtered_ignitions['Ncell'] = (filtered_ignitions['row'] * ncols + filtered_ignitions['col']) + 1

    # Prepare DataFrame for ignitions.csv and IgnitionPoints.csv
    ignition_df_ncell = pd.DataFrame({
        'Year': 1, # Always 1 as per your 'sim-years 1'
        'Ncell': filtered_ignitions['Ncell']
    })
    # Remove duplicates in case multiple FIRMS points fall into the same cell
    ignition_df_ncell.drop_duplicates(inplace=True)

    # Save to both required files
    ignition_points_file_path = os.path.join(input_instance_folder, "IgnitionPoints.csv")
    ignitions_file_path = os.path.join(input_instance_folder, "Ignitions.csv")

    ignition_df_ncell.to_csv(ignition_points_file_path, index=False)
    ignition_df_ncell.to_csv(ignitions_file_path, index=False)

    print(f"点火点文件生成完成: {ignition_points_file_path} 和 {ignitions_file_path}，每个包含 {len(ignition_df_ncell)} 个点。")
    
    # Return path to one of them for consistency, though both are saved
    return ignitions_file_path


# --- Generate a dummy ASC file with a given value ---
def generate_dummy_asc(reference_asc_path, output_asc_path, fill_value=70.0):
    """
    Generates a dummy .asc file with the header from a reference ASC file
    and fills the data with a specified value.
    This is useful for creating placeholder files like cur.asc when
    actual data is not available but the file is required by Cell2Fire.
    """
    print(f"正在生成占位符 .asc 文件: {os.pyth.basename(output_asc_path)}...")
    try:
        header_info = get_asc_header_info(reference_asc_path)
        ncols = header_info['ncols']
        nrows = header_info['nrows']
        xllcorner = header_info['xllcorner']
        yllcorner = header_info['yllcorner']
        cellsize = header_info['cellsize']
        nodata_value = header_info.get('nodata_value', -9999.0) # Use 'nodata_value' as key after get_asc_header_info
        
    except Exception as e:
        print(f"错误：无法读取参考 ASC 文件 {os.path.basename(reference_asc_path)} 的头部信息：{e}")
        raise

    with open(output_asc_path, 'w') as f:
        f.write(f"ncols         {ncols}\n")
        f.write(f"nrows         {nrows}\n")
        # Format float values to ensure consistent precision
        f.write(f"xllcorner     {xllcorner:.4f}\n") # Example: 4 decimal places
        f.write(f"yllcorner     {yllcorner:.4f}\n") # Example: 4 decimal places
        f.write(f"cellsize      {cellsize:.1f}\n")  # Example: 1 decimal place
        f.write(f"NODATA_value  {nodata_value:.1f}\n") # Ensure NODATA_value is consistent and formatted

        # Write rows of data
        row_values = [str(fill_value)] * ncols
        row_string = " ".join(row_values) + "\n"
        
        for _ in range(nrows):
            f.write(row_string)
            
    print(f"成功生成占位符文件: {os.path.basename(output_asc_path)}")

# --- Check Cell2Fire Log for specific errors ---
def check_cell2fire_log(log_file_path):
    print(f"检查 Cell2Fire 日志文件: {log_file_path}...")
    if not os.path.exists(log_file_path):
        print("日志文件不存在。")
        return False
    
    with open(log_file_path, 'r') as f:
        log_content = f.read()
    
    errors_found = False
    if "Error" in log_content or "Failed" in log_content:
        print("\n--- 检测到可能的错误或失败信息 ---")
        print(log_content)
        errors_found = True
    else:
        print("日志文件中未检测到明显错误信息。")
    
    return not errors_found # Return True if no errors found

# --- Main function to run Cell2Fire simulation preparation ---
def run_cell2fire_simulation(
    raw_data_folder, 
    input_instance_folder, 
    output_base_folder, 
    cell2fire_exec_path,
    sim_start_date, 
    sim_years, 
    crop_xmin, crop_xmax, crop_ymin, crop_ymax,
    target_utm_epsg=32610 # Example: UTM Zone 10N
):
    print("--- 准备 Cell2Fire 模拟输入文件 ---")

    # 1. 确保输入实例文件夹存在且为空
    if os.path.exists(input_instance_folder):
        shutil.rmtree(input_instance_folder)
    os.makedirs(input_instance_folder)
    print(f"已创建或清空输入实例文件夹: {input_instance_folder}")

    # 定义输出文件路径
    dem_asc_final = os.path.join(input_instance_folder, "elevation.asc")
    slope_asc_final = os.path.join(input_instance_folder, "slope.asc")
    aspect_asc_final = os.path.join(input_instance_folder, "aspect.asc") # 'saz.asc' will be renamed to 'aspect.asc'
    fuel_asc_final = os.path.join(input_instance_folder, "fuel.asc") # 'Forest.asc' will be renamed to 'fuel.asc'
    weather_csv_final = os.path.join(input_instance_folder, "Weather.csv")

    # 定义原始数据路径
    dem_tif_path = os.path.join(raw_data_folder, "resampled_dem50.tif")
    slope_tif_path = os.path.join(raw_data_folder, "resampled_slope50.tif")
    saz_tif_path = os.path.join(raw_data_folder, "resampled_saz50.tif") # Original aspect TIFF name
    fuel_tif_path = os.path.join(raw_data_folder, "resampled_LF50.tif") # Original fuel TIFF name
    fbp_lookup_table_path = os.path.join(raw_data_folder, "fbp_lookup_table.csv")
    noaa_csv_path = os.path.join(raw_data_folder, "Weather.csv") # Assuming NOAA data is in a Weather.csv
    firms_data_csv = os.path.join(raw_data_folder, "fire_archive_M-C61_106125.csv")

    # 定义投影转换器（WGS84经纬度到目标UTM）
    crs_wgs84 = pyproj.CRS("EPSG:4326")
    crs_utm = pyproj.CRS(f"EPSG:{target_utm_epsg}")
    transformer_wgs84_to_utm = pyproj.Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True)

    # 2. 转换原始数据为 .asc 并裁剪
    print("\n--- 转换并裁剪栅格文件 ---")
    try:
        # DEM
        # Step 1: Convert raw TIF to ASC (with controlled header precision)
        temp_dem_asc = os.path.join(input_instance_folder, "temp_dem.asc")
        convert_tif_to_asc(dem_tif_path, temp_dem_asc)
        # Step 2: Clip the ASC to final extent
        clip_raster_to_extent(temp_dem_asc, dem_asc_final, crop_xmin, crop_ymin, crop_xmax, crop_ymax)
        os.remove(temp_dem_asc) # Clean up temp file
        validate_asc_file(dem_asc_final)

        # Slope
        temp_slope_asc = os.path.join(input_instance_folder, "temp_slope.asc")
        convert_tif_to_asc(slope_tif_path, temp_slope_asc)
        clip_raster_to_extent(temp_slope_asc, slope_asc_final, crop_xmin, crop_ymin, crop_xmax, crop_ymax)
        os.remove(temp_slope_asc)
        validate_asc_file(slope_asc_final)

        # Aspect (SAZ)
        temp_saz_asc = os.path.join(input_instance_folder, "temp_saz.asc")
        convert_tif_to_asc(saz_tif_path, temp_saz_asc)
        clip_raster_to_extent(temp_saz_asc, aspect_asc_final, crop_xmin, crop_ymin, crop_xmax, crop_ymax) # Renamed to aspect.asc
        os.remove(temp_saz_asc)
        validate_asc_file(aspect_asc_final)

        # Fuel Model (Forest)
        temp_fuel_asc = os.path.join(input_instance_folder, "temp_fuel.asc")
        convert_tif_to_asc(fuel_tif_path, temp_fuel_asc)
        # Clip the fuel model before reclassification (to avoid reclassifying outside relevant area)
        clipped_fuel_temp = os.path.join(input_instance_folder, "clipped_fuel_temp.asc")
        clip_raster_to_extent(temp_fuel_asc, clipped_fuel_temp, crop_xmin, crop_ymin, crop_xmax, crop_ymax)
        os.remove(temp_fuel_asc)
        
        # 3. 重新分类燃料模型
        reclassify_fuel_model_in_memory(clipped_fuel_temp, fuel_asc_final, fbp_lookup_table_path) # Renamed to fuel.asc
        os.remove(clipped_fuel_temp) # Clean up temp clipped fuel file
        validate_asc_file(fuel_asc_final)

    except Exception as e:
        print(f"栅格文件处理失败: {e}")
        return

    # 4. 生成占位符 cur.asc 文件
    # 使用一个已生成的景观ASC文件 (如 elevation.asc) 作为参考来确保 cur.asc 具有正确的空间属性
    cur_asc_path = os.path.join(input_instance_folder, "cur.asc")
    print("\n--- 生成占位符 cur.asc 文件 ---")
    try:
        if not os.path.exists(dem_asc_final):
            print(f"错误: 参考文件 {dem_asc_final} 不存在，无法生成 cur.asc 占位符。")
            return
        generate_dummy_asc(dem_asc_final, cur_asc_path, fill_value=70) 
        validate_asc_file(cur_asc_path)
    except Exception as e:
        print(f"生成 cur.asc 占位符文件失败: {e}")
        return

    # 5. 处理 NOAA 天气数据
    print("\n--- 处理 NOAA 天气数据 ---")
    try:
        weather_file_path = process_noaa_to_fwi_stream(noaa_csv_path, weather_csv_final, sim_start_date, sim_years)
        if weather_file_path is None:
            print("警告：未生成 Weather.csv 文件，模拟可能无法获取天气数据。")
    except Exception as e:
        print(f"天气数据处理失败: {e}")
        return

    # 6. 处理 FIRMS 点火点
    print("\n--- 处理 FIRMS 点火点（基于手动裁剪范围筛选并转换为 Ncell 格式）---")
    try:
        # Pass dem_asc_final (or any other primary landscape ASC) to read its header for Ncell calculation
        ignition_file_path = prepare_ignition_file(
            firms_data_csv, sim_start_date, input_instance_folder, transformer_wgs84_to_utm,
            crop_xmin, crop_xmax, crop_ymin, crop_ymax,
            dem_asc_final # Pass the path to elevation.asc (or any other ASC)
        )
        if ignition_file_path is None:
            print("警告：在指定裁剪范围内未找到有效点火点，模拟可能无法启动。")
    except Exception as e:
        print(f"点火点处理失败: {e}")
        return

    # 7. 构建 Cell2Fire 命令行参数
    print("\n--- 构建 Cell2Fire 命令行 ---")
    output_instance_folder = os.path.join(output_base_folder, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(output_instance_folder, exist_ok=True)

    # 命令行参数 (确保使用生成的 fuel.asc 和 aspect.asc)
    cell2fire_command_list = [
        cell2fire_exec_path,
        "--landscape", input_instance_folder,
        "--weather", weather_csv_final,
        "--ignitions", ignition_file_path, # ignition_file_path points to Ignitions.csv or IgnitionPoints.csv
        "--output", output_instance_folder,
        "--output-ascii", # Enable ASCII output
        "--sim-years", str(sim_years),
        "--log", # Enable logging
        "--ncores", "1" # Example: use 1 core, adjust as needed
    ]

    # 8. 执行 Cell2Fire 模拟
    print("\n--- 执行 Cell2Fire 模拟 ---")
    try:
        # Run Cell2Fire
        result = subprocess.run(cell2fire_command_list, capture_output=True, text=True, check=True)
        print("Cell2Fire Standard Output:\n", result.stdout)
        if result.stderr:
            print("Cell2Fire Standard Error:\n", result.stderr)
        
        # Check log file after run
        log_file = os.path.join(output_instance_folder, "LogFile.txt")
        if os.path.exists(log_file):
            check_cell2fire_log(log_file)
        else:
            print("警告: Cell2Fire 日志文件未生成。")

        print("\n--- Cell2Fire 模拟完成 ---")
        print(f"输出结果保存在: {output_instance_folder}")

    except subprocess.CalledProcessError as e:
        print(f"Cell2Fire 模拟失败，返回错误代码 {e.returncode}。")
        print("Cell2Fire Standard Output:\n", e.stdout)
        print("Cell2Fire Standard Error:\n", e.stderr)
        log_file = os.path.join(output_instance_folder, "LogFile.txt")
        if os.path.exists(log_file):
            print(f"请检查日志文件: {log_file} 获取更多详细信息。")
            with open(log_file, 'r') as f:
                print(f.read())
        else:
            print("未找到 Cell2Fire 日志文件。")
    except FileNotFoundError:
        print(f"错误: 无法找到 Cell2Fire 可执行文件。请检查路径: {cell2fire_exec_path}")
    except Exception as e:
        print(f"执行 Cell2Fire 模拟时发生意外错误: {e}")

# --- 主程序入口 ---
if __name__ == "__main__":
    # 配置参数
    RAW_DATA_FOLDER = "/data/Tiaozhanbei/Cell2Fire/raw_data/" # 原始数据存放目录
    INPUT_INSTANCE_FOLDER = "/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/Input_Landscape/" # 生成输入文件的目录
    OUTPUT_BASE_FOLDER = "/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/output_cell2fire/" # 模拟输出的根目录
    CELL2FIRE_EXEC_PATH = "/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/Cell2Fire_v2.0_Linux" # Cell2Fire 可执行文件路径
    
    SIM_START_DATE = "2001-10-16" # 模拟开始日期
    SIM_YEARS = 1 # 模拟年数

    # 根据您新的 Forest.asc (6401x4401, 50m) 的范围调整裁剪坐标
    # 这些值应该与您的 Forest.asc, elevation.asc, slope.asc, saz.asc 的实际范围匹配
    # 如果您的原始TIFs范围更大，这里裁剪到 Cell2Fire 实际模拟的区域
    CROP_XMIN = 239967.4733
    CROP_XMAX = CROP_XMIN + (6401 * 50.0) 
    CROP_YMIN = 3689961.1860
    CROP_YMAX = CROP_YMIN + (4401 * 50.0) 

    # 目标UTM EPSG代码 (例如，UTM Zone 10N 是 32610，请根据您的区域调整)
    TARGET_UTM_EPSG = 32610 

    run_cell2fire_simulation(
        RAW_DATA_FOLDER,
        INPUT_INSTANCE_FOLDER,
        OUTPUT_BASE_FOLDER,
        CELL2FIRE_EXEC_PATH,
        SIM_START_DATE,
        SIM_YEARS,
        CROP_XMIN, CROP_XMAX, CROP_YMIN, CROP_YMAX,
        TARGET_UTM_EPSG
    )