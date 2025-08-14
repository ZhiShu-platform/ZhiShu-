import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import shutil
import subprocess
import warnings
import pyproj
import csv
from osgeo import gdal, osr

# No Warnings
warnings.filterwarnings("ignore")

# --- GDAL TIFF 到 ASC 转换函数 (保持不变) ---
def convert_tif_to_asc(tif_filepath, asc_output_filepath):
    """
    使用gdal_translate将单个tif文件转换为asc文件。
    需要GDAL命令行工具已安装并配置到系统PATH中。
    """
    print(f"开始转换文件：{os.path.basename(tif_filepath)} 到 {os.path.basename(asc_output_filepath)}")
    command = ["gdal_translate", "-of", "AAIGrid", tif_filepath, asc_output_filepath]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"  成功转换: {os.path.basename(tif_filepath)} -> {os.path.basename(asc_output_filepath)}")
        
        # 重要的修改：先清洗，后验证
        clean_asc_header(asc_output_filepath) # <-- 先清洗
        validate_asc_file(asc_output_filepath) # <-- 后验证
        

        print(f"  转换后文件大小: {os.path.getsize(asc_output_filepath) / (1024*1024):.2f} MB")
    except subprocess.CalledProcessError as e:
        print(f"  错误：转换 {os.path.basename(tif_filepath)} 失败。错误信息: {e.stderr.strip()}")
        raise
    except FileNotFoundError:
        print("  错误：未找到 'gdal_translate' 命令。请确保 GDAL 已安装并配置到系统 PATH 中。")
        raise
    except Exception as e:
        print(f"  转换 {os.path.basename(tif_filepath)} 时发生未知错误: {e}")
        raise

# --- 改进的 ASC文件验证函数 (保持不变) ---
def validate_asc_file(asc_filepath):
    """
    验证ASC文件的基本格式和数据完整性，以规避stoi错误。
    检查头信息是否为数字，并简单检查数据行是否有非数字字符。
    """
    print(f"  验证ASC文件: {os.path.basename(asc_filepath)}...")
    try:
        with open(asc_filepath, 'r') as f:
            header_lines = [next(f).strip() for _ in range(6)]
            
            # 1. 验证头信息
            header_keys = ['ncols', 'nrows', 'xllcorner', 'yllcorner', 'cellsize', 'NODATA_value']
            header_values = {}
            for line in header_lines:
                # 使用 split(maxsplit=1) 确保只在第一个空格处分割，处理更多变体
                parts = line.split(maxsplit=1) 
                if len(parts) == 2 and parts[0] in header_keys:
                    try:
                        # 尝试将值转换为浮点数，所有这些都应该是数字，包括整数如ncols/nrows
                        header_values[parts[0]] = float(parts[1])
                    except ValueError:
                        raise ValueError(f"ASC文件头信息格式错误: '{parts[0]}' 的值 '{parts[1]}' 不是有效数字。")
                else:
                    raise ValueError(f"ASC文件头信息格式错误: '{line}' 不符合 'key value' 格式。")
            
            # 检查关键头信息是否存在
            for key in ['ncols', 'nrows', 'cellsize', 'NODATA_value']:
                if key not in header_values:
                    raise ValueError(f"ASC文件头信息缺失关键参数: '{key}'。")

            # 2. 简单检查数据行 (只读少量行以避免大文件内存问题)
            # 检查10行，每行最多100个值，以避免内存溢出和处理时间过长
            for i, line in enumerate(f):
                if i >= 10: break # 只检查前10行数据
                parts = line.split()
                # 限制检查的数值数量，如果一行有太多数据，只检查前100个
                if not all(is_float(p) for p in parts[:100]): 
                    raise ValueError(f"ASC文件数据行包含非数字字符或格式错误 (行 {i+7}): '{line.strip()}'。")
            
        print(f"  ASC文件 {os.path.basename(asc_filepath)} 验证通过。")
    except Exception as e:
        print(f"  错误：ASC文件 {os.path.basename(asc_filepath)} 验证失败：{e}")
        raise # 重新抛出错误，中止脚本

def is_float(value):
    """辅助函数：检查字符串是否可以转换为浮点数"""
    try:
        float(value)
        return True
    except ValueError:
        return False

# --- 改进版：ASC文件头清洗函数 (保持不变) ---
def clean_asc_header(asc_filepath):
    """
    读取ASC文件，严格地重新格式化其头部信息，确保为 'key SPACE value' 格式，
    并处理NODATA_value和整数值。
    """
    print(f"  清洗ASC文件头: {os.path.basename(asc_filepath)}...")
    
    # Define the expected header keys and their corresponding types
    header_specs = {
        'ncols': int,
        'nrows': int,
        'xllcorner': float,
        'yllcorner': float,
        'cellsize': float,
        'NODATA_value': int # Cell2Fire often prefers NODATA as an integer
    }

    original_header_values = {}
    remaining_lines = []

    with open(asc_filepath, 'r') as f_read:
        file_content = f_read.readlines()

    # First pass: try to extract values from the existing header
    for i, line in enumerate(file_content[:6]): # Only process first 6 lines as header
        parts = line.strip().split(maxsplit=1) 
        if len(parts) == 2 and parts[0] in header_specs:
            try:
                # Attempt to convert to the specified type to catch errors early
                original_header_values[parts[0]] = header_specs[parts[0]](float(parts[1]))
            except ValueError:
                print(f"    警告: 无法解析原始头行 '{line.strip()}' 的值。")
        else:
            print(f"    警告: 原始头行 '{line.strip()}' 格式不符合 'key value'。")
            
    # Copy the rest of the file content (data)
    remaining_lines = file_content[6:]

    # Now, reconstruct the header with strict formatting
    new_header_lines = []
    for key in header_specs.keys():
        value = original_header_values.get(key)
        if value is not None:
            new_header_lines.append(f"{key} {value}\n")
        else:
            print(f"    警告: 无法获取 '{key}' 的值，跳过此头行重建。")

    if len(new_header_lines) != 6:
        print("    严重警告: 无法完全重建6行标准ASC头信息。请检查原始文件确保其完整性。")

    # Overwrite the original file with the new, strictly formatted header
    with open(asc_filepath, 'w') as f_write:
        f_write.writelines(new_header_lines)
        f_write.writelines(remaining_lines)
        
    print(f"  ASC文件头清洗完成: {os.path.basename(asc_filepath)}")


