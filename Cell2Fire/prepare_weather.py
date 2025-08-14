import pandas as pd

file_path = '/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/Input_Landscape/4073436.csv'

# 尝试读取CSV文件，处理缺失值和引号
df = pd.read_csv(file_path, quotechar='"', na_values=['', ' ', 'U', 'N/A', '-9999'])

# 将 'DATE' 列转换为日期时间格式
df['DATE'] = pd.to_datetime(df['DATE'])

# --- 第一步：识别所有可用的站点名称 ---
print("文件中包含的气象站名称 (NAME) 列表：")
unique_names = df['NAME'].unique()
for name in unique_names:
    print(f"- {name}")

# --- 第二步：选择一个您希望作为代表的气象站名称 ---
# 请将 'YOUR_PREFERRED_STATION_NAME' 替换为您从上面列表中选择的实际名称
# 例如: preferred_station_name = 'LEO CARRILLO CALIFORNIA, CA US'
preferred_station_name = 'LOS ANGELES INTERNATIONAL AIRPORT, CA US' # 示例，请替换为您的实际选择

print(f"\n您选择了气象站：'{preferred_station_name}' 的数据进行处理。")

# --- 第三步：筛选数据，只保留选定气象站的记录 ---
df_filtered = df[df['NAME'] == preferred_station_name].copy() # .copy() 避免SettingWithCopyWarning

# 验证筛选后的数据中 'DATE' 列是否唯一
print(f"\n筛选后，日期列是否有重复？: {df_filtered['DATE'].duplicated().any()}")
print("筛选后的数据头部：")
print(df_filtered.head())

# 将处理后的数据保存为新的 CSV 文件
output_file_path = '/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/Input_Landscape/Weather_SingleStation.csv'
df_filtered.to_csv(output_file_path, index=False)

print(f"\n处理完成！仅包含 '{preferred_station_name}' 气象站的新天气数据文件已保存到：{output_file_path}")
print("请更新您的 Cell2Fire 配置或脚本，使其使用此文件。")