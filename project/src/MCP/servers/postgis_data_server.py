import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import asyncpg
from datetime import datetime
import os
import subprocess
import tempfile

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent

class PostGISDataServer:
    """PostGIS数据服务 - 地理空间数据中枢"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_config = self._get_db_config()
        self.pool: Optional[asyncpg.Pool] = None
        self.server = Server("postgis-data-server")
        
        self._setup_tools()
        self._setup_resources()
    
    def _get_db_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'zs_data'),
            'user': os.getenv('DB_USER', 'zs_zzr'),
            'password': os.getenv('DB_PASSWORD', '373291Moon'),
            'min_size': 5,
            'max_size': 20
        }
    
    async def _get_connection(self) -> asyncpg.Connection:
        """获取数据库连接"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(**self.db_config)
        
        return await self.pool.acquire()
    
    def _setup_tools(self):
        """设置工具"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """列出可用工具"""
            return [
                Tool(
                    name="spatial_query",
                    description="执行空间查询，支持点、线、面等几何对象查询",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query_type": {"type": "string", "enum": ["point", "line", "polygon", "buffer"]},
                            "geometry": {"type": "object", "description": "GeoJSON几何对象"},
                            "table_name": {"type": "string", "description": "要查询的表名"},
                            "fields": {"type": "array", "items": {"type": "string"}, "description": "要返回的字段"},
                            "spatial_relation": {"type": "string", "enum": ["intersects", "contains", "within", "near"], "default": "intersects"},
                            "buffer_distance": {"type": "number", "description": "缓冲区距离（米）"}
                        },
                        "required": ["query_type", "table_name"]
                    }
                ),
                Tool(
                    name="raster_analysis",
                    description="栅格数据分析，包括统计、重分类、叠加分析等",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["statistics", "reclassify", "overlay", "slope", "aspect"]},
                            "raster_table": {"type": "string", "description": "栅格表名"},
                            "parameters": {"type": "object", "description": "操作参数"}
                        },
                        "required": ["operation", "raster_table"]
                    }
                ),
                Tool(
                    name="data_import",
                    description="导入地理空间数据，支持多种格式",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"},
                            "file_format": {"type": "string", "enum": ["shp", "geojson", "kml", "netcdf", "tiff"]},
                            "table_name": {"type": "string", "description": "目标表名"},
                            "srid": {"type": "integer", "description": "空间参考系统ID", "default": 4326}
                        },
                        "required": ["file_path", "file_format", "table_name"]
                    }
                ),
                # ==================== 精准识别灾情 ====================
                
                # 灾害事件查询
                Tool(
                    name="postgis_disaster_event_query",
                    description="查询灾害事件数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_type": {
                                "type": "string",
                                "enum": ["flood", "earthquake", "landslide", "wildfire", "storm", "drought"],
                                "description": "灾害类型"
                            },
                            "spatial_extent": {
                                "type": "object",
                                "properties": {
                                    "geometry": {"type": "object", "description": "GeoJSON几何对象"},
                                    "buffer_distance": {"type": "number", "description": "缓冲区距离(米)"}
                                },
                                "description": "空间范围"
                            },
                            "temporal_range": {
                                "type": "object",
                                "properties": {
                                    "start_time": {"type": "string", "format": "date-time"},
                                    "end_time": {"type": "string", "format": "date-time"}
                                },
                                "description": "时间范围"
                            },
                            "event_attributes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "事件属性字段"
                            }
                        },
                        "required": ["event_type"]
                    }
                ),
                
                # 实时监测数据查询
                Tool(
                    name="postgis_real_time_monitoring",
                    description="查询实时监测数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "monitoring_type": {
                                "type": "string",
                                "enum": ["weather", "hydrology", "seismology", "air_quality"],
                                "description": "监测类型"
                            },
                            "station_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "监测站ID列表"
                            },
                            "data_frequency": {
                                "type": "string",
                                "enum": ["minute", "hourly", "daily"],
                                "description": "数据频率"
                            },
                            "latest_records": {
                                "type": "integer",
                                "description": "最新记录数",
                                "default": 100
                            }
                        },
                        "required": ["monitoring_type"]
                    }
                ),
                
                # ==================== 量化评估风险 ====================
                
                # 风险区域分析
                Tool(
                    name="postgis_risk_zone_analysis",
                    description="风险区域空间分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "risk_type": {
                                "type": "string",
                                "enum": ["flood_risk", "earthquake_risk", "landslide_risk", "wildfire_risk"],
                                "description": "风险类型"
                            },
                            "analysis_method": {
                                "type": "string",
                                "enum": ["overlay", "buffer", "intersection", "union"],
                                "description": "分析方法"
                            },
                            "risk_levels": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "very_high"]
                                },
                                "description": "风险等级"
                            },
                            "spatial_resolution": {
                                "type": "number",
                                "description": "空间分辨率(米)"
                            }
                        },
                        "required": ["risk_type", "analysis_method"]
                    }
                ),
                
                # 脆弱性评估
                Tool(
                    name="postgis_vulnerability_assessment",
                    description="脆弱性空间评估",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vulnerability_factors": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["population_density", "infrastructure", "land_use", "socioeconomic"]
                                },
                                "description": "脆弱性因子"
                            },
                            "assessment_scale": {
                                "type": "string",
                                "enum": ["building", "block", "district", "city"],
                                "description": "评估尺度"
                            },
                            "weighting_scheme": {
                                "type": "object",
                                "description": "权重方案",
                                "additionalProperties": {"type": "number"}
                            }
                        },
                        "required": ["vulnerability_factors"]
                    }
                ),
                
                # ==================== 主动协同调度 ====================
                
                # 应急资源查询
                Tool(
                    name="postgis_emergency_resource_query",
                    description="查询应急资源分布",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "enum": ["fire_station", "hospital", "police_station", "shelter", "equipment"],
                                "description": "资源类型"
                            },
                            "service_area": {
                                "type": "object",
                                "properties": {
                                    "center": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}},
                                    "radius": {"type": "number", "description": "服务半径(米)"}
                                },
                                "description": "服务区域"
                            },
                            "resource_capacity": {
                                "type": "object",
                                "properties": {
                                    "min_capacity": {"type": "number"},
                                    "max_capacity": {"type": "number"}
                                },
                                "description": "资源容量"
                            }
                        },
                        "required": ["resource_type"]
                    }
                ),
                
                # 交通网络分析
                Tool(
                    name="postgis_transportation_analysis",
                    description="交通网络分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["shortest_path", "service_area", "accessibility", "connectivity"],
                                "description": "分析类型"
                            },
                            "network_type": {
                                "type": "string",
                                "enum": ["road", "rail", "water", "air"],
                                "description": "网络类型"
                            },
                            "origin_destination": {
                                "type": "object",
                                "properties": {
                                    "origin": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}},
                                    "destination": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}}
                                },
                                "description": "起终点"
                            },
                            "constraints": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "约束条件"
                            }
                        },
                        "required": ["analysis_type", "network_type"]
                    }
                ),
                
                # ==================== 量化评估灾损 ====================
                
                # 损失评估数据查询
                Tool(
                    name="postgis_damage_assessment_query",
                    description="查询损失评估数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "damage_category": {
                                "type": "string",
                                "enum": ["infrastructure", "buildings", "agriculture", "economic", "human"],
                                "description": "损失类别"
                            },
                            "assessment_period": {
                                "type": "object",
                                "properties": {
                                    "start_date": {"type": "string", "format": "date"},
                                    "end_date": {"type": "string", "format": "date"}
                                },
                                "description": "评估周期"
                            },
                            "spatial_aggregation": {
                                "type": "string",
                                "enum": ["point", "polygon", "grid"],
                                "description": "空间聚合方式"
                            },
                            "damage_indicators": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "损失指标"
                            }
                        },
                        "required": ["damage_category"]
                    }
                ),
                
                # 恢复进度监测
                Tool(
                    name="postgis_recovery_monitoring",
                    description="恢复进度监测",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "recovery_phase": {
                                "type": "string",
                                "enum": ["immediate", "short_term", "long_term", "reconstruction"],
                                "description": "恢复阶段"
                            },
                            "monitoring_indicators": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["infrastructure_restoration", "economic_recovery", "social_recovery", "environmental_recovery"]
                                },
                                "description": "监测指标"
                            },
                            "progress_threshold": {
                                "type": "number",
                                "description": "进度阈值(%)",
                                "minimum": 0,
                                "maximum": 100
                            }
                        },
                        "required": ["recovery_phase"]
                    }
                ),
                
                # 原有工具保留
                Tool(
                    name="data_export",
                    description="导出地理空间数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {"type": "string", "description": "源表名"},
                            "output_format": {"type": "string", "enum": ["shp", "geojson", "kml", "netcdf", "tiff"]},
                            "output_path": {"type": "string", "description": "输出路径"},
                            "query": {"type": "string", "description": "SQL查询条件"}
                        },
                        "required": ["table_name", "output_format", "output_path"]
                    }
                ),
                Tool(
                    name="spatial_index",
                    description="创建和管理空间索引",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["create", "drop", "rebuild"]},
                            "table_name": {"type": "string", "description": "表名"},
                            "geometry_column": {"type": "string", "description": "几何列名", "default": "geom"}
                        },
                        "required": ["action", "table_name"]
                    }
                ),
                Tool(
                    name="risk_assessment_query",
                    description="查询灾害风险评估数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "disaster_type": {"type": "string", "enum": ["flood", "earthquake", "wildfire", "hurricane"]},
                            "region": {"type": "string", "description": "地理区域"},
                            "risk_level": {"type": "string", "enum": ["low", "moderate", "high", "critical"], "description": "风险等级"},
                            "date_range": {"type": "array", "items": {"type": "string"}, "description": "日期范围"}
                        },
                        "required": ["disaster_type"]
                    }
                ),
                Tool(
                    name="format_conversion",
                    description="地理空间数据格式转换",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "input_file": {"type": "string", "description": "输入文件路径"},
                            "input_format": {"type": "string", "enum": ["netcdf", "tiff", "shp", "geojson"]},
                            "output_file": {"type": "string", "description": "输出文件路径"},
                            "output_format": {"type": "string", "enum": ["netcdf", "tiff", "shp", "geojson", "postgis"]},
                            "target_srid": {"type": "integer", "description": "目标空间参考系统ID", "default": 4326}
                        },
                        "required": ["input_file", "input_format", "output_file", "output_format"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            try:
                if name == "spatial_query":
                    result = await self._spatial_query(arguments)
                elif name == "raster_analysis":
                    result = await self._raster_analysis(arguments)
                elif name == "data_import":
                    result = await self._data_import(arguments)
                elif name == "data_export":
                    result = await self._data_export(arguments)
                elif name == "spatial_index":
                    result = await self._spatial_index(arguments)
                elif name == "risk_assessment_query":
                    result = await self._risk_assessment_query(arguments)
                elif name == "format_conversion":
                    result = await self._format_conversion(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                
            except Exception as e:
                self.logger.error(f"Tool execution error: {e}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]
    
    def _setup_resources(self):
        """设置资源"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """列出可用资源"""
            return [
                Resource(
                    uri="postgis://disaster_data",
                    name="disaster_data",
                    description="灾害数据表",
                    mimeType="application/postgis"
                ),
                Resource(
                    uri="postgis://risk_assessment",
                    name="risk_assessment", 
                    description="风险评估结果表",
                    mimeType="application/postgis"
                ),
                Resource(
                    uri="postgis://spatial_layers",
                    name="spatial_layers",
                    description="空间图层表",
                    mimeType="application/postgis"
                ),
                Resource(
                    uri="postgis://weather_data",
                    name="weather_data",
                    description="天气数据表",
                    mimeType="application/postgis"
                ),
                Resource(
                    uri="postgis://infrastructure",
                    name="infrastructure",
                    description="基础设施数据表",
                    mimeType="application/postgis"
                )
            ]
    
    async def _spatial_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行空间查询"""
        query_type = params.get('query_type')
        table_name = params.get('table_name')
        fields = params.get('fields', ['*'])
        spatial_relation = params.get('spatial_relation', 'intersects')
        
        try:
            conn = await self._get_connection()
            
            # 构建查询SQL
            field_list = ', '.join(fields) if fields != ['*'] else '*'
            
            if query_type == 'point':
                sql = f"""
                SELECT {field_list}
                FROM {table_name}
                WHERE ST_{spatial_relation.capitalize()}(geom, ST_GeomFromGeoJSON($1))
                """
            elif query_type == 'buffer':
                buffer_distance = params.get('buffer_distance', 1000)
                sql = f"""
                SELECT {field_list}
                FROM {table_name}
                WHERE ST_{spatial_relation.capitalize()}(geom, ST_Buffer(ST_GeomFromGeoJSON($1), {buffer_distance}))
                """
            else:
                sql = f"""
                SELECT {field_list}
                FROM {table_name}
                WHERE ST_{spatial_relation.capitalize()}(geom, ST_GeomFromGeoJSON($1))
                """
            
            # 执行查询
            geometry = params.get('geometry', {})
            rows = await conn.fetch(sql, json.dumps(geometry))
            
            # 转换结果
            results = []
            for row in rows:
                row_dict = dict(row)
                # 处理几何对象
                if 'geom' in row_dict and row_dict['geom']:
                    row_dict['geom'] = row_dict['geom'].__geo_interface__
                results.append(row_dict)
            
            await self.pool.release(conn)
            
            return {
                "success": True,
                "count": len(results),
                "results": results,
                "query": sql
            }
            
        except Exception as e:
            self.logger.error(f"Spatial query error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _raster_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """栅格数据分析"""
        operation = params.get('operation')
        raster_table = params.get('raster_table')
        
        try:
            conn = await self._get_connection()
            
            if operation == 'statistics':
                sql = f"""
                SELECT 
                    ST_SummaryStats(rast) as stats,
                    ST_Width(rast) as width,
                    ST_Height(rast) as height
                FROM {raster_table}
                LIMIT 1
                """
                row = await conn.fetchrow(sql)
                
                if row:
                    stats = row['stats']
                    result = {
                        "success": True,
                        "statistics": {
                            "count": stats.count,
                            "sum": float(stats.sum),
                            "mean": float(stats.mean),
                            "stddev": float(stats.stddev),
                            "min": float(stats.min),
                            "max": float(stats.max)
                        },
                        "dimensions": {
                            "width": row['width'],
                            "height": row['height']
                        }
                    }
                else:
                    result = {"success": False, "error": "No raster data found"}
            
            elif operation == 'slope':
                sql = f"""
                SELECT ST_Slope(rast, 1, '32BF', 'DEGREES') as slope
                FROM {raster_table}
                LIMIT 1
                """
                row = await conn.fetchrow(sql)
                result = {"success": True, "message": "Slope calculation completed"}
            
            else:
                result = {"success": False, "error": f"Unsupported operation: {operation}"}
            
            await self.pool.release(conn)
            return result
            
        except Exception as e:
            self.logger.error(f"Raster analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _data_import(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """导入地理空间数据"""
        file_path = params.get('file_path')
        file_format = params.get('file_format')
        table_name = params.get('table_name')
        srid = params.get('srid', 4326)
        
        try:
            conn = await self._get_connection()
            
            if file_format == 'shp':
                # 使用shp2pgsql导入Shapefile
                result = await self._import_shapefile(file_path, table_name, srid)
            elif file_format == 'geojson':
                # 导入GeoJSON
                result = await self._import_geojson(file_path, table_name, srid)
            elif file_format == 'netcdf':
                # 导入NetCDF
                result = await self._import_netcdf(file_path, table_name, srid)
            elif file_format == 'tiff':
                # 导入GeoTIFF
                result = await self._import_geotiff(file_path, table_name, srid)
            else:
                return {"success": False, "error": f"Unsupported format: {file_format}"}
            
            await self.pool.release(conn)
            return result
            
        except Exception as e:
            self.logger.error(f"Data import error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _import_shapefile(self, file_path: str, table_name: str, srid: int) -> Dict[str, Any]:
        """导入Shapefile"""
        try:
            # 使用shp2pgsql工具
            cmd = [
                'shp2pgsql',
                '-s', str(srid),
                '-I',  # 创建空间索引
                file_path,
                table_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"success": True, "message": f"Shapefile imported to {table_name}"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": f"Shapefile import failed: {str(e)}"}
    
    async def _import_geojson(self, file_path: str, table_name: str, srid: int) -> Dict[str, Any]:
        """导入GeoJSON"""
        try:
            # 使用ogr2ogr工具
            cmd = [
                'ogr2ogr',
                '-f', 'PostgreSQL',
                f'PG:host={self.db_config["host"]} port={self.db_config["port"]} dbname={self.db_config["database"]} user={self.db_config["user"]} password={self.db_config["password"]}',
                file_path,
                '-nln', table_name,
                '-a_srs', f'EPSG:{srid}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"success": True, "message": f"GeoJSON imported to {table_name}"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": f"GeoJSON import failed: {str(e)}"}
    
    async def _import_netcdf(self, file_path: str, table_name: str, srid: int) -> Dict[str, Any]:
        """导入NetCDF"""
        try:
            # 使用gdal_translate工具
            temp_tiff = tempfile.NamedTemporaryFile(suffix='.tiff', delete=False)
            temp_tiff.close()
            
            cmd = [
                'gdal_translate',
                '-of', 'GTiff',
                file_path,
                temp_tiff.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 导入转换后的TIFF文件
                import_result = await self._import_geotiff(temp_tiff.name, table_name, srid)
                
                # 清理临时文件
                os.unlink(temp_tiff.name)
                
                return import_result
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": f"NetCDF import failed: {str(e)}"}
    
    async def _import_geotiff(self, file_path: str, table_name: str, srid: int) -> Dict[str, Any]:
        """导入GeoTIFF"""
        try:
            # 使用raster2pgsql工具
            cmd = [
                'raster2pgsql',
                '-s', str(srid),
                '-I',  # 创建空间索引
                '-C',  # 应用约束
                file_path,
                table_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"success": True, "message": f"GeoTIFF imported to {table_name}"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": f"GeoTIFF import failed: {str(e)}"}
    
    async def _data_export(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """导出地理空间数据"""
        table_name = params.get('table_name')
        output_format = params.get('output_format')
        output_path = params.get('output_path')
        
        try:
            conn = await self._get_connection()
            
            # 构建导出SQL
            if output_format == 'geojson':
                sql = f"""
                SELECT json_build_object(
                    'type', 'FeatureCollection',
                    'features', json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'geometry', ST_AsGeoJSON(geom)::json,
                            'properties', to_jsonb(row_to_json(t.*))
                        )
                    )
                ) as geojson
                FROM (
                    SELECT * FROM {table_name}
                ) t
                """
            else:
                return {"success": False, "error": f"Unsupported export format: {output_format}"}
            
            # 执行导出
            row = await conn.fetchrow(sql)
            
            if row and row['geojson']:
                # 保存到文件
                with open(output_path, 'w') as f:
                    json.dump(row['geojson'], f, indent=2)
                
                result = {"success": True, "message": f"Data exported to {output_path}"}
            else:
                result = {"success": False, "error": "No data to export"}
            
            await self.pool.release(conn)
            return result
            
        except Exception as e:
            self.logger.error(f"Data export error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _spatial_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """管理空间索引"""
        action = params.get('action')
        table_name = params.get('table_name')
        geometry_column = params.get('geometry_column', 'geom')
        
        try:
            conn = await self._get_connection()
            
            if action == 'create':
                sql = f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_{geometry_column}
                ON {table_name}
                USING GIST ({geometry_column})
                """
                await conn.execute(sql)
                result = {"success": True, "message": f"Spatial index created on {table_name}.{geometry_column}"}
            
            elif action == 'drop':
                sql = f"DROP INDEX IF EXISTS idx_{table_name}_{geometry_column}"
                await conn.execute(sql)
                result = {"success": True, "message": f"Spatial index dropped from {table_name}.{geometry_column}"}
            
            elif action == 'rebuild':
                sql = f"REINDEX INDEX idx_{table_name}_{geometry_column}"
                await conn.execute(sql)
                result = {"success": True, "message": f"Spatial index rebuilt for {table_name}.{geometry_column}"}
            
            else:
                result = {"success": False, "error": f"Unsupported action: {action}"}
            
            await self.pool.release(conn)
            return result
            
        except Exception as e:
            self.logger.error(f"Spatial index error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _risk_assessment_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询灾害风险评估数据"""
        disaster_type = params.get('disaster_type')
        region = params.get('region')
        risk_level = params.get('risk_level')
        date_range = params.get('date_range')
        
        try:
            conn = await self._get_connection()
            
            # 构建查询SQL
            sql = """
            SELECT 
                location,
                risk_score,
                risk_level,
                assessment_date,
                confidence_score,
                ST_AsGeoJSON(geom) as geometry
            FROM risk_assessment
            WHERE disaster_type = $1
            """
            
            query_params = [disaster_type]
            param_count = 1
            
            if region:
                sql += f" AND region = ${param_count + 1}"
                query_params.append(region)
                param_count += 1
            
            if risk_level:
                sql += f" AND risk_level = ${param_count + 1}"
                query_params.append(risk_level)
                param_count += 1
            
            if date_range and len(date_range) == 2:
                sql += f" AND assessment_date BETWEEN ${param_count + 1} AND ${param_count + 2}"
                query_params.extend(date_range)
                param_count += 2
            
            sql += " ORDER BY assessment_date DESC"
            
            # 执行查询
            rows = await conn.fetch(sql, *query_params)
            
            # 转换结果
            results = []
            for row in rows:
                row_dict = dict(row)
                if 'geometry' in row_dict and row_dict['geometry']:
                    row_dict['geometry'] = json.loads(row_dict['geometry'])
                results.append(row_dict)
            
            await self.pool.release(conn)
            
            return {
                "success": True,
                "count": len(results),
                "results": results,
                "query": sql
            }
            
        except Exception as e:
            self.logger.error(f"Risk assessment query error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _format_conversion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """地理空间数据格式转换"""
        input_file = params.get('input_file')
        input_format = params.get('input_format')
        output_file = params.get('output_file')
        output_format = params.get('output_format')
        target_srid = params.get('target_srid', 4326)
        
        try:
            if output_format == 'postgis':
                # 直接导入到PostGIS
                result = await self._data_import({
                    'file_path': input_file,
                    'file_format': input_format,
                    'table_name': output_file,  # 使用output_file作为表名
                    'srid': target_srid
                })
            else:
                # 使用GDAL工具进行格式转换
                result = await self._convert_with_gdal(
                    input_file, input_format, output_file, output_format, target_srid
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Format conversion error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _convert_with_gdal(self, input_file: str, input_format: str, output_file: str, output_format: str, target_srid: int) -> Dict[str, Any]:
        """使用GDAL工具进行格式转换"""
        try:
            if output_format == 'tiff':
                cmd = [
                    'gdal_translate',
                    '-of', 'GTiff',
                    '-a_srs', f'EPSG:{target_srid}',
                    input_file,
                    output_file
                ]
            elif output_format == 'netcdf':
                cmd = [
                    'gdal_translate',
                    '-of', 'NetCDF',
                    '-a_srs', f'EPSG:{target_srid}',
                    input_file,
                    output_file
                ]
            elif output_format == 'geojson':
                cmd = [
                    'ogr2ogr',
                    '-f', 'GeoJSON',
                    '-t_srs', f'EPSG:{target_srid}',
                    output_file,
                    input_file
                ]
            else:
                return {"success": False, "error": f"Unsupported output format: {output_format}"}
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"success": True, "message": f"File converted to {output_format}"}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": f"GDAL conversion failed: {str(e)}"}
    
    async def close(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()

async def main():
    """主函数"""
    server = PostGISDataServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