# --- 修改后的裁剪函数：新增 set_nodata_value 参数 ---
def clip_raster_to_extent(input_raster_path, output_raster_path, xmin, ymin, xmax, ymax, output_format="GTiff", set_nodata_value=None):
    """
    使用 gdal_translate 裁剪栅格文件到指定地理范围。
    xmin, ymin, xmax, ymax 应是输入栅格坐标系下的坐标 (例如 UTM)。
    输出格式默认为 GTiff。
    set_nodata_value: 如果提供，将此值设置为输出 TIFF 的 NoData 值。
    """
    print(f"\n--- 开始裁剪文件: {os.path.basename(input_raster_path)} ---")
    print(f"  裁剪范围: Xmin={xmin:.2f}, Ymin={ymin:.2f}, Xmax={xmax:.2f}, Ymax={ymax:.2f}")

    command = [
        "gdal_translate",
        "-of", output_format,
        "-projwin", str(xmin), str(ymax), str(xmax), str(ymin),
    ]
    
    if set_nodata_value is not None:
        command.extend(["-a_nodata", str(set_nodata_value)]) # Add -a_nodata option
        print(f"  为输出文件设置 NoData 值: {set_nodata_value}")

    command.extend([input_raster_path, output_raster_path])

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"  成功裁剪: {os.path.basename(input_raster_path)} -> {os.path.basename(output_raster_path)}")
        
        if not os.path.exists(output_raster_path) or os.path.getsize(output_raster_path) == 0:
            raise Exception(f"输出文件 '{output_raster_path}' 生成失败或为空。GDAL stdout: {result.stdout.strip()}")
        
        print(f"  裁剪后文件大小: {os.path.getsize(output_raster_path) / (1024*1024):.2f} MB")
        
        # 验证裁剪是否实际发生 (可选，但推荐用于调试)
        src_ds = gdal.Open(input_raster_path)
        out_ds = gdal.Open(output_raster_path)
        if src_ds and out_ds:
            if src_ds.RasterXSize == out_ds.RasterXSize and src_ds.RasterYSize == out_ds.RasterYSize:
                print("  警告: 裁剪后的栅格尺寸与原始栅格相同。裁剪可能未实际生效，请检查范围。")
        else:
            print("  警告: 无法打开源或目标栅格文件进行尺寸验证。")

    except subprocess.CalledProcessError as e:
        print(f"  错误：裁剪 {os.path.basename(input_raster_path)} 失败。GDAL 错误信息: {e.stderr.strip()}")
        print(f"  GDAL stdout: {e.stdout.strip()}")
        raise
    except FileNotFoundError:
        print("  错误：未找到 'gdal_translate' 命令。请确保 GDAL 已安装并配置到系统 PATH 中。")
        raise
    except Exception as e:
        print(f"  裁剪 {os.path.basename(input_raster_path)} 时发生未知错误: {e}")
        raise

# --- 修改：强制栅格对齐函数，使用临时文件 ---
def force_raster_alignment(reference_filepath, target_filepath):
    """
    将目标栅格文件强制对齐到参考栅格的尺寸、范围和分辨率。
    使用gdal_translate进行裁剪和重采样，并使用临时文件避免输入输出相同的问题。
    """
    print(f"正在将 {os.path.basename(target_filepath)} 对齐到 {os.path.basename(reference_filepath)}")
    
    # 读取参考文件的头部信息
    ref_header = read_asc_header(reference_filepath)
    if not ref_header:
        print(f"错误：无法读取参考文件 {reference_filepath} 的头部信息，无法进行对齐。")
        return False
        
    ref_ncols = int(ref_header['ncols'])
    ref_nrows = int(ref_header['nrows'])
    ref_xllcorner = ref_header['xllcorner']
    ref_yllcorner = ref_header['yllcorner']
    ref_cellsize = ref_header['cellsize']
    ref_nodata = ref_header.get('nodata_value', -9999) # 获取NODATA值
    
    # 计算参考文件的右上角坐标
    ref_ulx = ref_xllcorner
    ref_uly = ref_yllcorner + ref_nrows * ref_cellsize
    ref_lrx = ref_xllcorner + ref_ncols * ref_cellsize
    ref_lry = ref_yllcorner

    # 构建临时输出文件路径
    temp_output_filepath = target_filepath + ".tmp"

    # 构建 gdal_translate 命令，使用参考文件的精确参数
    command = [
        "gdal_translate",
        "-projwin", str(ref_ulx), str(ref_uly), str(ref_lrx), str(ref_lry),
        "-outsize", str(ref_ncols), str(ref_nrows), # 强制输出行列数
        "-tr", str(ref_cellsize), str(ref_cellsize), # 强制输出分辨率
        "-r", "near", # 使用最近邻重采样，避免对分类数据（如燃料）产生平均值
        "-a_nodata", str(ref_nodata), # 确保NODATA值一致
        "-of", "AAIGrid",
        target_filepath,
        temp_output_filepath # 保存到临时文件
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"  成功对齐并保存到临时文件: {os.path.basename(target_filepath)} -> {os.path.basename(temp_output_filepath)}")
        if result.stderr:
            print(f"  对齐过程警告/信息: {result.stderr}")
        
        # 替换原始文件
        if os.path.exists(temp_output_filepath):
            if os.path.exists(target_filepath):
                os.remove(target_filepath) # 删除旧文件
            os.rename(temp_output_filepath, target_filepath) # 重命名临时文件
            print(f"  成功将对齐后的文件替换为: {os.path.basename(target_filepath)}")
            
            # 清洗并验证对齐后的文件头部
            clean_asc_header(target_filepath)
            validate_asc_file(target_filepath)
            return True
        else:
            print(f"错误：临时文件 {os.path.basename(temp_output_filepath)} 未生成。对齐失败。")
            return False

    except subprocess.CalledProcessError as e:
        print(f"错误：强制对齐 {os.path.basename(target_filepath)} 失败。命令: {' '.join(command)}")
        print(f"  Stdout: {e.stdout}")
        print(f"  Stderr: {e.stderr}")
        # 清理可能残留的临时文件
        if os.path.exists(temp_output_filepath):
            os.remove(temp_output_filepath)
        return False
    except Exception as e:
        print(f"对齐 {os.path.basename(target_filepath)} 时发生未知错误: {e}")
        # 清理可能残留的临时文件
        if os.path.exists(temp_output_filepath):
            os.remove(temp_output_filepath)
        return False
        
