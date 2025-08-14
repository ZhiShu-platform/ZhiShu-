import os
import numpy as np
import pandas as pd
import subprocess
import warnings
import pyproj 
from datetime import datetime 

# No Warnings
warnings.filterwarnings("ignore")

# --- 读取ASC文件头部信息函数 ---
def read_asc_header(filepath):
    """
    读取ASC文件的头部信息并返回字典。
    """
    header = {}
    try:
        with open(filepath, 'r') as f:
            for _ in range(6):
                line = f.readline().strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) == 2:
                    key, value = parts
                    try:
                        # Attempt to convert to float, then int if applicable, handle NODATA as string if needed
                        if key in ['ncols', 'nrows']:
                            header[key.lower()] = int(float(value))
                        elif key == 'nodata_value':
                             header[key.lower()] = int(float(value)) # Ensure NODATA_value is an integer
                        elif '.' in value or 'e' in value.lower():
                            header[key.lower()] = float(value)
                        else:
                            header[key.lower()] = int(value)
                    except ValueError:
                        header[key.lower()] = value # Keep as string if conversion fails (e.g., if NODATA_value is "NA")
        return header
    except Exception as e:
        print(f"错误：无法读取文件 {filepath} 的头部信息。请检查文件是否存在或格式是否正确。错误信息: {e}")
        return None

# --- 读取 FBP 映射表并创建字典 ---
def load_fbp_dictionary(fbp_lookup_filepath):
    """
    读取 fbp_lookup_table.csv 并创建数字燃料代码到 FBP 字符串的映射字典。
    根据提供的 fbp_lookup_table.csv 文件结构进行调整。
    """
    fuel_map = {}
    try:
        df_lookup = pd.read_csv(fbp_lookup_filepath)
        # 核心修改：去除所有列名中的首尾空格，解决 KeyError 问题
        df_lookup.columns = df_lookup.columns.str.strip() 

        # 假设 fbp_lookup_table.csv 有 'grid_value' 和 'fuel_type' 列
        for index, row in df_lookup.iterrows():
            grid_value = str(int(row['grid_value'])) # 确保键是字符串
            fbp_type_raw = str(row['fuel_type'])

            # 根据 Cell2Fire 的惯例进行映射和格式化
            if grid_value == "102": # 水体
                fuel_map[grid_value] = "W"
            elif fbp_type_raw == "Non-fuel": # 其他非燃料区域
                fuel_map[grid_value] = "NF"
            elif fbp_type_raw.startswith("O-1a"): #
                fuel_map[grid_value] = "O1a"
            elif fbp_type_raw.startswith("O-1b"): #
                fuel_map[grid_value] = "O1b"
            else:
                # 移除 FBP 类型中的连字符，例如 "C-1" -> "C1"
                fuel_map[grid_value] = fbp_type_raw.replace('-', '')
                
    except FileNotFoundError:
        print(f"错误：未找到 FBP 查找表文件：{fbp_lookup_filepath}")
        print("请确保 'fbp_lookup_table.csv' 存在于您的 Input_Landscape 目录中。")
        return None
    except KeyError as e:
        print(f"错误：'fbp_lookup_table.csv' 缺少必要的列。请确保包含 'grid_value' 和 'fuel_type'。错误: {e}")
        return None
    except Exception as e:
        print(f"读取或解析 'fbp_lookup_table.csv' 时发生错误: {e}")
        return None
    
    print(f"DEBUG: 成功加载 FBP 映射表，包含 {len(fuel_map)} 个条目。")
    return fuel_map

