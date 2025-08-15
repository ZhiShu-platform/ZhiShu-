import geopandas as gpd
from sqlalchemy import create_engine
import logging
import pandas as pd
import json
import requests # 引入 requests 库

# --- 配置区 ---

# 1. PostGIS 数据库连接信息
DB_USER = "zs_zzr"
DB_PASSWORD = "373291Moon"  # <--- !! 请务必修改为您的真实密码 !!
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "zs_data"
SCHEMA_NAME = "public"

# 2. 灾害数据源配置
DISASTER_SOURCES = {
    "california_fires": {
        "name": "California Wildfires (NIFC)",
        "url": "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0/query?where=POOCounty%20IN%20('Irwin'%2C%20'Inyo'%2C%20'Kern'%2C%20'Kings'%2C%20'Los%20Angeles'%2C%20'Madera'%2C%20'Mariposa'%2C%20'Merced'%2C%20'Mono'%2C%20'Monterey'%2C%20'Napa'%2C%20'Nevada'%2C%20'Orange'%2C%20'Placer'%2C%20'Plumas'%2C%20'Riverside'%2C%20'Sacramento'%2C%20'San%20Benito'%2C%20'San%20Bernardino'%2C%20'San%20Diego'%2C%20'San%20Joaquin'%2C%20'San%20Luis%20Obispo'%2C%20'San%20Mateo'%2C%20'Santa%20Barbara'%2C%20'Santa%20Clara'%2C%20'Santa%20Cruz'%2C%20'Shasta'%2C%20'Sierra'%2C%20'Siskiyou'%2C%20'Solano'%2C%20'Sonoma'%2C%20'Stanislaus'%2C%20'Sutter'%2C%20'Tehama'%2C%20'Trinity'%2C%20'Tulare'%2C%20'Tuolumne'%2C%20'Ventura'%2C%20'Yolo'%2C%20'Yuba'%2C%20'Alameda'%2C%20'Alpine'%2C%20'Amador'%2C%20'Butte'%2C%20'Calaveras'%2C%20'Colusa'%2C%20'Contra%20Costa'%2C%20'Del%20Norte'%2C%20'El%20Dorado'%2C%20'Fresno'%2C%20'Glenn'%2C%20'Humboldt'%2C%20'Imperial'%2C%20'Lake'%2C%20'Lassen')&outFields=*&f=geojson",
        "table_name": "current_california_fires"
    },
    "global_earthquakes": {
        "name": "Global Earthquakes M2.5+ (USGS)",
        "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson",
        "table_name": "global_earthquakes_last_week"
    },
    "active_hurricanes": {
        "name": "Active Hurricanes (NOAA)",
        "url": "https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/Active_Hurricanes_v1/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson",
        "table_name": "active_hurricanes"
    }
}

# --- 脚本主逻辑 ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_column_names(gdf):
    """清理列名，转换为小写并替换特殊字符。"""
    new_columns = {}
    for col in gdf.columns:
        clean_col = str(col).lower().replace(' ', '_').replace('-', '_').replace('.', '')
        new_columns[col] = clean_col
    gdf.rename(columns=new_columns, inplace=True)
    return gdf

def preprocess_data_for_postgis(gdf):
    """对 GeoDataFrame 进行预处理，以确保能被 PostGIS 正确识别。"""
    if gdf.crs is None:
        logging.warning("CRS not found, setting to EPSG:4326 (WGS84).")
        gdf.set_crs("EPSG:4326", inplace=True)
    else:
        gdf = gdf.to_crs("EPSG:4326")

    gdf = clean_column_names(gdf)

    for col in gdf.columns:
        if col == 'geometry':
            continue
        
        is_complex = gdf[col].dropna().apply(lambda x: isinstance(x, (dict, list))).any()
        if is_complex:
            logging.info(f"Column '{col}' contains complex objects. Converting to JSON string.")
            gdf[col] = gdf[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    
    gdf = gdf.fillna(value=pd.NA).replace({pd.NA: None})
    return gdf

def sync_disaster_data(source_config, db_engine):
    """从单个数据源获取数据并同步到 PostGIS 数据库。"""
    source_name = source_config['name']
    url = source_config['url']
    table_name = source_config['table_name']

    try:
        logging.info(f"--- Starting sync for: {source_name} ---")
        
        # 使用 requests 获取数据，增加超时和错误处理
        logging.info(f"Fetching data from {url}")
        response = requests.get(url, timeout=60) # 60秒超时
        response.raise_for_status()  # 如果请求失败 (如 404, 500)，则会抛出异常

        # 检查返回内容是否为空
        if not response.content:
            logging.warning(f"No data content returned for {source_name}. Skipping sync.")
            return

        # 将获取到的内容传递给 geopandas
        gdf = gpd.read_file(response.content)
        
        if gdf.empty:
            logging.warning(f"No features found for {source_name}. Skipping sync.")
            return

        logging.info(f"Successfully fetched {len(gdf)} features for {source_name}.")

        gdf = preprocess_data_for_postgis(gdf)
        logging.info(f"Data types before writing to PostGIS:\n{gdf.dtypes}")

        gdf.to_postgis(
            name=table_name, 
            con=db_engine, 
            schema=SCHEMA_NAME, 
            if_exists='replace', 
            index=False
        )
        logging.info(f"Successfully synced data for {source_name}.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching data for {source_name}: {e}")
    except Exception as e:
        logging.error(f"An error occurred during sync for {source_name}: {e}", exc_info=True)
    finally:
        logging.info(f"--- Finished sync for: {source_name} ---\n")

def main():
    """主函数，初始化数据库连接并遍历所有数据源进行同步。"""
    logging.info(">>> Starting disaster data synchronization process <<<")
    
    try:
        engine_str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(engine_str)
        logging.info("Database connection engine created successfully.")
    except Exception as e:
        logging.error(f"Failed to create database engine: {e}")
        return

    for key, config in DISASTER_SOURCES.items():
        sync_disaster_data(config, engine)
        
    logging.info(">>> All disaster data sources have been processed. <<<")

if __name__ == "__main__":
    # 在运行脚本前，确保 requests 库已安装
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found. Please install it using 'pip3 install requests'")
        exit(1)
        
    main()