# --- 燃料模型重分类函数（新增对文件头的检查）(保持不变) ---
def reclassify_fuel_model_in_memory(fbfm13_asc_path):
    print("\n开始在内存中重分类燃料模型...")
    try:
        with open(fbfm13_asc_path, 'r') as f:
            header = [next(f) for _ in range(6)] # 读取ASC头信息
            # 再次验证header，确保后续np.loadtxt不会因为错误的header而失败
            validate_asc_file_header_only(fbfm13_asc_path) # 新增头信息验证
            data = np.loadtxt(f) # 加载栅格数据
    except FileNotFoundError:
        print(f"错误：未找到FBFM13文件：{fbfm13_asc_path}。请检查路径。")
        raise
    except Exception as e:
        print(f"读取FBFM13文件时发生错误：{e}")
        raise

    reclass_map = {
        1: 31, 2: 32, 3: 50, 4: 40, 5: 1, 6: 11, 7: 12,
        8: 1, 9: 4, 10: 2, 11: 5, 12: 6, 13: 7,
        -9999: -9999, 91: 23, 92: 102, 93: 5, 98: 102, 99: 101,0:-9999
    }
    
    fbp_data = data.copy()
    for original_val, new_val in reclass_map.items():
        fbp_data[data == original_val] = new_val
    
    all_known_keys = list(reclass_map.keys())
    mask_unknown = ~np.isin(data, all_known_keys)
    fbp_data[mask_unknown] = 0

    temp_fbp_path = os.path.join(os.getcwd(), "fuel_fbp_processed_reclassified.asc")
    with open(temp_fbp_path, 'w') as f:
        f.writelines(header) # 写入原始（已清洗过的）头信息
        # 确保输出的数据类型与Cell2Fire预期一致，例如整数。
        # 如果FBP模型需要整数，fmt='%d' 是正确的。
        np.savetxt(f, fbp_data, fmt='%d', delimiter=' ')
        
    print(f"燃料模型重分类完成，已保存为临时文件: {temp_fbp_path}")
    print(f"重分类后燃料文件大小: {os.path.getsize(temp_fbp_path) / (1024*1024):.2f} MB")
    return temp_fbp_path

# --- 新增：仅验证ASC文件头信息函数 (保持不变) ---
def validate_asc_file_header_only(asc_filepath):
    """
    仅验证ASC文件的头信息是否为数字，避免重复加载整个文件数据。
    """
    try:
        with open(asc_filepath, 'r') as f:
            header_lines = [next(f).strip() for _ in range(6)]
            header_keys = ['ncols', 'nrows', 'xllcorner', 'yllcorner', 'cellsize', 'NODATA_value']
            
            for line in header_lines:
                parts = line.split(maxsplit=1) # 使用split(maxsplit=1)处理任意数量的空格
                if len(parts) == 2 and parts[0] in header_keys:
                    try:
                        float(parts[1]) # 尝试转换为浮点数
                    except ValueError:
                        raise ValueError(f"ASC文件头信息格式错误: '{parts[0]}' 的值 '{parts[1]}' 不是有效数字。")
                else:
                    raise ValueError(f"ASC文件头信息格式错误: '{line}' 不符合 'key value' 格式。")
            
    except Exception as e:
        print(f"  错误：ASC文件 {os.path.basename(asc_filepath)} 头信息验证失败：{e}")
        raise
        