# --- 生成 Data.csv 函数 (已修改，确保动态计算 lat/lon, 并填充 gfl, pdf, pc) ---
def generate_data_csv(clipped_input_dir, data_csv_output_path, 
                      reclassified_fuel_path, fbp_lookup_filepath, processed_weather_path): 
    """
    根据所有处理后的输入文件生成 Cell2Fire 所需的 Data.csv。
    这个版本将使用 Weather.csv 的第一行数据填充 Data.csv。
    """
    print("\n--- 正在生成 Data.csv ---")

    # 读取裁剪并对齐后的栅格数据
    elevation_data = np.loadtxt(os.path.join(clipped_input_dir, "elevation.asc"), skiprows=6)
    slope_data = np.loadtxt(os.path.join(clipped_input_dir, "slope.asc"), skiprows=6)
    saz_data = np.loadtxt(os.path.join(clipped_input_dir, "saz.asc"), skiprows=6)
    cur_data = np.loadtxt(os.path.join(clipped_input_dir, "cur.asc"), skiprows=6)
    
    fuel_data_reclassified_array = np.loadtxt(reclassified_fuel_path, skiprows=6)

    header = read_asc_header(os.path.join(clipped_input_dir, "Forest.asc"))
    if not header:
        print("错误：无法读取裁剪后的 Forest.asc 头部信息，无法生成 Data.csv。")
        return False
    
    ncols = int(header['ncols'])
    nrows = int(header['nrows'])
    xllcorner = header['xllcorner']
    yllcorner = header['yllcorner']
    cellsize = header['cellsize']
    nodata_value = int(header.get('nodata_value', -9999)) 

    print(f"DEBUG: Data.csv生成：从Forest.asc读取到的头部信息:")
    print(f"DEBUG: ncols={ncols}, nrows={nrows}, xllcorner={xllcorner}, yllcorner={yllcorner}, cellsize={cellsize}, NODATA_value={nodata_value}")

    elev_flat = elevation_data.flatten()
    slope_flat = slope_data.flatten()
    saz_flat = saz_data.flatten()
    cur_flat = cur_data.flatten()
    
    # 检查所有数组长度是否一致
    if not (len(elev_flat) == len(slope_flat) == len(saz_flat) == len(cur_flat) == len(fuel_data_reclassified_array.flatten())):
        print("错误：输入 .asc 文件长度不一致。请检查裁剪是否正确。")
        return False

    fuel_type_map = load_fbp_dictionary(fbp_lookup_filepath)
    if fuel_type_map is None:
        return False 
    
    fuel_flat_numeric = fuel_data_reclassified_array.flatten()
    fuel_flat_fbp_strings = []
    
    print("  正在转换数字燃料代码为 FBP 字符串...")
    for fuel_code_num in fuel_flat_numeric:
        if fuel_code_num == nodata_value:
            fuel_flat_fbp_strings.append("NF") 
        else:
            fuel_code_str = str(int(fuel_code_num)) 
            fuel_flat_fbp_strings.append(fuel_type_map.get(fuel_code_str, "NF")) 

    data_df = pd.DataFrame({
        'elev': elev_flat,
        'slope': slope_flat,
        'saz': saz_flat,
        'cur': cur_flat,
        'fueltype': fuel_flat_fbp_strings 
    })

    data_df = data_df.replace(-9999, np.nan) 

    x_coords = np.linspace(xllcorner + cellsize / 2,
                           xllcorner + ncols * cellsize - cellsize / 2,
                           ncols)
    y_coords = np.linspace(yllcorner + nrows * cellsize - cellsize / 2,
                           yllcorner + cellsize / 2,
                           nrows)
    
    xx, yy = np.meshgrid(x_coords, y_coords)
    
    transformer_utm_to_latlon = pyproj.Transformer.from_crs("EPSG:26911", "EPSG:4326", always_xy=True)
    lon_grid, lat_grid = transformer_utm_to_latlon.transform(xx, yy)
    
    data_df['lon'] = lon_grid.flatten()
    data_df['lat'] = lat_grid.flatten()

    print(f"DEBUG: Data.csv生成：第一个单元格的经纬度 (用于验证):")
    print(f"DEBUG: Lat={data_df['lat'].iloc[0]}, Lon={data_df['lon'].iloc[0]}")

    simulation_start_date = datetime(2025, 1, 7)
    data_df['mon'] = simulation_start_date.month 
    data_df['jd'] = simulation_start_date.timetuple().tm_yday 
    data_df['M'] = 0 
    data_df['jd_min'] = 0 

    # --- 关键修改：从 Weather.csv 的第一行读取天气数据，并标准化列名 ---
    weather_df = pd.read_csv(processed_weather_path)
    if not weather_df.empty:
        
        # 定义一个映射，将可能的列名转换为脚本内部使用的标准名称
        weather_col_mapping = {
            'T': 't', 'TMP': 't', 
            'RH': 'rh',
            'WS': 'ws',
            'WD': 'wd',
            'APCP': 'prec', 'prec': 'prec',
            'FFMC': 'ffmc', 'ffmc': 'ffmc',
            'DMC': 'dmc', 'dmc': 'dmc',
            'DC': 'dc', 'dc': 'dc',
            'ISI': 'isi', 'isi': 'isi',
            'BUI': 'bui', 'bui': 'bui',
            'FWI': 'fwi', 'fwi': 'fwi',
            'Waz': 'waz', # 考虑之前的脚本中可能存在的 'Waz'
            'waz': 'waz'
        }
        
        # 将 weather_df 的列名全部转换为小写，并去除首尾空格
        weather_df.columns = weather_df.columns.str.strip().str.lower()
        
        # 准备一个反向映射，将标准化后的列名映射回原始列名
        reverse_mapping = {v: k for k, v in weather_col_mapping.items()}
        
        # 重命名列名以进行标准化
        weather_df = weather_df.rename(columns={col: weather_col_mapping.get(col, col) for col in weather_df.columns})
        
        # 再次确保列名是小写的，以匹配 data_df
        weather_df.columns = weather_df.columns.str.lower()

        weather_row = weather_df.iloc[0]
        
        print("  正在从 Weather.csv 的第一行填充天气数据...")
        
        weather_cols_to_map = {
            'ffmc': 'ffmc',
            'ws': 'ws',
            'wd': 'waz',
            'bui': 'bui'
        }
        
        for weather_col, df_col in weather_cols_to_map.items():
            if weather_col in weather_row:
                data_df[df_col] = weather_row[weather_col]
                print(f"    '{weather_col}' 列找到并已填充。")
            else:
                data_df[df_col] = 0.0
                print(f"    警告：Weather.csv 中缺少 '{weather_col}' 列。已将 '{df_col}' 设为默认值 0.0。请检查您的 Weather.csv。可用列: {weather_row.index.tolist()}")
    else:
        data_df['ffmc'] = 0.0
        data_df['ws'] = 0.0
        data_df['waz'] = 0.0
        data_df['bui'] = 0.0
        print("警告：Weather.csv 为空，已将天气数据设为默认值 0.0。")


    # --- 核心修改：将 'ps' 列的值设置为从 'slope.asc' 文件读取的坡度值 ---
    data_df['ps'] = slope_flat
    print("  'ps' 列已成功从 'slope.asc' 填充。")
    
    data_df['time'] = 0 
    data_df['pattern'] = 20 

    # --- 新增：根据 DataGeneratorC.py 中的逻辑填充 gfl, pdf, pc ---
    # GFL dictionary
    GFLD = {"C1": 0.75, "C2": 0.8, "C3": 1.15, "C4": 1.2, "C5":1.2, "C6":1.2, "C7":1.2, 
            "D1": np.nan, "D2": np.nan, 
            "S1":np.nan, "S2": np.nan, "S3": np.nan, 
            "O1a":0.35, "O1b":0.35, 
            "M1": np.nan, "M2": np.nan, "M3":np.nan, "M4":np.nan, "NF":np.nan, "W":np.nan, 
            "M1_5": 0.1, "M1_10": 0.2,  "M1_15": 0.3, "M1_20": 0.4, "M1_25": 0.5, "M1_30": 0.6, 
            "M1_35": 0.7, "M1_40": 0.8, "M1_45": 0.8, "M1_50": 0.8, "M1_55": 0.8, "M1_60": 0.8, 
            "M1_65": 1.0, "M1_70": 1.0, "M1_75": 1.0, "M1_80": 1.0, "M1_85": 1.0, "M1_90": 1.0, "M1_95": 1.0}
    
    # PDF dictionary
    PDFD ={"M3_5": 5,"M3_10": 10,"M3_15": 15,"M3_20": 20,"M3_25": 25,"M3_30": 30,"M3_35": 35,"M3_40": 40,"M3_45": 45,"M3_50": 50,
           "M3_55": 55,"M3_60": 60,"M3_65": 65,"M3_70": 70,"M3_75": 75,"M3_80": 80,"M3_85": 85,"M3_90": 90,"M3_95": 95,"M4_5": 5,
           "M4_10": 10,"M4_15": 15,"M4_20": 20,"M4_25": 25,"M4_30": 30,"M4_35": 35,"M4_40": 40,"M4_45": 45,"M4_50": 50,"M4_55": 55,
           "M4_60": 60,"M4_65": 65,"M4_70": 70,"M4_75": 75,"M4_80": 80,"M4_85": 85,"M4_90": 90,"M4_95": 95,"M3M4_5": 5,"M3M4_10": 10,
           "M3M4_15": 15,"M3M4_20": 20,"M3M4_25": 25,"M3M4_30": 30,"M3M4_35": 35,"M3M4_40": 40,"M3M4_45": 45,"M3M4_50": 50,"M3M4_55": 55,
           "M3M4_60": 60,"M3M4_65": 65,"M3M4_70": 70,"M3M4_75": 75,"M3M4_80": 80,"M3M4_85": 85,"M3M4_90": 90,"M3M4_95": 95}
    
    # PCD dictionary
    PCD = {"M1_5":5,"M1_10":10,"M1_15":15,"M1_20":20,"M1_25":25,"M1_30":30,"M1_35":35,"M1_40":40,"M1_45":45,
           "M1_50":50,"M1_55":55,"M1_60":60,"M1_65":65,"M1_70":70,"M1_75":75,"M1_80":80,"M1_85":85,"M1_90":90,
           "M1_95":95,"M2_5":5,"M2_10":10,"M2_15":15,"M2_20":20,"M2_25":25,"M2_30":30,"M2_35":35,"M2_40":40,
           "M2_45":45,"M2_50":50,"M2_55":55,"M2_60":60,"M2_65":65,"M2_70":70,"M2_75":75,"M2_80":80,"M2_85":85,
           "M2_90":90,"M2_95":95,"M1M2_5":5,"M1M2_10":10,"M1M2_15":15,"M1M2_20":20,"M1M2_25":25,"M1M2_30":30,
           "M1M2_35":35,"M1M2_40":40,"M1M2_45":45,"M1M2_50":50,"M1M2_55":55,"M1M2_60":60,"M1M2_65":65,"M1M2_70":70,
           "M1M2_75":75,"M1M2_80":80,"M1M2_85":85,"M1M2_90":90,"M1M2_95":95}
    
    data_df['pc'] = np.nan
    data_df['pdf'] = np.nan
    data_df['gfl'] = np.nan

    print("  正在填充 'gfl'...")
    for fuel_type_fbp, value in GFLD.items():
        data_df.loc[data_df['fueltype'] == fuel_type_fbp, 'gfl'] = value
        
    print("  正在填充 'pdf'...")
    for fuel_type_fbp, value in PDFD.items():
        data_df.loc[data_df['fueltype'] == fuel_type_fbp, 'pdf'] = value
    
    print("  正在填充 'pc'...")
    for fuel_type_fbp, value in PCD.items():
        data_df.loc[data_df['fueltype'] == fuel_type_fbp, 'pc'] = value

    print(f"  正在检查 O1a/O1b 燃料类型的 'cur' 值...")
    mask_o1_fuels = data_df['fueltype'].isin(["O1a", "O1b"])
    mask_cur_nan = data_df['cur'].isna()
    data_df.loc[mask_o1_fuels & mask_cur_nan, 'cur'] = 60.0
    print(f"  已为 O1a/O1b 且 cur 为 NaN 的 { (mask_o1_fuels & mask_cur_nan).sum() } 个单元格设置 'cur' 为 60.0。")

    print(f"  正在根据 fueltype (NF, W 等) 将 'cur' 值设置为 NODATA ({nodata_value})...")
    
    non_burnable_fuel_types = ["NF", "W"] 
    mask_non_burnable = data_df['fueltype'].isin(non_burnable_fuel_types)
    
    data_df.loc[mask_non_burnable, 'cur'] = nodata_value
    
    print(f"  已处理 {mask_non_burnable.sum()} 个单元格的 'cur' 值。")

    final_cols = [
        'fueltype', 'mon', 'jd', 'M', 'jd_min', 'lat', 'lon', 'elev',
        'ffmc', 'ws', 'waz', 'bui', 'ps', 'saz', 'pc', 'pdf', 'gfl', 'cur',
        'time', 'pattern'
    ]
    data_df = data_df[final_cols]
    
    for col in data_df.columns:
        if col != 'fueltype' and data_df[col].dtype == np.float64: 
            data_df[col] = data_df[col].fillna(nodata_value) 

    data_df.to_csv(data_csv_output_path, index=False)
    print(f"  Data.csv 已生成并保存到：{os.path.basename(data_csv_output_path)}")
    return True

