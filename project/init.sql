-- PostgreSQL数据库初始化脚本
-- 灾害管理系统数据库结构

-- 启用PostGIS扩展
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建会话表
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 创建灾害事件表
CREATE TABLE IF NOT EXISTS disaster_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    disaster_type VARCHAR(50) NOT NULL,
    severity_level VARCHAR(20) NOT NULL,
    location_name VARCHAR(200),
    geom GEOMETRY(POINT, 4326),
    affected_area_km2 DECIMAL(10,2),
    estimated_population INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建风险评估表
CREATE TABLE IF NOT EXISTS risk_assessment (
    id SERIAL PRIMARY KEY,
    assessment_id VARCHAR(100) UNIQUE NOT NULL,
    disaster_type VARCHAR(50) NOT NULL,
    region VARCHAR(100) NOT NULL,
    risk_score DECIMAL(5,2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(3,2),
    assessment_date DATE NOT NULL,
    geom GEOMETRY(POLYGON, 4326),
    methodology TEXT,
    data_sources TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建天气数据表
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(50) NOT NULL,
    observation_time TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    precipitation DECIMAL(8,2),
    wind_speed DECIMAL(5,2),
    wind_direction DECIMAL(5,2),
    pressure DECIMAL(8,2),
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建基础设施表
CREATE TABLE IF NOT EXISTS infrastructure (
    id SERIAL PRIMARY KEY,
    facility_id VARCHAR(100) UNIQUE NOT NULL,
    facility_type VARCHAR(50) NOT NULL,
    facility_name VARCHAR(200) NOT NULL,
    capacity INTEGER,
    status VARCHAR(20) DEFAULT 'operational',
    geom GEOMETRY(POINT, 4326),
    address TEXT,
    contact_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建传感器数据表
CREATE TABLE IF NOT EXISTS sensor_data (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(100) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    reading_time TIMESTAMP NOT NULL,
    reading_value DECIMAL(10,4),
    unit VARCHAR(20),
    geom GEOMETRY(POINT, 4326),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建工作流执行记录表
CREATE TABLE IF NOT EXISTS workflow_executions (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) UNIQUE NOT NULL,
    workflow_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'running',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建MCP调用记录表
CREATE TABLE IF NOT EXISTS mcp_calls (
    id SERIAL PRIMARY KEY,
    call_id VARCHAR(100) UNIQUE NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    input_parameters JSONB,
    output_result JSONB,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建空间索引
CREATE INDEX IF NOT EXISTS idx_disaster_events_geom ON disaster_events USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_risk_assessment_geom ON risk_assessment USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_weather_data_geom ON weather_data USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_infrastructure_geom ON infrastructure USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_sensor_data_geom ON sensor_data USING GIST (geom);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_disaster_events_time ON disaster_events (start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_weather_data_time ON weather_data (observation_time);
CREATE INDEX IF NOT EXISTS idx_sensor_data_time ON sensor_data (reading_time);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_time ON workflow_executions (start_time, end_time);

-- 创建复合索引
CREATE INDEX IF NOT EXISTS idx_disaster_events_type_status ON disaster_events (disaster_type, status);
CREATE INDEX IF NOT EXISTS idx_risk_assessment_type_region ON risk_assessment (disaster_type, region);
CREATE INDEX IF NOT EXISTS idx_weather_data_station_time ON weather_data (station_id, observation_time);

-- 插入示例数据
INSERT INTO users (username, email, full_name, role) VALUES
('admin', 'admin@emergency.gov', '系统管理员', 'admin'),
('analyst', 'analyst@emergency.gov', '数据分析师', 'analyst'),
('operator', 'operator@emergency.gov', '操作员', 'operator')
ON CONFLICT (username) DO NOTHING;

-- 插入示例灾害事件
INSERT INTO disaster_events (event_id, disaster_type, severity_level, location_name, geom, affected_area_km2, estimated_population, start_time, description) VALUES
('EVT_001', 'flood', 'high', '长江中下游地区', ST_GeomFromText('POINT(114.3 30.6)', 4326), 1500.5, 500000, '2024-01-15 08:00:00', '长江中下游地区发生严重洪涝灾害'),
('EVT_002', 'earthquake', 'moderate', '四川雅安地区', ST_GeomFromText('POINT(103.0 30.0)', 4326), 200.0, 100000, '2024-01-16 14:30:00', '四川雅安地区发生5.2级地震')
ON CONFLICT (event_id) DO NOTHING;

-- 插入示例风险评估
INSERT INTO risk_assessment (assessment_id, disaster_type, region, risk_score, risk_level, confidence_score, assessment_date, geom) VALUES
('RISK_001', 'flood', '长江流域', 8.5, 'high', 0.85, '2024-01-15', ST_GeomFromText('POLYGON((114.0 30.0, 115.0 30.0, 115.0 31.0, 114.0 31.0, 114.0 30.0))', 4326)),
('RISK_002', 'earthquake', '四川盆地', 6.2, 'moderate', 0.78, '2024-01-16', ST_GeomFromText('POLYGON((102.5 29.5, 103.5 29.5, 103.5 30.5, 102.5 30.5, 102.5 29.5))', 4326))
ON CONFLICT (assessment_id) DO NOTHING;

-- 插入示例天气数据
INSERT INTO weather_data (station_id, observation_time, temperature, humidity, precipitation, wind_speed, wind_direction, pressure, geom) VALUES
('WX_001', '2024-01-15 08:00:00', 25.5, 78.0, 15.2, 3.2, 180.0, 1013.25, ST_GeomFromText('POINT(114.3 30.6)', 4326)),
('WX_002', '2024-01-15 08:00:00', 22.1, 65.0, 0.0, 2.1, 90.0, 1015.30, ST_GeomFromText('POINT(103.0 30.0)', 4326))
ON CONFLICT DO NOTHING;

-- 插入示例基础设施
INSERT INTO infrastructure (facility_id, facility_type, facility_name, capacity, geom, address) VALUES
('INF_001', 'hospital', '武汉市第一人民医院', 800, ST_GeomFromText('POINT(114.3 30.6)', 4326), '湖北省武汉市江岸区解放大道238号'),
('INF_002', 'fire_station', '雅安市消防支队', 50, ST_GeomFromText('POINT(103.0 30.0)', 4326), '四川省雅安市雨城区雅州大道')
ON CONFLICT (facility_id) DO NOTHING;

-- 创建视图
CREATE OR REPLACE VIEW disaster_summary AS
SELECT 
    de.event_id,
    de.disaster_type,
    de.severity_level,
    de.location_name,
    de.affected_area_km2,
    de.estimated_population,
    de.start_time,
    de.status,
    ra.risk_score,
    ra.risk_level,
    ST_AsGeoJSON(de.geom) as geometry
FROM disaster_events de
LEFT JOIN risk_assessment ra ON ST_Intersects(de.geom, ra.geom)
WHERE de.status = 'active';

-- 创建函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
CREATE TRIGGER update_disaster_events_updated_at 
    BEFORE UPDATE ON disaster_events 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_infrastructure_updated_at 
    BEFORE UPDATE ON infrastructure 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建空间查询函数
CREATE OR REPLACE FUNCTION get_disasters_in_radius(
    center_lat DECIMAL,
    center_lon DECIMAL,
    radius_km DECIMAL
)
RETURNS TABLE(
    event_id VARCHAR(100),
    disaster_type VARCHAR(50),
    severity_level VARCHAR(20),
    location_name VARCHAR(200),
    distance_km DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.event_id,
        de.disaster_type,
        de.severity_level,
        de.location_name,
        ST_Distance(
            de.geom::geography,
            ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography
        ) / 1000.0 as distance_km
    FROM disaster_events de
    WHERE ST_DWithin(
        de.geom::geography,
        ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography,
        radius_km * 1000.0
    )
    ORDER BY distance_km;
END;
$$ LANGUAGE plpgsql;

-- 创建风险评估聚合函数
CREATE OR REPLACE FUNCTION get_risk_summary_by_region()
RETURNS TABLE(
    region VARCHAR(100),
    disaster_type VARCHAR(50),
    avg_risk_score DECIMAL(5,2),
    max_risk_score DECIMAL(5,2),
    risk_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ra.region,
        ra.disaster_type,
        AVG(ra.risk_score) as avg_risk_score,
        MAX(ra.risk_score) as max_risk_score,
        COUNT(*) as risk_count
    FROM risk_assessment ra
    GROUP BY ra.region, ra.disaster_type
    ORDER BY ra.region, AVG(ra.risk_score) DESC;
END;
$$ LANGUAGE plpgsql;

-- 设置权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zs_zzr;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zs_zzr;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO zs_zzr;

-- 创建只读用户（可选）
-- CREATE USER emergency_reader WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE zs_data TO emergency_reader;
-- GRANT USAGE ON SCHEMA public TO emergency_reader;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO emergency_reader;

COMMENT ON DATABASE zs_data IS '灾害管理系统数据库';
COMMENT ON TABLE disaster_events IS '灾害事件记录表';
COMMENT ON TABLE risk_assessment IS '风险评估结果表';
COMMENT ON TABLE weather_data IS '天气观测数据表';
COMMENT ON TABLE infrastructure IS '基础设施信息表';
COMMENT ON TABLE sensor_data IS '传感器数据表';
COMMENT ON TABLE workflow_executions IS '工作流执行记录表';
COMMENT ON TABLE mcp_calls IS 'MCP服务调用记录表';