# =============================================================================
# --- FWI 官方逻辑的每日 FWI 计算函数 (已根据FWI.pdf文献完全重写) ---
# =============================================================================
def calculate_daily_fwi(weather_df_daily, initial_fwi_params):
    """
    根据每日气象数据计算 FWI 指数。此函数严格遵循 FWI.pdf 文档中的官方方程和程序。
    
    参数:
    weather_df_daily: 包含每日气象数据的 DataFrame，列名必须为 'T', 'H', 'W', 'P' 和 'month'。
    initial_fwi_params: 包含初始 'ffmc', 'dmc', 'dc' 值的字典。
    
    返回:
    包含所有每日 FWI 指数的 DataFrame。
    """
    print("  开始使用 FWI.pdf 文档中的官方逻辑计算每日 FWI 指数...")

    # FWI.pdf 表1和表2中的有效日长因子
    # Effective day-lengths (Le) for DMC and Day-length factors (Lf) for DC from Tables 1 & 2 in FWI.pdf
    EL = [6.5, 7.5, 9.0, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8.0, 7.0, 6.0]
    FL = [-1.6, -1.6, -1.6, 0.9, 3.8, 5.8, 6.4, 5.0, 2.4, 0.4, -1.6, -1.6]

    weather_df = weather_df_daily.copy()

    ffmc_yda = initial_fwi_params['ffmc']
    dmc_yda = initial_fwi_params['dmc']
    dc_yda = initial_fwi_params['dc']
    
    fwi_outputs = []

    for index, row in weather_df.iterrows():
        T = row['T']
        H = row['H']
        W = row['W']
        P = row['P']
        # 确保月份是整数
        month = int(row['month'])

        # --- FFMC (Fine Fuel Moisture Code) Calculation ---
        mo = 147.2 * (101.0 - ffmc_yda) / (59.5 + ffmc_yda)
        
        if P > 0.5:
            rf = P - 0.5
            if mo <= 150.0:
                mr = mo + 42.5 * rf * np.exp(-100.0 / (251.0 - mo)) * (1.0 - np.exp(-6.93 / rf))
            else:
                mr = mo + 42.5 * rf * np.exp(-100.0 / (251.0 - mo)) * (1.0 - np.exp(-6.93 / rf)) + 0.0015 * (mo - 150.0)**2 * np.sqrt(rf)
            if mr > 250.0:
                mr = 250.0
            mo = mr
        
        Ed = 0.942 * (H**0.679) + 11.0 * np.exp((H - 100.0) / 10.0) + 0.18 * (21.1 - T) * (1.0 - np.exp(-0.115 * H))
        Ew = 0.618 * (H**0.753) + 10.0 * np.exp((H - 100.0) / 10.0) + 0.18 * (21.1 - T) * (1.0 - np.exp(-0.115 * H))
        
        if mo > Ed:
            ko = 0.424 * (1.0 - (H / 100.0)**1.7) + 0.0694 * np.sqrt(W) * (1.0 - (H / 100.0)**8)
            kd = ko * 0.581 * np.exp(0.0365 * T)
            m = Ed + (mo - Ed) * (10.0**(-kd))
        elif mo < Ew:
            k1 = 0.424 * (1.0 - ((100.0 - H) / 100.0)**1.7) + 0.0694 * np.sqrt(W) * (1.0 - ((100.0 - H) / 100.0)**8)
            kw = k1 * 0.581 * np.exp(0.0365 * T)
            m = Ew - (Ew - mo) * (10.0**(-kw))
        else:
            m = mo
            
        ffmc_next = (59.5 * (250.0 - m)) / (147.2 + m)
        ffmc_next = min(ffmc_next, 101.0)
        
        # --- DMC (Duff Moisture Code) Calculation ---
        if T < -1.1: T_dmc = -1.1 
        else: T_dmc = T
        Le = EL[month - 1]
        K = 1.894 * (T_dmc + 1.1) * (100.0 - H) * Le * 1e-6
        if P > 1.5:
            re = 0.92 * P - 1.27
            mo_dmc = 20.0 + np.exp(5.6348 - dmc_yda / 43.43)
            if dmc_yda <= 33: b = 100.0 / (0.5 + 0.3 * dmc_yda)
            elif dmc_yda <= 65: b = 14.0 - 1.3 * np.log(dmc_yda)
            else: b = 6.2 * np.log(dmc_yda) - 17.2
            mr_dmc = mo_dmc + (1000.0 * re) / (48.77 + b * re)
            pr = 244.72 - 43.43 * np.log(mr_dmc - 20.0)
            if pr < 0: pr = 0.0
            dmc_next = pr + 100.0 * K
        else:
            dmc_next = dmc_yda + 100.0 * K
        
        # --- DC (Drought Code) Calculation ---
        if T < -2.8: T_dc = -2.8
        else: T_dc = T
        Lf = FL[month - 1]
        V = 0.36 * (T_dc + 2.8) + Lf
        if V < 0: V = 0.0
        if P > 2.8:
            rd = 0.83 * P - 1.27
            Qo = 800.0 * np.exp(-dc_yda / 400.0)
            Qr = Qo + 3.937 * rd
            dr = 400.0 * np.log(800.0 / Qr)
            if dr < 0: dr = 0.0
            dc_next = dr + 0.5 * V
        else:
            dc_next = dc_yda + 0.5 * V
            
        # --- ISI, BUI, FWI Calculation ---
        fW = np.exp(0.05039 * W)
        m_isi = 147.2 * (101.0 - ffmc_next) / (59.5 + ffmc_next)
        fF = 91.9 * np.exp(-0.1386 * m_isi) * (1.0 + m_isi**5.31 / 4.93e7)
        isi = 0.208 * fW * fF

        if dmc_next == 0 and dc_next == 0:
            bui = 0.0
        elif dmc_next <= 0.4 * dc_next:
            bui = (0.8 * dc_next * dmc_next) / (dmc_next + 0.4 * dc_next)
        else:
            bui = dmc_next - (1.0 - 0.8 * dc_next / (dmc_next + 0.4 * dc_next)) * (0.92 + (0.0114 * dmc_next)**1.7)
        if bui < 0: bui = 0.0

        if bui <= 80.0:
            fD = 0.626 * bui**0.809 + 2.0
        else:
            fD = 1000.0 / (25.0 + 108.64 * np.exp(-0.023 * bui))
        B = 0.1 * isi * fD
        
        if B > 1.0:
            fwi = np.exp(2.72 * (0.434 * np.log(B))**0.647)
        else:
            fwi = B

        ffmc_yda, dmc_yda, dc_yda = ffmc_next, dmc_next, dc_next
        fwi_outputs.append([ffmc_next, dmc_next, dc_next, isi, bui, fwi])

    print("  每日 FWI 指数计算完成。")
    return pd.DataFrame(fwi_outputs, columns=['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI'])

