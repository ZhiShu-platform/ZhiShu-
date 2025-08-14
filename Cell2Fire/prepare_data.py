import os
import numpy as np
import pandas as pd
import shutil
import subprocess
import warnings
from osgeo import gdal # 确保osgeo库已安装，pip install GDAL

# No Warnings
warnings.filterwarnings("ignore")

# --- GDAL TIFF 到 ASC 转换函数 ---
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
        clean_asc_header(asc_output_filepath)
        validate_asc_file(asc_output_filepath)
        print(f"  转换后文件大小: {os.path.getsize(asc_output_filepath) / (1024*1024):.2f} MB")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误：转换 {os.path.basename(tif_filepath)} 失败。命令: {' '.join(command)}")
        print(f"  Stdout: {e.stdout}")
        print(f"  Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"转换 {os.path.basename(tif_filepath)} 时发生未知错误: {e}")
        return False

# --- ASC 头部清洗函数 ---
def clean_asc_header(asc_filepath):
    """
    清洗ASC文件的头部，确保浮点数精度和格式。
    """
    try:
        with open(asc_filepath, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for i, line in enumerate(lines):
            if i < 6: # 只处理头部行
                parts = line.split()
                if len(parts) == 2:
                    key = parts[0].lower()
                    value = parts[1]
                    try:
                        if key in ['xllcorner', 'yllcorner', 'cellsize']:
                            new_lines.append(f"{key.upper()} {float(value):.10f}\n")
                        elif key in ['ncols', 'nrows', 'nodata_value']:
                            new_lines.append(f"{key.upper()} {int(float(value)) if key != 'nodata_value' else int(float(value))}\n")
                        else:
                            new_lines.append(line)
                    except ValueError:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        with open(asc_filepath, 'w') as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"清洗文件 {os.path.basename(asc_filepath)} 头部时发生错误: {e}")

# --- ASC 文件验证函数 ---
def validate_asc_file(asc_filepath):
    """
    验证ASC文件是否有效（存在、有头部、有数据）。
    """
    try:
        if not os.path.exists(asc_filepath) or os.path.getsize(asc_filepath) == 0:
            print(f"错误：文件 {os.path.basename(asc_filepath)} 不存在或为空。")
            return False

        with open(asc_filepath, 'r') as f:
            header_lines = [f.readline() for _ in range(6)]
            
        header_keys = [line.split()[0].lower() for line in header_lines if line.strip()]
        required_keys = ['ncols', 'nrows', 'xllcorner', 'yllcorner', 'cellsize', 'nodata_value']
        if not all(key in header_keys for key in required_keys):
            print(f"错误：文件 {os.path.basename(asc_filepath)} 头部不完整或格式不正确。")
            return False

        data = np.loadtxt(asc_filepath, skiprows=6)
        if data.size == 0:
            print(f"警告：文件 {os.path.basename(asc_filepath)} 没有数据部分。")
        if not np.all(np.isfinite(data[data != float(read_asc_header(asc_filepath).get('nodata_value', -9999))])):
             print(f"警告：文件 {os.path.basename(asc_filepath)} 数据包含非有限值 (NaN/Inf)。")

        return True
    except Exception as e:
        print(f"错误：验证文件 {os.path.basename(asc_filepath)} 时发生错误: {e}")
        return False

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
                        header[key.lower()] = float(value) if '.' in value or 'e' in value.lower() else int(value)
                    except ValueError:
                        header[key.lower()] = value
        return header
    except Exception as e:
        print(f"错误：无法读取文件 {filepath} 的头部信息。请检查文件是否存在或格式是否正确。错误信息: {e}")
        return None

# --- 栅格裁剪函数 ---
def clip_raster_to_extent(input_filepath, output_filepath, xmin, ymin, xmax, ymax, cellsize=None):
    """
    使用gdal_translate裁剪栅格文件到指定范围。
    """
    print(f"开始裁剪文件：{os.path.basename(input_filepath)} 到 {os.path.basename(output_filepath)}")
    command = [
        "gdal_translate",
        "-projwin", str(xmin), str(ymax), str(xmax), str(ymin), # projwin expects ulx uly lrx lry
        "-of", "AAIGrid",
        input_filepath,
        output_filepath
    ]
    if cellsize:
        command.insert(2, "-tr")
        command.insert(3, str(cellsize))
        command.insert(4, str(cellsize))

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"  成功裁剪: {os.path.basename(input_filepath)} -> {os.path.basename(output_filepath)}")
        clean_asc_header(output_filepath)
        validate_asc_file(output_filepath)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误：裁剪 {os.path.basename(input_filepath)} 失败。命令: {' '.join(command)}")
        print(f"  Stdout: {e.stdout}")
        print(f"  Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"裁剪 {os.path.basename(input_filepath)} 时发生未知错误: {e}")
        return False

# --- 强制栅格对齐函数 ---
def force_raster_alignment(reference_filepath, target_filepath):
    """
    将目标栅格文件强制对齐到参考栅格的尺寸、范围和分辨率。
    使用gdal_translate进行裁剪和重采样，并使用临时文件避免输入输出相同的问题。
    """
    print(f"正在将 {os.path.basename(target_filepath)} 对齐到 {os.path.basename(reference_filepath)}")
    
    ref_header = read_asc_header(reference_filepath)
    if not ref_header:
        print(f"错误：无法读取参考文件 {reference_filepath} 的头部信息，无法进行对齐。")
        return False
        
    ref_ncols = int(ref_header['ncols'])
    ref_nrows = int(ref_header['nrows'])
    ref_xllcorner = ref_header['xllcorner']
    ref_yllcorner = ref_header['yllcorner']
    ref_cellsize = ref_header['cellsize']
    ref_nodata = ref_header.get('nodata_value', -9999)
    
    ref_ulx = ref_xllcorner
    ref_uly = ref_yllcorner + ref_nrows * ref_cellsize
    ref_lrx = ref_xllcorner + ref_ncols * ref_cellsize
    ref_lry = ref_yllcorner

    temp_output_filepath = target_filepath + ".tmp"

    command = [
        "gdal_translate",
        "-projwin", str(ref_ulx), str(ref_uly), str(ref_lrx), str(ref_lry),
        "-outsize", str(ref_ncols), str(ref_nrows),
        "-tr", str(ref_cellsize), str(ref_cellsize),
        "-r", "near", # 使用最近邻重采样，适用于分类数据（如燃料）
        "-a_nodata", str(ref_nodata),
        "-of", "AAIGrid",
        target_filepath,
        temp_output_filepath
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"  成功对齐并保存到临时文件: {os.path.basename(target_filepath)} -> {os.path.basename(temp_output_filepath)}")
        if result.stderr:
            print(f"  对齐过程警告/信息: {result.stderr}")
        
        if os.path.exists(temp_output_filepath):
            if os.path.exists(target_filepath):
                os.remove(target_filepath)
            os.rename(temp_output_filepath, target_filepath)
            print(f"  成功将对齐后的文件替换为: {os.path.basename(target_filepath)}")
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
        if os.path.exists(temp_output_filepath):
            os.remove(temp_output_filepath)
        return False
    except Exception as e:
        print(f"对齐 {os.path.basename(target_filepath)} 时发生未知错误: {e}")
        if os.path.exists(temp_output_filepath):
            os.remove(temp_output_filepath)
        return False


if __name__ == "__main__":
    # --- 用户配置部分 ---
    # 原始栅格TIFF文件所在目录，例如 'data/tif_inputs'
    initial_tif_dir = os.path.join(os.getcwd(),  "Input_Landscape") 
    # 所有输出文件的基准目录
    output_base_dir = os.path.join(os.getcwd(), "cell2fire_run")

    # 栅格分辨率 (例如 100 表示 100x100 米的单元格)
    cell_size_meters = 50

    # 固定裁剪范围 (UTM Zone 11N, EPSG:26911 坐标)
    # 示例值，请根据您的研究区域实际范围进行替换
    fixed_crop_xmin = 260000.0  # 西边最小X坐标
    fixed_crop_xmax = 350000.0  # 东边最大X坐标
    fixed_crop_ymin = 3710000.0 # 南边最小Y坐标
    fixed_crop_ymax = 3800000.0 # 北边最大Y坐标

    # 裁剪范围的缓冲区 (米)，可选，用于稍微扩大裁剪区域
    buffer_for_fixed_range = 5000 # 例如 5公里

    # -------------------

    # 定义子目录和文件路径
    raw_input_dir = os.path.join(output_base_dir, "Input_Landscape_raw")
    clipped_input_dir = os.path.join(output_base_dir, "Input_Landscape_cropped")

    # 创建输出目录
    os.makedirs(raw_input_dir, exist_ok=True)
    os.makedirs(clipped_input_dir, exist_ok=True)

    print("\n--- 1. 将原始TIFF文件转换为ASC文件 ---")
    tif_files = ["resampled_dem50.tif", "resampled_slope50.tif", "resampled_saz50.tif", "resampled_LF50.tif", "cur.tif"]
    asc_names = ["elevation.asc", "slope.asc", "saz.asc", "Forest.asc", "cur.asc"]

    for tif_name, asc_name in zip(tif_files, asc_names):
        tif_path = os.path.join(initial_tif_dir, tif_name)
        asc_path = os.path.join(raw_input_dir, asc_name)
        if os.path.exists(tif_path):
            convert_tif_to_asc(tif_path, asc_path)
        else:
            print(f"警告：原始TIFF文件 {tif_path} 不存在，跳过转换。")

    # --- 2. 确定精确的裁剪范围 ---
    # 使用用户定义的固定范围，并考虑缓冲区
    crop_xmin = fixed_crop_xmin - buffer_for_fixed_range
    crop_xmax = fixed_crop_xmax + buffer_for_fixed_range
    crop_ymin = fixed_crop_ymin - buffer_for_fixed_range
    crop_ymax = fixed_crop_ymax + buffer_for_fixed_range

    print(f"\n裁剪范围 (UTM):")
    print(f"  X: {crop_xmin:.2f} to {crop_xmax:.2f}")
    print(f"  Y: {crop_ymin:.2f} to {crop_ymax:.2f}")

    # --- 3. 裁剪栅格文件 ---
    print("\n--- 裁剪所有景观栅格文件 ---")
    for asc_name in asc_names:
        raw_asc_path = os.path.join(raw_input_dir, asc_name)
        cropped_asc_path = os.path.join(clipped_input_dir, asc_name)
        if os.path.exists(raw_asc_path):
            clip_raster_to_extent(raw_asc_path, cropped_asc_path, crop_xmin, crop_ymin, crop_xmax, crop_ymax, cell_size_meters)
        else:
            print(f"警告：原始ASC文件 {raw_asc_path} 不存在，跳过裁剪。")

    # --- 4. 强制对齐所有裁剪后的栅格文件 ---
    print("\n--- 强制对齐所有裁剪后的栅格文件到 Forest.asc 基准 ---")
    reference_file_for_alignment = os.path.join(clipped_input_dir, "Forest.asc")

    files_to_force_align = [
        os.path.join(clipped_input_dir, "elevation.asc"), 
        os.path.join(clipped_input_dir, "slope.asc"),
        os.path.join(clipped_input_dir, "saz.asc"),
        os.path.join(clipped_input_dir, "cur.asc")
    ]

    if not os.path.exists(reference_file_for_alignment):
        print(f"错误：参考对齐文件 {reference_file_for_alignment} 不存在，无法进行对齐。")
    else:
        for target_path in files_to_force_align:
            if os.path.exists(target_path):
                force_raster_alignment(reference_file_for_alignment, target_path)
            else:
                print(f"警告：文件 {os.path.basename(target_path)} 不存在，跳过对齐。")
    
    print("\n\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"")
    print("--- 数据准备脚本运行完成 ---")
    print(f"处理后的栅格文件位于: {clipped_input_dir}")
    print("\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"")
    print("您现在可以运行 'run_cell2fire_simulation.py' 脚本来执行模拟。")