# --- 检查 Cell2Fire 日志函数 ---
def check_cell2fire_log(log_file_path):
    """
    简单检查 Cell2Fire 的 LogFile.txt，看是否有指示成功的关键信息。
    """
    print("\n--- 检查 Cell2Fire 日志文件 ---")
    if not os.path.exists(log_file_path):
        print(f"错误：Cell2Fire 日志文件 {log_file_path} 不存在。")
        return False
    
    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        log_content = f.read()
    
    if "Simulation finished successfully" in log_content or "Total simulated fires:" in log_content:
        print("  Cell2Fire 模拟可能已成功完成。")
        return True
    else:
        print("  Cell2Fire 模拟可能失败或未完全成功。请检查 LogFile.txt 的详细内容。")
        return False

if __name__ == "__main__":
    # --- 用户配置部分 ---
    project_root = os.path.join(os.getcwd()) 

    output_base_dir = os.path.join(project_root, "Input_Landscape")
    
    cell2fire_main_script_path = os.path.join(project_root, "cell2fire", "main.py") 

    clipped_input_dir = output_base_dir 
    cell2fire_output_dir = os.path.join(output_base_dir, "output_cell2fire") 

    processed_weather_path = os.path.join(output_base_dir, "Weather.csv") # 这里使用你提供的文件名
    processed_firms_path = os.path.join(output_base_dir, "Ignitions.csv") 
    processed_ignition_points_path = os.path.join(output_base_dir, "IgnitionPoints.csv") 
    reclassified_fuel_path = os.path.join(clipped_input_dir, "Forest.asc") 
    data_csv_path = os.path.join(output_base_dir, "Data.csv") 
    log_file_path = os.path.join(cell2fire_output_dir, "LogFile.txt")
    
    fbp_lookup_table_path = os.path.join(output_base_dir, "fbp_lookup_table.csv")

    cell_size_meters = 50 

    os.makedirs(cell2fire_output_dir, exist_ok=True) 

    print("\n" + "="*50)
    print("--- 启动 Cell2Fire 模拟工作流 ---")
    print(" (假设所有输入数据已准备就绪) ")
    print("="*50 + "\n")

    if not generate_data_csv(clipped_input_dir, data_csv_path,
                             reclassified_fuel_path, fbp_lookup_table_path,
                             processed_weather_path): 
        print("Data.csv 生成失败，模拟无法正常进行。")
        exit(1)

    # --- 打印关键 CSV 文件的头部，以便调试 ---
    print("\n--- 调试信息：Data.csv 前5行 ---")
    try:
        print(pd.read_csv(data_csv_path).head().to_string())
    except Exception as e:
        print(f"无法读取或打印 Data.csv：{e}")

    print("\n--- 调试信息：Weather.csv 前5行 ---")
    try:
        weather_df = pd.read_csv(processed_weather_path)
        print(weather_df.head().to_string())
        nweathers = len(weather_df)
        print(f"\nDEBUG: 检测到 Weather.csv 中有 {nweathers} 行数据。")
    except Exception as e:
        print(f"无法读取或打印 Weather.csv：{e}")
        nweathers = 1 

    print("\n--- 调试信息：Ignitions.csv 前5行 ---")
    try:
        print(pd.read_csv(processed_firms_path).head().to_string())
    except Exception as e:
        print(f"无法读取或打印 Ignitions.csv：{e}")
    # --- 调试信息结束 ---

    missing_files = []
    if not os.path.exists(data_csv_path): missing_files.append(data_csv_path)
    if not os.path.exists(os.path.join(clipped_input_dir, 'elevation.asc')): missing_files.append(os.path.join(clipped_input_dir, 'elevation.asc'))
    if not os.path.exists(os.path.join(clipped_input_dir, 'slope.asc')): missing_files.append(os.path.join(clipped_input_dir, 'slope.asc'))
    if not os.path.exists(os.path.join(clipped_input_dir, 'saz.asc')): missing_files.append(os.path.join(clipped_input_dir, 'saz.asc'))
    if not os.path.exists(os.path.join(clipped_input_dir, 'cur.asc')): missing_files.append(os.path.join(clipped_input_dir, 'cur.asc'))
    if not os.path.exists(reclassified_fuel_path): missing_files.append(reclassified_fuel_path)
    if not os.path.exists(processed_weather_path): missing_files.append(processed_weather_path)
    if not os.path.exists(processed_firms_path): missing_files.append(processed_firms_path) 
    if not os.path.exists(processed_ignition_points_path): missing_files.append(processed_ignition_points_path)
    if not os.path.exists(cell2fire_main_script_path): missing_files.append(cell2fire_main_script_path)
    if not os.path.exists(fbp_lookup_table_path): missing_files.append(fbp_lookup_table_path)


    if missing_files:
        print("\n错误：以下一个或多个输入文件缺失，无法运行 Cell2Fire：")
        for f in missing_files:
            print(f"- {f}")
        print("请检查数据是否已正确准备在以下目录：")
        print(f"  - {clipped_input_dir} (ASC 地形/燃料文件)")
        print(f"  - {output_base_dir} (Weather.csv, Ignitions.csv, IgnitionPoints.csv, fbp_lookup_table.csv)")
        print(f"  - 确保 Cell2Fire 的 main.py 脚本存在于: {cell2fire_main_script_path}")
        exit(1)

    relative_input_instance_folder = os.path.relpath(os.path.dirname(data_csv_path), start=project_root)
    if not relative_input_instance_folder.endswith(os.sep):
        relative_input_instance_folder += os.sep

    relative_output_folder = os.path.relpath(cell2fire_output_dir, start=project_root)
    if not relative_output_folder.endswith(os.sep):
        relative_output_folder += os.sep

    cell2fire_command_list = [
        "python", 
        os.path.relpath(cell2fire_main_script_path, start=project_root), 
        "--input-instance-folder", relative_input_instance_folder, 
        "--output-folder", relative_output_folder, 
        "--ignitions", 
        "--sim-years", "1", 
        "--nsims", "14", 
        "--finalGrid",
        "--nweathers", "1", # 暂时改为1个天气文件
        "--Fire-Period-Length", "0.041666666666666664", 
        "--output-messages",
        "--ROS-CV", "0.0", 
        "--seed", "123", 
        "--stats",
        "--allPlots",
        "--IgnitionRad", "10", 
        "--grids",
        "--combine"
    ]
    
    print("\n" + "="*50)
    print("--- 尝试运行 Cell2Fire 模拟 ---")
    print(f"Cell2Fire 命令: {' '.join(cell2fire_command_list)}") 
    print(f" (将在 '{project_root}' 目录下执行)") 
    print("="*50 + "\n")
    
    try:
        result = subprocess.run(cell2fire_command_list, check=False, capture_output=True, text=True, cwd=project_root)
        
        if result.stdout:
            print("Cell2Fire Standard Output:\n", result.stdout)
        if result.stderr:
            print("Cell2Fire Standard Error:\n", result.stderr)
            
        if result.returncode != 0:
            print(f"\n错误：Cell2Fire 进程以非零退出码 {result.returncode} 结束。")
            print("这通常表示模拟失败。请检查上述错误信息或 Cell2Fire 的 LogFile.txt。")
        else:
            print("\nCell2Fire 进程成功结束。")
            
        check_cell2fire_log(log_file_path)

    except FileNotFoundError:
        print(f"\n错误：未找到 Python 解释器或 Cell2Fire 的 main.py 脚本。")
        print(f"请检查 Python 是否已安装且在 PATH 中，以及 main.py 路径是否正确：{cell2fire_main_script_path}")
    except Exception as e:
        print(f"\n运行 Cell2Fire 时发生未知错误: {e}")

    print("\n" + "="*50)
    print("--- Cell2Fire 模拟运行完成 ---")
    print(f"模拟输出日志位于: {log_file_path}")
    print(f"模拟输出文件位于: {cell2fire_output_dir}")
    print("="*50 + "\n")
    print("请检查 Cell2Fire 的 LogFile.txt 和输出文件夹，以验证模拟结果。")