# =============================================================================
# --- NOAA 数据处理函数 (已彻底修复数据类型和文件写入问题) ---
# =============================================================================
def process_noaa_to_fwi_stream(noaa_csv_path, scenario_name="DEFAULT_SCENARIO"):
    """
    将 NOAA 天气数据处理为符合官方 Cell2Fire 示例 Weather.csv 格式的数据流。
    此版本使用 FWI 官方逻辑根据每日气象数据计算 FWI 指数，然后用每日值填充每小时数据。
    """
    print(f"\n开始处理NOAA天气数据，文件：{os.path.basename(noaa_csv_path)}...")
    try:
        df = pd.read_csv(noaa_csv_path)
    except Exception as e:
        print(f"读取NOAA文件时发生错误：{e}")
        raise

    # 数据预处理
    df[['TAVG', 'AWND', 'WDFG', 'PRCP']] = df[['TAVG', 'AWND', 'WD', 'PRCP']].fillna(0)
    
    df['DATE'] = pd.to_datetime(df['DATE'])
    df.set_index('DATE', inplace=True)
    
    # 确保索引是 DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("处理后的DataFrame索引不是DatetimeIndex")

    # 准备每日 FWI 计算所需的列
    df['T'] = df['TAVG'] / 10.0
    df['W'] = df['AWND'] 
    df['P'] = df['PRCP'] / 10.0
    df['month'] = df.index.month
    df['H'] = np.interp(df['T'], [0, 10, 20, 30], [80, 60, 40, 30]).clip(20, 90)
    
    fwi_input_daily = df[['T', 'H', 'W', 'P', 'month']]
    
    # 使用您的 FWI 计算函数
    initial_fwi_params = {'ffmc': 85.0, 'dmc': 50.0, 'dc': 200.0}
    fwi_output_daily = calculate_daily_fwi(fwi_input_daily, initial_fwi_params)
    fwi_output_daily.index = fwi_input_daily.index
    
    # 合并每日数据
    df_daily_combined = df.join(fwi_output_daily)

    # 创建每小时时间序列并进行前向填充
    df_hourly = df_daily_combined.resample('h').ffill()
    
    # ------------------- 核心修正部分 -------------------
    # 筛选从1月7日00:00到1月8日00:00的数据
    # 使用 .loc[start_date:end_date] 语法进行切片
    df_hourly = df_hourly.loc['2025-01-07 00:00':'2025-01-08 00:00']

    # 确保没有NaN值
    df_hourly = df_hourly.fillna(0)

    # 准备最终的输出DataFrame
    weather_stream_df = pd.DataFrame({
        'Scenario': [scenario_name] * len(df_hourly),
        # 直接使用每小时索引作为datetime列
        'datetime': df_hourly.index,
        'APCP': df_hourly['P'] / 24.0,
        'TMP': df_hourly['T'],
        'RH': df_hourly['H'],
        'WS': df_hourly['W'],
        'WD': df_hourly['WDFG'],
        'FFMC': df_hourly['FFMC'],
        'DMC': df_hourly['DMC'],
        'DC': df_hourly['DC'],
        'ISI': df_hourly['ISI'] * 10,
        'BUI': df_hourly['BUI'] * 2,
        'FWI': df_hourly['FWI'] * 8
    })
    
    # 确保 datetime 列的格式与官方示例一致
    weather_stream_df['datetime'] = weather_stream_df['datetime'].dt.strftime('%Y-%m-%d %H:%M')

    # 在写入文件之前，将所有数值列强制转换为浮点数类型
    numeric_cols = ['APCP', 'TMP', 'RH', 'WS', 'WD', 'FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']
    for col in numeric_cols:
        if col in weather_stream_df.columns:
            # 强制类型转换，处理非数字值
            weather_stream_df[col] = pd.to_numeric(weather_stream_df[col], errors='coerce').fillna(0)
    
    temp_weather_path = os.path.join(os.getcwd(), "weather_processed.csv")
    
    # 使用 quoting=csv.QUOTE_NONE 彻底移除所有引号
    # 将 float_format 设置为 '%.1f' 以保留一位小数
    weather_stream_df.to_csv(temp_weather_path, index=False, quoting=csv.QUOTE_NONE, escapechar=' ', float_format='%.1f')
    
    print(f"天气数据处理完成，已保存为临时文件: {temp_weather_path}")
    print(f"新文件的列名已调整为：{weather_stream_df.columns.tolist()}")
    return temp_weather_path


# --- Helper to read ASC header values ---
def get_asc_header_info(asc_filepath):
    """Reads ncols, nrows, xllcorner, yllcorner, cellsize from an ASC file."""
    header_info = {}
    with open(asc_filepath, 'r') as f:
        for _ in range(6):
            line = next(f).strip()
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                try:
                    header_info[parts[0]] = float(parts[1]) # Read as float, convert to int where necessary later
                except ValueError:
                    raise ValueError(f"Error parsing ASC header line: {line}")
            else:
                raise ValueError(f"Malformed ASC header line: {line}")
    header_info['ncols'] = int(header_info['ncols'])
    header_info['nrows'] = int(header_info['nrows'])
    header_info['cellsize'] = float(header_info['cellsize'])
    return header_info


# --- FIRMS 数据处理与点火点文件生成 (修改后) ---
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
    # Calculate column and row indices
    # col = (X - xllcorner) / cellsize
    # row = (Y - yllcorner) / cellsize
    # Rows are usually indexed from top (0) to bottom (nrows-1) in raster,
    # while yllcorner is the bottom-left. So we need to convert Y to a top-indexed row.
    
    filtered_ignitions['col'] = np.floor((filtered_ignitions['X_proj'] - xllcorner) / cellsize).astype(int)
    filtered_ignitions['row_from_bottom'] = np.floor((filtered_ignitions['Y_proj'] - yllcorner) / cellsize).astype(int)
    
    # Convert row from bottom to row from top
    filtered_ignitions['row'] = nrows - 1 - filtered_ignitions['row_from_bottom']

    # Filter out points that might fall outside due to precision or being exactly on edge
    filtered_ignitions = filtered_ignitions[
        (filtered_ignitions['col'] >= 0) & (filtered_ignitions['col'] < ncols) &
        (filtered_ignitions['row'] >= 0) & (filtered_ignitions['row'] < nrows)
    ].copy()

    if filtered_ignitions.empty:
        print(f"警告：所有点火点在转换为栅格单元后，均不在有效范围内。请检查坐标转换和栅格参数。")
        return None

    # Calculate Ncell (0-indexed or 1-indexed based on Cell2Fire's actual requirement)
    # The example Ncell suggests 1-indexed, so let's try 1-indexed.
    filtered_ignitions['Ncell'] = (filtered_ignitions['row'] * ncols + filtered_ignitions['col']) + 1

    # Prepare DataFrame for ignitions.csv and IgnitionPoints.csv
    # The example used 'Year' column, corresponding to 'sim-years 1'
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

# --- Cell2Fire日志文件检查函数 (保持不变) ---
def check_cell2fire_log(log_filepath):
    """
    检查Cell2Fire的LogFile.txt，寻找常见的错误指示。
    """
    print(f"\n--- 检查 Cell2Fire 日志文件: {os.path.basename(log_filepath)} ---")
    if not os.path.exists(log_filepath):
        print("  日志文件不存在，无法检查。")
        return False
    
    error_keywords = [
        "ERROR", "error", "failed", "invalid argument", "stoi", "not found",
        "file does not exist", "failed to open", "segmentation fault",
        "invalid_argument" # Explicitly added for clarity
    ]
    
    found_error = False
    with open(log_filepath, 'r') as f:
        for line_num, line in enumerate(f):
            for keyword in error_keywords:
                if keyword in line.lower():
                    print(f"  日志中发现潜在错误 (行 {line_num+1}): {line.strip()}")
                    found_error = True
    
    if found_error:
        print(f"\n  警告：Cell2Fire 日志文件 '{os.path.basename(log_filepath)}' 中发现错误信息。请仔细检查该文件以获取详细信息。")
        return True
    else:
        print("  日志文件中未发现明显的错误关键字。")
        return False


