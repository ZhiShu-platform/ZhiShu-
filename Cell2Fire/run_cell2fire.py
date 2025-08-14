# debug_cell2fire_inputs.py
import pandas as pd
import numpy as np
import os
import datetime
import warnings



def read_asc_header(filepath):
    """读取ASC文件的头部信息并返回一个字典"""
    header = {}
    try:
        with open(filepath, 'r') as f:
            for _ in range(6):
                line = next(f).strip().split()
                header[line[0].lower()] = float(line[1])
        return header
    except FileNotFoundError:
        print(f"  [检查失败] 文件未找到: {filepath}")
        return None
    except Exception as e:
        print(f"  [检查失败] 读取文件头部时出错: {filepath} - {e}")
        return None

def main():
    """主诊断函数"""
    print("="*60)
    print("=== Cell2Fire 输入数据诊断脚本启动 ===")
    print("="*60)
    
    # 检查所有需要的目录
    for dir_name, dir_path in cfg.DATA_DIRS.items():
        if not os.path.isdir(dir_path):
            print(f"错误：目录 '{dir_path}' 不存在。请检查您的 'cell2fire_config.py'。")
            return

    # 定义Cell2fire期望的输入文件路径
    input_instance_dir = cfg.DATA_DIRS["cell2fire_input_instance"]
    landscape_files = {
        "dem": os.path.join(input_instance_dir, "elevation.asc"),
        "slope": os.path.join(input_instance_dir, "slope.asc"),
        "aspect": os.path.join(input_instance_dir, "saz.asc"),
        "fuel": os.path.join(input_instance_dir, "fuel.asc"),
        "weather": os.path.join(input_instance_dir, "Weather.csv"),
        "ignitions": os.path.join(input_instance_dir, "Ignitions.csv")
    }

    # 1. 检查文件是否存在
    print("\n--- 1. 检查输入文件是否存在 ---")
    all_files_exist = True
    for name, path in landscape_files.items():
        if os.path.exists(path):
            print(f"  [通过] {name} 文件存在: {path}")
        else:
            print(f"  [失败] {name} 文件不存在: {path}")
            all_files_exist = False
    if not all_files_exist:
        print("\n错误：缺少必要的输入文件。请运行 run_cell2fire.py 脚本生成这些文件。")
        return
    
    # 2. 检查栅格文件头部的对齐情况
    print("\n--- 2. 检查栅格文件 (.asc) 是否对齐 ---")
    headers = {name: read_asc_header(path) for name, path in landscape_files.items() if path.endswith('.asc')}
    if any(h is None for h in headers.values()):
        return

    base_header = headers["dem"]
    print(f"  基准图层 (dem.asc): {base_header['nrows']} 行, {base_header['ncols']} 列")
    is_aligned = True
    for name, header in headers.items():
        if name == "dem": continue
        
        mismatches = []
        for key in ['ncols', 'nrows', 'xllcorner', 'yllcorner', 'cellsize']:
            if abs(base_header[key] - header[key]) > 1e-9: # 容忍浮点数误差
                mismatches.append(f"{key} (基准: {base_header[key]}, 当前: {header[key]})")
        
        if mismatches:
            print(f"  [失败] {name}.asc 与 dem.asc 未对齐。差异项: {', '.join(mismatches)}")
            is_aligned = False
        else:
            print(f"  [通过] {name}.asc 与 dem.asc 对齐。")

    if not is_aligned:
        print("\n建议：请返回QGIS，严格按照指南中的步骤1.2，使用'弯曲(重投影)'工具重新对齐所有栅格图层。")

    # 3. 检查起火点是否在栅格范围内
    print("\n--- 3. 检查起火点是否在栅格范围内 ---")
    try:
        ignitions_df = pd.read_csv(landscape_files["ignitions"])
        max_row = ignitions_df['IgRow'].max()
        max_col = ignitions_df['IgCol'].max()
        
        if max_row < base_header['nrows'] and max_col < base_header['ncols']:
            print(f"  [通过] 所有起火点都在栅格范围内 (最大行: {max_row}, 最大列: {max_col})。")
        else:
            print(f"  [失败] 存在越界的起火点！")
            print(f"    栅格维度: {int(base_header['nrows'])} 行, {int(base_header['ncols'])} 列")
            print(f"    文件中最大行号: {max_row}, 最大列号: {max_col}")
            print("\n建议：检查 run_cell2fire.py 中的 prepare_ignitions_from_firms 函数，确保坐标到行列号的转换逻辑正确。")
    except Exception as e:
        print(f"  [失败] 无法读取或检查起火点文件: {e}")

    # 4. 检查燃料文件中的值是否有效
    print("\n--- 4. 检查燃料文件中的值是否有效 ---")
    try:
        with open(landscape_files["fuel"], 'r') as f:
            [next(f) for _ in range(6)]
            fuel_data = np.loadtxt(f)
        
        unique_values = np.unique(fuel_data)
        valid_fbp_codes = set(cfg.FUEL_RECLASS_MAP.values())
        
        invalid_codes = [val for val in unique_values if val not in valid_fbp_codes]
        
        if not invalid_codes:
            print(f"  [通过] 燃料文件中的所有值都在FBP映射表中。")
        else:
            print(f"  [失败] 燃料文件中发现无效或未映射的 FBP 代码: {invalid_codes}")
            print("\n建议：更新 cell2fire_config.py 中的 FUEL_RECLASS_MAP，确保所有 FBFM13 值都有对应的FBP代码。")

    except Exception as e:
        print(f"  [失败] 无法读取或检查燃料文件: {e}")

    # 5. 检查天气文件行数
    print("\n--- 5. 检查天气文件与模拟时长的匹配性 ---")
    try:
        weather_df = pd.read_csv(landscape_files["weather"])
        num_weather_rows = len(weather_df)
        
        start = datetime.datetime.strptime(cfg.SIMULATION_PARAMS["simulation_start_date"], "%Y-%m-%d")
        end = datetime.datetime.strptime(cfg.SIMULATION_PARAMS["simulation_end_date"], "%Y-%m-%d")
        expected_hours = int((end - start).total_seconds() / 3600) + 24
        
        if num_weather_rows == expected_hours:
            print(f"  [通过] 天气文件行数 ({num_weather_rows}) 与预期模拟小时数 ({expected_hours}) 匹配。")
        else:
            print(f"  [失败] 天气文件行数 ({num_weather_rows}) 与预期模拟小时数 ({expected_hours}) 不匹配。")
            print("\n建议：检查 run_cell2fire.py 中的 process_weather_data 函数和 config.py 中的日期设置。")
            
    except Exception as e:
        print(f"  [失败] 无法读取或检查天气文件: {e}")

    print("\n" + "="*60)
    print("=== 诊断完成 ===")
    print("="*60)

if __name__ == "__main__":
    main()