# --- 主运行脚本 ---
def run_cell2fire_simulation():
    # --- 配置参数 ---
    cell2fire_root_dir = "/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/" 
    input_instance_folder = os.path.join(cell2fire_root_dir, "Input_Landscape") 
    os.makedirs(input_instance_folder, exist_ok=True)

    output_folder = os.path.join(cell2fire_root_dir, "output_cell2fire")
    os.makedirs(output_folder, exist_ok=True)

    # 原始 TIFF 文件路径
    original_dem_tif = os.path.join(input_instance_folder, "resampled_dem50.tif")
    original_slope_tif = os.path.join(input_instance_folder, "resampled_slope50.tif")
    original_aspect_tif = os.path.join(input_instance_folder, "resampled_saz50.tif")
    original_fbfm_tif = os.path.join(input_instance_folder, "resampled_LF50.tif")

    # 裁剪后的 TIFF 临时文件路径
    clipped_dem_tif_temp = os.path.join(input_instance_folder, "elevation_clipped.tif")
    clipped_slope_tif_temp = os.path.join(input_instance_folder, "slope_clipped.tif")
    clipped_aspect_tif_temp = os.path.join(input_instance_folder, "saz_clipped.tif")
    clipped_fbfm_tif_temp = os.path.join(input_instance_folder, "fbfm13_clipped.tif")

    # 最终的 ASC 文件路径 (供 Cell2Fire 使用)
    dem_asc_final = os.path.join(input_instance_folder, "elevation.asc")
    slope_asc_final = os.path.join(input_instance_folder, "slope.asc")
    aspect_asc_final = os.path.join(input_instance_folder, "saz.asc")
    fuel_asc_final = os.path.join(input_instance_folder, "Forest.asc")
    cropped_cur_path = os.path.join(input_instance_folder, "cur.asc")
    # NOAA 和 FIRMS 数据路径
    noaa_raw_csv_file = "/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/Input_Landscape/Weather_SingleStation.csv"
    firms_data_csv = "/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/Input_Landscape/fire_archive_M-C61_106125.csv"

    # 模拟时间范围 (1月7号到1月25号)
    sim_start_date = "2025-01-07"
    sim_end_date = "2025-01-25"
    start_dt = datetime.strptime(sim_start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(sim_end_date, '%Y-%m-%d')
    total_sim_days = (end_dt - start_dt).days + 1
    total_sim_hours = total_sim_days * 24

    # 定义坐标转换器 (WGS84 到 UTM zone 11N)
    target_utm_srs = "EPSG:26911" # NAD83 / UTM zone 11N
    transformer_wgs84_to_utm = pyproj.Transformer.from_crs("epsg:4326", target_utm_srs, always_xy=True)

    # --- 1. 手动设置精确的裁剪范围 (UTM 坐标) ---
    # 根据2025年1月南加州山火的维基百科信息确定的范围
    fixed_crop_xmin = 330000 
    fixed_crop_xmax = 360000 
    fixed_crop_ymin = 3740000 
    fixed_crop_ymax = 3770000 
    
    # 增加一个小的缓冲区，确保覆盖边界
    buffer_for_fixed_range = 10000 # 例如 10 公里缓冲区
    crop_xmin = fixed_crop_xmin - buffer_for_fixed_range
    crop_xmax = fixed_crop_xmax + buffer_for_fixed_range
    crop_ymin = fixed_crop_ymin - buffer_for_fixed_range
    crop_ymax = fixed_crop_ymax + buffer_for_fixed_range

    print("\n--- 裁剪范围手动设置 ---")
    print(f"  手动设置的裁剪范围 (UTM, 含 {buffer_for_fixed_range/1000:.0f}km 缓冲区):")
    print(f"  X [{crop_xmin:.2f}, {crop_xmax:.2f}], Y [{crop_ymin:.2f}, {crop_ymax:.2f}]")

    # 打印原始 DEM 的范围进行对比，便于调试
    print("\n  --- 原始 DEM (resampled_dem30.tif) 范围 (从 gdalinfo) ---")
    src_ds_original = gdal.Open(original_dem_tif)
    if src_ds_original:
        gt_original = src_ds_original.GetGeoTransform()
        ulx_orig = gt_original[0]
        uly_orig = gt_original[3]
        lrx_orig = gt_original[0] + src_ds_original.RasterXSize * gt_original[1]
        lry_orig = gt_original[3] + src_ds_original.RasterYSize * gt_original[5]
        print(f"    原始 DEM X 范围: [{ulx_orig:.2f}, {lrx_orig:.2f}]")
        print(f"    原始 DEM Y 范围: [{lry_orig:.2f}, {uly_orig:.2f}] (注意：Y轴是 LRY 到 ULY)")
        src_ds_original = None
    else:
        print(f"    无法读取原始 DEM 文件: {original_dem_tif}，跳过原始范围打印。")

    # --- 2. 裁剪原始 TIFF 景观数据（使用手动确定的范围）---
    print("\n--- 开始裁剪原始 TIFF 景观文件 ---")
    try:
        print(f"原始 DEM 文件大小: {os.path.getsize(original_dem_tif) / (1024*1024):.2f} MB")
        # For DEM, it's often common to have a NODATA value, let's assume -9999
        clip_raster_to_extent(original_dem_tif, clipped_dem_tif_temp, crop_xmin, crop_ymin, crop_xmax, crop_ymax, output_format="GTiff", set_nodata_value=-9999)
        
        print(f"原始 Slope 文件大小: {os.path.getsize(original_slope_tif) / (1024*1024):.2f} MB")
        # Slope also often has NODATA
        clip_raster_to_extent(original_slope_tif, clipped_slope_tif_temp, crop_xmin, crop_ymin, crop_xmax, crop_ymax, output_format="GTiff", set_nodata_value=-9999)
        
        print(f"原始 Aspect 文件大小: {os.path.getsize(original_aspect_tif) / (1024*1024):.2f} MB")
        # THIS IS THE KEY FIX FOR SAZ: Explicitly set NODATA_value
        clip_raster_to_extent(original_aspect_tif, clipped_aspect_tif_temp, crop_xmin, crop_ymin, crop_xmax, crop_ymax, output_format="GTiff", set_nodata_value=-9999)
        
        print(f"原始 FBFM 文件大小: {os.path.getsize(original_fbfm_tif) / (1024*1024):.2f} MB")
        # Fuel models usually have 0 as NODATA, or -9999. Use -9999 if it's consistent.
        # Note: reclassify_fuel_model_in_memory also handles -9999 and maps to 0.
        clip_raster_to_extent(original_fbfm_tif, clipped_fbfm_tif_temp, crop_xmin, crop_ymin, crop_xmax, crop_ymax, output_format="GTiff", set_nodata_value=-9999)        
        print("--- TIFF 景观文件裁剪完成 ---")
    except Exception as e:
        print(f"TIFF 景观文件裁剪失败: {e}")
        return

    # --- 3. 将裁剪后的 TIFF 转换为最终的 ASC 文件 ---
    print("\n--- 开始转换裁剪后的 TIFF 到 ASC 格式 ---")
    try:
        # 每个转换调用都包含验证和清洗头部，确保ASC文件格式正确
        convert_tif_to_asc(clipped_dem_tif_temp, dem_asc_final)
        convert_tif_to_asc(clipped_slope_tif_temp, slope_asc_final)
        convert_tif_to_asc(clipped_aspect_tif_temp, aspect_asc_final)
        # Fuel model input also converted to ASC and then cleaned
        convert_tif_to_asc(clipped_fbfm_tif_temp, os.path.join(input_instance_folder, "fbfm13_input.asc"))
        # --- 新增步骤：强制对齐所有裁剪后的栅格文件 ---
        #print("\n--- 强制对齐所有裁剪后的栅格文件到 Forest.asc 基准 ---")
        #reference_file_for_alignment = os.path.join(input_instance_folder, "fbfm13_input.asc") # 以 Forest.asc 作为对齐基准
    
        #files_to_force_align = [
            #dem_asc_final, # target, output (overwrite original clipped)
            #slope_asc_final,
            #aspect_asc_final,
            #cropped_cur_path
        #]
    
        #for target_path, output_path in files_to_force_align:
            #if os.path.exists(target_path):
                #force_raster_alignment(reference_file_for_alignment, target_path)
            #else:
                #print(f"警告：文件 {os.path.basename(target_path)} 不存在，跳过对齐。")     
        print("--- 裁剪后的 TIFF 文件转换 ASC 完成 ---")
    except Exception as e:
        print(f"转换裁剪后的 TIFF 文件到 ASC 失败: {e}")
        return

    # --- 4. 重分类燃料模型 ---
    print("\n--- 开始重分类裁剪后的燃料模型 ---")
    try:
        # reclassify_fuel_model_in_memory 会加载已经清洗过的 fbfm13_input.asc
        # 然后它将 Forest.asc 写为整数格式，因此这里不需要额外的清洗
        processed_fbp_file_temp = reclassify_fuel_model_in_memory(os.path.join(input_instance_folder, "fbfm13_input.asc")) 
        shutil.move(processed_fbp_file_temp, fuel_asc_final)
        print(f"已将重分类后的燃料文件覆盖到 {fuel_asc_final}")
    except Exception as e:
        print(f"燃料模型重分类失败: {e}")
        return

    # --- 5. 清理裁剪生成的临时 TIFF 文件和 fbfm13_input.asc ---
    print("\n--- 开始清理临时文件 ---")
    try:
        os.remove(clipped_dem_tif_temp)
        os.remove(clipped_slope_tif_temp)
        os.remove(clipped_aspect_tif_temp)
        os.remove(clipped_fbfm_tif_temp)
        os.remove(os.path.join(input_instance_folder, "fbfm13_input.asc"))
        print("--- 临时文件清理完成 ---")
    except Exception as e:
        print(f"清理临时文件失败: {e}")

    # --- 6. 处理 NOAA 天气数据 ---
    print("\n--- 开始处理 NOAA 天气数据 ---")
    try:
        processed_weather_file_temp = process_noaa_to_fwi_stream(noaa_raw_csv_file)
        shutil.copy(processed_weather_file_temp, os.path.join(input_instance_folder, "Weather.csv"))
        print(f"已将处理后的天气文件 {processed_weather_file_temp} 复制为 {os.path.join(input_instance_folder, 'Weather.csv')}")
        os.remove(processed_weather_file_temp)
    except Exception as e:
        print(f"天气数据处理失败: {e}")
        return

    # 7. 处理 FIRMS 点火点（现在根据手动裁剪范围筛选，并生成 Ncell 格式）
    print("\n--- 开始处理 FIRMS 点火点（基于手动裁剪范围筛选并转换为 Ncell 格式）---")
    try:
        # Pass an existing ASC file path to read its header for Ncell calculation
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

    # --- 8. 构建 Cell2Fire 运行命令 ---
    # 定义 Cell2Fire 的主脚本路径
    cell2fire_main_script = os.path.join(cell2fire_root_dir, 'cell2fire', 'main.py')

    # 定义 PYTHONPATH，使其包含 Cell2Fire-main 的父目录
    # 这样 Python 就能找到 'cell2fire' 包
    # 如果 cell2fire_root_dir 是 /data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/
    # 那么需要把 /data/Tiaozhanbei/Cell2Fire/ 加入 PYTHONPATH
    # 或者直接把 cell2fire_root_dir 本身加入 PYTHONPATH，因为它包含了 cell2fire 模块
    # 我们选择后者，更直接
    python_path_env = os.environ.copy() # 复制当前环境变量
    # 确保 cell2fire_root_dir 在 PYTHONPATH 中
    # 如果你的系统上已经有 PYTHONPATH，请确保追加而不是覆盖
    if 'PYTHONPATH' in python_path_env:
        python_path_env['PYTHONPATH'] = f"{cell2fire_root_dir}:{python_path_env['PYTHONPATH']}"
    else:
        python_path_env['PYTHONPATH'] = cell2fire_root_dir


    cell2fire_command_list = [
        "python",
        cell2fire_main_script,
        "--input-instance-folder", f"{input_instance_folder}/",
        "--output-folder", output_folder,
        "--ignitions",
        "--sim-years", "1",
        "--nsims", "14",
        "--grids",
        "--finalGrid",
        "--weather", "rows",
        "--nweathers", "1",
        "--Fire-Period-Length", str(1/24.0),
        "--output-messages",
        "--ROS-CV", "0.0",
        "--seed", "123",
        "--IgnitionRad", "5",
        "--stats"
    ]

    print("\n" + "="*50)
    print("--- 所有数据准备完成！尝试运行 Cell2Fire 命令 ---")
    print("="*50 + "\n")
    # 为了清晰起见，打印出完整的命令
    print(" ".join(cell2fire_command_list)) 
    print(f"使用的 PYTHONPATH: {python_path_env['PYTHONPATH']}")
    
    try:
        # 使用 check=False，因为我们希望捕获C++的错误码，而不是立即抛出Python异常
        # 传递修改后的环境变量给 subprocess.run
        result = subprocess.run(cell2fire_command_list, check=False, capture_output=True, text=True, env=python_path_env)
        
        # 打印Cell2Fire的标准输出和标准错误
        if result.stdout:
            print("Cell2Fire Standard Output:\n", result.stdout)
        if result.stderr:
            print("Cell2Fire Standard Error:\n", result.stderr)
            
        # 检查返回码
        if result.returncode != 0:
            print(f"\n错误：Cell2Fire 进程以非零退出码 {result.returncode} 结束。")
            print("这通常表示模拟失败。请检查上述错误信息或 Cell2Fire 的日志文件。")
            
        # 无论成功与否，都检查Cell2Fire的日志文件
        log_file_path = os.path.join(output_folder, "LogFile.txt")
        if check_cell2fire_log(log_file_path):
            print("\n**重要提示：请务必打开并仔细阅读 Cell2Fire 的 LogFile.txt 获取详细错误信息！**")
        
    except FileNotFoundError:
        print("错误：未找到 'python' 命令或 Cell2Fire 的 'main.py' 脚本。请检查路径。")
    except Exception as e:
        print(f"运行 Cell2Fire 模拟时发生未知错误: {e}")

    print("\n" + "="*50)
    print("--- 所有数据准备完成！请在您的终端中运行以下 Cell2Fire 命令 ---")
    print("="*50 + "\n")
    print(cell2fire_command)
    print("\n" + "="*50)
    print("--- 后续重要步骤提醒 ---")
    print("="*50 + "\n")
    print(f"1. **替换裁剪范围：** 再次提醒，请务必根据您选择的南加州特定火灾的真实蔓延范围，在脚本中替换 `fixed_crop_xmin` 等的**示例值**。这些值应是 **UTM Zone 11N (EPSG:26911) 坐标**。")
    print(f"2. **手动获取裁剪范围的方法：** 建议使用 QGIS 加载原始 DEM 和您找到的火灾边界文件 (SHP/KML)。将所有图层统一到 `EPSG:26911`，然后查看火灾边界图层的属性，获取其在 UTM 坐标系下的范围。在这些范围基础上，再增加一个 5-10 公里（5000-10000米）的缓冲区，将其作为 `fixed_crop_xmin` 等的值。")
    print(f"3. **火点与裁剪区域：** `prepare_ignition_file` 函数现在会根据你设定的裁剪范围来筛选火点。请确保你设定的裁剪范围确实包含了你想要模拟的那场火灾的起火点。如果没有点火点落在范围内，模拟将无法启动。")
    print("4. **文件大小：** 运行脚本后，请检查 `Input_Landscape` 文件夹中 `elevation.asc`, `slope.asc`, `saz.asc`, `Forest.asc` 的文件大小。裁剪后的 TIFF 文件 (例如 `elevation_clipped.tif`) 应该显著小于原始 TIFF，如果最终的 ASC 文件比裁剪后的 TIFF 大，这是由于格式转换的特性。")
    print("5. **GDAL 安装：** 确保你已安装 GDAL 库 (`pip install GDAL`) 并在系统 PATH 中配置了 'gdal_translate' 命令，以及安装 `pyproj` Python 库 (`pip install pyproj`)。")
    print("6. **燃料模型映射：** 再次检查 `reclassify_fuel_model_in_memory` 函数中的 `reclass_map`。此映射是示例性的，需您根据实际情况确认其准确性。")
    print("7. **相对湿度与FWI：** 请注意 `process_noaa_to_fwi_stream` 中的 RH 和 FWI 指数目前是估算或随机模拟的。为了更精确的模拟，建议寻找包含实际 RH 数据的 NOAA 产品，并集成并调用 `cffdrs` 或其他 FWI 计算库进行计算。")
    
    # --- 9. 运行 Cell2Fire 并检查其日志 ---
    print("\n" + "="*50)
    print("--- 尝试运行 Cell2Fire 模拟 ---")
    print("="*50 + "\n")
    
    # 将命令分解为列表形式以便 subprocess.run 执行
    cell2fire_command_list = cell2fire_command.split()
    
    try:
        # 使用 check=False，因为我们希望捕获C++的错误码，而不是立即抛出Python异常
        result = subprocess.run(cell2fire_command_list, check=False, capture_output=True, text=True)
        
        # 打印Cell2Fire的标准输出和标准错误
        if result.stdout:
            print("Cell2Fire Standard Output:\n", result.stdout)
        if result.stderr:
            print("Cell2Fire Standard Error:\n", result.stderr)
            
        # 检查返回码
        if result.returncode != 0:
            print(f"\n错误：Cell2Fire 进程以非零退出码 {result.returncode} 结束。")
            print("这通常表示模拟失败。请检查上述错误信息或 Cell2Fire 的日志文件。")
            
        # 无论成功与否，都检查Cell2Fire的日志文件
        log_file_path = os.path.join(output_folder, "LogFile.txt")
        if check_cell2fire_log(log_file_path):
            print("\n**重要提示：请务必打开并仔细阅读 Cell2Fire 的 LogFile.txt 获取详细错误信息！**")
        
    except FileNotFoundError:
        print("错误：未找到 'python' 命令或 Cell2Fire 的 'main.py' 脚本。请检查路径。")
    except Exception as e:
        print(f"运行 Cell2Fire 模拟时发生未知错误: {e}")

# --- 执行函数以生成脚本和文件 ---
if __name__ == "__main__":
    run_cell2fire_simulation()