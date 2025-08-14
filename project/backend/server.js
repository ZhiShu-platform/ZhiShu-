// server.js
require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const fetch = require('node-fetch'); // v2
const AbortController = require('abort-controller');

const app = express();
const port = process.env.PORT || 3000;

// --- Middleware ---
app.use(cors());
app.use(bodyParser.json({ limit: '1mb' })); // limit to 1MB to avoid runaway payloads

// --- Database connection configuration ---
const pool = new Pool({
  user: process.env.DB_USER,
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD,
  port: process.env.DB_PORT || 5432,
});

// -------------------- Helper utilities --------------------
/**
 * Safe JSON stringify for logging (truncates long values)
 */
function safeStringify(obj, maxLen = 2000) {
  try {
    const s = JSON.stringify(obj, null, 2);
    if (s.length > maxLen) return s.slice(0, maxLen) + '... (truncated)';
    return s;
  } catch (e) {
    return String(obj);
  }
}

/**
 * fetch with timeout and optional retries
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = 15000, retries = 1) {
  let lastErr = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const opts = Object.assign({}, options, { signal: controller.signal });
      const resp = await fetch(url, opts);
      clearTimeout(id);
      return resp;
    } catch (err) {
      clearTimeout(id);
      lastErr = err;
      if (attempt < retries) {
        console.warn(`fetch attempt ${attempt + 1} failed, retrying...`, err.message || err);
        await new Promise(r => setTimeout(r, 300)); // small backoff
        continue;
      } else {
        throw lastErr;
      }
    }
  }
  throw lastErr;
}

/**
 * Normalize frontend input into backend-expected input_data wrapper.
 * Build request body matching LangGraph's /process_emergency_event API spec.
 */
function buildLangGraphInput(reqBody, req) {
  const { question, context, user_id, session_id, location: loc, ...otherData } = reqBody || {};
  const currentSessionId = session_id || `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const userId = user_id || (reqBody.user && reqBody.user.id) || otherData.user_id || null;
  const requestTimestamp = new Date().toISOString();

  // Map question or content to user_prompt field
  const userPromptText = question ||
    (reqBody.content && (reqBody.content.user_prompt || reqBody.content.prompt || reqBody.content.text)) ||
    (reqBody.input && reqBody.input.content && (reqBody.input.content.user_prompt || reqBody.input.content.prompt || reqBody.input.content.text)) ||
    reqBody.prompt || "";

  // Location object must include latitude, longitude, region, country_iso (fill defaults if missing)
  const location = {
    latitude: (loc && typeof loc.latitude === 'number') ? loc.latitude : 0,
    longitude: (loc && typeof loc.longitude === 'number') ? loc.longitude : 0,
    region: (loc && loc.region) || "Unknown",
    country_iso: (loc && loc.country_iso) || ""
  };

  // 构建Python自然语言对话API的请求格式
  const payload = {
    message: userPromptText,
    session_id: currentSessionId,
    user_id: userId,
    context: {
      region: reqBody.context && reqBody.context.region,
      model: reqBody.context && reqBody.context.model,
      datasets: reqBody.context && reqBody.context.datasets,
      frontend_context: reqBody.frontend_context
    }
  };

  return { payload, currentSessionId, userId, requestTimestamp };
}

// -------------------- Auth routes --------------------
// user register
app.post('/api/register', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ message: '�û��������벻��Ϊ��' });
  }

  try {
    const salt = await bcrypt.genSalt(10);
    const passwordHash = await bcrypt.hash(password, salt);
    const newUser = await pool.query(
      'INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING id, username',
      [username, passwordHash]
    );
    res.status(201).json({ message: '�û�ע��ɹ�', user: newUser.rows[0] });
  } catch (err) {
    console.error('ע�����:', err.message);
    if (err.code === '23505') {
      res.status(409).json({ message: '�û����Ѵ���' });
    } else {
      res.status(500).json({ message: 'ע��ʧ��' });
    }
  }
});

// user login
app.post('/api/login', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ message: '�û��������벻��Ϊ��' });
  }

  try {
    const userResult = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
    const user = userResult.rows[0];
    if (!user) {
      return res.status(400).json({ message: '�û��������벻��ȷ' });
    }

    const isMatch = await bcrypt.compare(password, user.password_hash);
    if (!isMatch) {
      return res.status(400).json({ message: '�û��������벻��ȷ' });
    }

    res.status(200).json({ message: '��¼�ɹ�', user: { id: user.id, username: user.username } });
  } catch (err) {
    console.error('��¼����:', err.message);
    res.status(500).json({ message: '��¼ʧ��' });
  }
});

// ==========================================================
// === API endpoint to handle AI chat requests (Proxy to LangGraph) ===
// ==========================================================
app.post('/api/chat', async (req, res) => {
  console.log('?? �յ��������� (truncated):', safeStringify(req.body, 1000));

  // Validate presence of question/prompt
  const maybeQuestion = req.body && (
    req.body.question ||
    (req.body.content && (req.body.content.user_prompt || req.body.content.prompt || req.body.content.text)) ||
    req.body.prompt ||
    (req.body.input && req.body.input.content && (req.body.input.content.user_prompt || req.body.input.content.prompt || req.body.input.content.text))
  );
  if (!maybeQuestion) {
    console.error('? ����ȱ�� question/prompt �ֶ�');
    return res.status(400).json({
      message: '�������ݲ���Ϊ��',
      error_code: 'MISSING_QUESTION'
    });
  }

  const { payload, currentSessionId, userId, requestTimestamp } = buildLangGraphInput(req.body, req);

  // LangGraph backend URL, can be overridden by env
  // 使用本地Python后端的自然语言对话API
  const langGraphUrl = process.env.LANGGRAPH_URL || 'http://localhost:2024/chat';

  try {
    console.log(`?? Forwarding to LangGraph: session=${currentSessionId} user=${userId || 'anonymous'}`);
    console.debug('?? LangGraph payload (truncated):', safeStringify(payload, 1500));

    const startTime = Date.now();
    const response = await fetchWithTimeout(langGraphUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': currentSessionId,
        'X-User-ID': userId || '',
        'X-Request-Source': 'frontend'
      },
      body: JSON.stringify(payload),
    }, 20000, 1);
    const elapsed = Date.now() - startTime;
    console.log(`?? LangGraph request finished in ${elapsed}ms (status ${response.status})`);

    let bodyText = null;
    let backend = null;
    try {
      bodyText = await response.text();
      const trimmed = bodyText.trim();
      if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        backend = JSON.parse(trimmed);
      } else {
        backend = { raw: trimmed };
      }
    } catch (parseErr) {
      console.warn('?? �޷����������ӦΪ JSON������ԭʼ�ı�', parseErr.message || parseErr);
      backend = { raw: bodyText || '' };
    }

    if (!response.ok) {
      console.error('? LangGraph API ����:', response.status, safeStringify(backend, 2000));
      return res.status(502).json({
        success: false,
        message: `LangGraph backend returned status ${response.status}`,
        backend: backend
      });
    }

    // 根据后端返回的结构自动处理响应格式，将最终的回复作为直接返回
    // 处理Python自然语言对话API的响应格式
    const reply = backend.response && backend.response.content ? backend.response.content : 
                  backend.human_readable_summary || backend.final_report || JSON.stringify(backend);

    const responsePayload = {
      reply,
      session_info: { 
        session_id: currentSessionId, 
        user_id: userId, 
        processing_time_ms: elapsed, 
        timestamp: requestTimestamp 
      },
      success: true,
      timestamp: new Date().toISOString(),
      // 添加Python API的额外信息
      intent: backend.response && backend.response.intent,
      confidence: backend.response && backend.response.confidence,
      response_type: backend.response && backend.response.response_type,
      backend_raw: (process.env.NODE_ENV === 'development') ? safeStringify(backend, 2000) : undefined
    };

    console.log(`? Completed session ${currentSessionId} in ${elapsed}ms`);
    return res.status(200).json(responsePayload);

  } catch (err) {
    console.error('? LangGraph Chat API ����:', err && err.message ? err.message : err);
    const currentSessionId = (req.body && (req.body.session_id || req.body.session)) || `chat_err_${Date.now()}`;
    const errorResponse = {
      reply: `��Ǹ��������������ʱ�����˼������⡣\n\n������Ϣ: ${err && err.message ? err.message : String(err)}\n�ỰID: ${currentSessionId}\nʱ��: ${new Date().toLocaleString('zh-CN')}\n\n���Ժ����ԣ�����ϵ����֧���Ŷӡ�`,
      session_info: {
        session_id: currentSessionId,
        user_id: (req.body && (req.body.user_id || (req.body.user && req.body.user.id))) || null,
        error: true,
        timestamp: new Date().toISOString()
      },
      success: false,
      error_details: {
        message: err && err.message ? err.message : String(err),
        type: err && err.name ? err.name : 'UnknownError'
      },
      timestamp: new Date().toISOString()
    };
    return res.status(500).json(errorResponse);
  }
});

// ==========================================================
// === LangGraph health check API ===
app.get('/api/langgraph/health', async (req, res) => {
  try {
    const healthUrl = process.env.LANGGRAPH_HEALTH_URL || 'http://10.0.3.4:2024/system_health';
    const healthResponse = await fetchWithTimeout(healthUrl, { method: 'GET' }, 5000, 0);
    if (!healthResponse.ok) {
      const errTxt = await healthResponse.text();
      throw new Error(`Health check failed: ${errTxt}`);
    }
    const healthJson = await healthResponse.json();
    res.status(200).json(healthJson);
  } catch (err) {
    console.error('LangGraph Health Check Error:', err.message || err);
    res.status(500).json({
      success: false,
      message: `LangGraph Health Check failed: ${err.message || err}`
    });
  }
});

// ==========================================================
// === 工作流管理和MCP服务控制API ===

// 模拟MCP服务状态数据
let mcpServices = [
  {
    name: 'nfdrs4',
    display_name: 'NFDRS4火灾风险评估',
    status: 'stopped',
    conda_env: 'NFDRS4',
    host_path: '/data/Tiaozhanbei/NFDRS4',
    port: 8004,
    error_message: null,
    pid: null
  },
  {
    name: 'lisflood',
    display_name: 'LISFLOOD洪水仿真',
    status: 'stopped',
    conda_env: 'Lisflood',
    host_path: '/data/Tiaozhanbei/Lisflood',
    port: 8002,
    error_message: null,
    pid: null
  },
  {
    name: 'climada',
    display_name: 'CLIMADA气候风险评估',
    status: 'stopped',
    conda_env: 'Climada',
    host_path: '/data/Tiaozhanbei/Climada',
    port: 8001,
    error_message: null,
    pid: null
  },
  {
    name: 'aurora',
    display_name: 'Aurora极光预测',
    status: 'stopped',
    conda_env: 'aurora',
    host_path: '/data/Tiaozhanbei/aurora-main',
    port: 8006,
    error_message: null,
    pid: null
  },
  {
    name: 'cell2fire',
    display_name: 'Cell2Fire火灾蔓延仿真',
    status: 'stopped',
    conda_env: 'Cell2Fire',
    host_path: '/data/Tiaozhanbei/Cell2Fire',
    port: 8005,
    error_message: null,
    pid: null
  }
];

// 模拟工作流实例数据
let workflowInstances = [];

// 模拟工作流定义
const workflowDefinitions = [
  {
    name: 'nfdrs4_fire_risk_assessment',
    description: 'NFDRS4火灾风险评估完整工作流',
    version: '1.0.0',
    step_count: 4,
    parameters_schema: {
      type: 'object',
      properties: {
        location: { type: 'string', description: '火灾发生地点' },
        coordinates: { type: 'object', description: '地理坐标' },
        fuel_type: { type: 'string', description: '燃料类型' },
        weather_conditions: { type: 'string', description: '天气条件' }
      },
      required: ['location', 'coordinates']
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    name: 'lisflood_flood_risk_assessment',
    description: 'LISFLOOD洪水风险评估完整工作流',
    version: '1.0.0',
    step_count: 4,
    parameters_schema: {
      type: 'object',
      properties: {
        location: { type: 'string', description: '洪水发生地点' },
        coordinates: { type: 'object', description: '地理坐标' },
        water_level: { type: 'number', description: '水位高度' },
        rainfall_intensity: { type: 'string', description: '降雨强度' }
      },
      required: ['location', 'coordinates']
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    name: 'climada_climate_risk_assessment',
    description: 'CLIMADA气候风险评估完整工作流',
    version: '1.0.0',
    step_count: 4,
    parameters_schema: {
      type: 'object',
      properties: {
        location: { type: 'string', description: '气候事件发生地点' },
        coordinates: { type: 'object', description: '地理坐标' },
        climate_type: { type: 'string', description: '气候类型' },
        wind_speed: { type: 'number', description: '风速' }
      },
      required: ['location', 'coordinates']
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    name: 'comprehensive_disaster_assessment',
    description: '综合灾害评估工作流（多模型协同）',
    version: '1.0.0',
    step_count: 5,
    parameters_schema: {
      type: 'object',
      properties: {
        location: { type: 'string', description: '灾害发生地点' },
        coordinates: { type: 'object', description: '地理坐标' },
        disaster_types: { type: 'array', description: '灾害类型列表' }
      },
      required: ['location', 'coordinates', 'disaster_types']
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

// MCP服务管理API
app.get('/api/mcp/services', (req, res) => {
  res.json({ services: mcpServices });
});

app.post('/api/mcp/services/start', (req, res) => {
  const { service_name, action } = req.body;
  
  if (!service_name || !action) {
    return res.status(400).json({
      success: false,
      message: '缺少必要参数'
    });
  }
  
  const service = mcpServices.find(s => s.name === service_name);
  if (!service) {
    return res.status(404).json({
      success: false,
      message: `服务 ${service_name} 不存在`
    });
  }
  
  try {
    if (action === 'start') {
      service.status = 'running';
      service.pid = Math.floor(Math.random() * 10000) + 1000;
      service.error_message = null;
      console.log(`✅ 服务 ${service_name} 启动成功，PID: ${service.pid}`);
    } else if (action === 'stop') {
      service.status = 'stopped';
      service.pid = null;
      service.error_message = null;
      console.log(`🛑 服务 ${service_name} 停止成功`);
    } else if (action === 'restart') {
      service.status = 'running';
      service.pid = Math.floor(Math.random() * 10000) + 1000;
      service.error_message = null;
      console.log(`🔄 服务 ${service_name} 重启成功，PID: ${service.pid}`);
    } else {
      return res.status(400).json({
        success: false,
        message: '不支持的操作'
      });
    }
    
    res.json({
      success: true,
      message: `服务 ${service_name} ${action === 'start' ? '启动' : action === 'stop' ? '停止' : '重启'}成功`
    });
  } catch (error) {
    console.error(`❌ 服务 ${service_name} 操作失败:`, error);
    res.status(500).json({
      success: false,
      message: `操作失败: ${error.message}`
    });
  }
});

app.post('/api/mcp/services/start-all', (req, res) => {
  try {
    mcpServices.forEach(service => {
      service.status = 'running';
      service.pid = Math.floor(Math.random() * 10000) + 1000;
      service.error_message = null;
    });
    
    console.log('✅ 所有MCP服务启动成功');
    res.json({
      success: true,
      message: '所有服务启动成功'
    });
  } catch (error) {
    console.error('❌ 启动所有服务失败:', error);
    res.status(500).json({
      success: false,
      message: `启动失败: ${error.message}`
    });
  }
});

app.post('/api/mcp/services/stop-all', (req, res) => {
  try {
    mcpServices.forEach(service => {
      service.status = 'stopped';
      service.pid = null;
      service.error_message = null;
    });
    
    console.log('🛑 所有MCP服务停止成功');
    res.json({
      success: true,
      message: '所有服务停止成功'
    });
  } catch (error) {
    console.error('❌ 停止所有服务失败:', error);
    res.status(500).json({
      success: false,
      message: `停止失败: ${error.message}`
    });
  }
});

app.post('/api/mcp/call', (req, res) => {
  const { service_name, tool_name, arguments: args } = req.body;
  
  if (!service_name || !tool_name) {
    return res.status(400).json({
      success: false,
      message: '缺少必要参数'
    });
  }
  
  const service = mcpServices.find(s => s.name === service_name);
  if (!service) {
    return res.status(404).json({
      success: false,
      message: `服务 ${service_name} 不存在`
    });
  }
  
  if (service.status !== 'running') {
    return res.status(400).json({
      success: false,
      message: `服务 ${service_name} 未运行`
    });
  }
  
  // 模拟MCP调用
  const result = {
    success: true,
    service: service_name,
    tool: tool_name,
    arguments: args,
    result: `模拟${service_name}服务${tool_name}工具执行结果`,
    timestamp: new Date().toISOString(),
    execution_time: 1.5
  };
  
  console.log(`🔬 MCP调用: ${service_name}.${tool_name}`);
  res.json(result);
});

// 工作流管理API
app.get('/api/workflows', (req, res) => {
  res.json({ workflows: workflowDefinitions });
});

app.get('/api/workflows/instances', (req, res) => {
  const instances = workflowInstances.map(instance => ({
    id: instance.id,
    workflow_name: instance.workflow_name,
    status: instance.status,
    current_step: instance.current_step,
    start_time: instance.start_time,
    end_time: instance.end_time,
    total_execution_time: instance.total_execution_time,
    created_at: instance.created_at
  }));
  
  res.json({ instances });
});

app.post('/api/workflows/start', (req, res) => {
  const { workflow_name, parameters } = req.body;
  
  if (!workflow_name) {
    return res.status(400).json({
      success: false,
      message: '缺少工作流名称'
    });
  }
  
  const definition = workflowDefinitions.find(w => w.name === workflow_name);
  if (!definition) {
    return res.status(404).json({
      success: false,
      message: `工作流 ${workflow_name} 不存在`
    });
  }
  
  // 创建新的工作流实例
  const instance = {
    id: `wf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    workflow_name,
    parameters,
    steps: [
      { id: 'step_1', name: '数据获取', description: '从数据库获取相关数据', status: 'pending' },
      { id: 'step_2', name: '模型调用', description: '调用MCP服务进行分析', status: 'pending' },
      { id: 'step_3', name: '结果保存', description: '将分析结果保存到数据库', status: 'pending' },
      { id: 'step_4', name: '前端展示', description: '通过GeoServer发布结果', status: 'pending' }
    ],
    status: 'pending',
    current_step: null,
    start_time: new Date().toISOString(),
    end_time: null,
    total_execution_time: null,
    created_at: new Date().toISOString()
  };
  
  workflowInstances.push(instance);
  
  // 模拟工作流执行（在实际应用中应该使用后台任务）
  setTimeout(() => {
    simulateWorkflowExecution(instance.id);
  }, 1000);
  
  console.log(`🚀 工作流 ${workflow_name} 启动成功，实例ID: ${instance.id}`);
  
  res.json({
    success: true,
    instance_id: instance.id,
    message: `工作流 ${workflow_name} 启动成功`
  });
});

app.get('/api/workflows/instances/:instance_id', (req, res) => {
  const { instance_id } = req.params;
  const instance = workflowInstances.find(i => i.id === instance_id);
  
  if (!instance) {
    return res.status(404).json({
      success: false,
      message: '工作流实例不存在'
    });
  }
  
  res.json({ instance });
});

app.post('/api/workflows/instances/:instance_id/cancel', (req, res) => {
  const { instance_id } = req.params;
  const instance = workflowInstances.find(i => i.id === instance_id);
  
  if (!instance) {
    return res.status(404).json({
      success: false,
      message: '工作流实例不存在'
    });
  }
  
  if (instance.status === 'completed' || instance.status === 'failed') {
    return res.status(400).json({
      success: false,
      message: '无法取消已完成的工作流'
    });
  }
  
  instance.status = 'cancelled';
  instance.end_time = new Date().toISOString();
  
  console.log(`❌ 工作流实例 ${instance_id} 已取消`);
  
  res.json({
    success: true,
    message: '工作流取消成功'
  });
});

// 实时监控API
app.get('/api/monitor/status', (req, res) => {
  const service_stats = {
    total: mcpServices.length,
    running: mcpServices.filter(s => s.status === 'running').length,
    stopped: mcpServices.filter(s => s.status === 'stopped').length,
    error: mcpServices.filter(s => s.status === 'error').length
  };
  
  const workflow_stats = {
    total: workflowInstances.length,
    running: workflowInstances.filter(i => i.status === 'running').length,
    completed: workflowInstances.filter(i => i.status === 'completed').length,
    failed: workflowInstances.filter(i => i.status === 'failed').length
  };
  
  res.json({
    timestamp: new Date().toISOString(),
    service_stats,
    workflow_stats,
    active_connections: 0 // 这里应该实现真实的连接计数
  });
});

app.get('/api/monitor/logs', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  
  // 模拟系统日志
  const logs = [
    {
      timestamp: new Date().toISOString(),
      level: 'INFO',
      message: '系统运行正常',
      source: 'system'
    }
  ];
  
  res.json({ logs: logs.slice(0, limit) });
});

// 健康检查
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    mcp_manager: true,
    workflow_engine: true
  });
});

// 模拟工作流执行
function simulateWorkflowExecution(instanceId) {
  const instance = workflowInstances.find(i => i.id === instanceId);
  if (!instance) return;
  
  instance.status = 'running';
  instance.current_step = 'step_1';
  
  // 模拟步骤执行
  const steps = ['step_1', 'step_2', 'step_3', 'step_4'];
  let currentStepIndex = 0;
  
  const executeStep = () => {
    if (currentStepIndex >= steps.length) {
      instance.status = 'completed';
      instance.current_step = null;
      instance.end_time = new Date().toISOString();
      instance.total_execution_time = (new Date(instance.end_time) - new Date(instance.start_time)) / 1000;
      console.log(`✅ 工作流实例 ${instanceId} 执行完成`);
      return;
    }
    
    const stepId = steps[currentStepIndex];
    const step = instance.steps.find(s => s.id === stepId);
    
    if (step) {
      step.status = 'running';
      instance.current_step = stepId;
      
      // 模拟步骤执行时间
      setTimeout(() => {
        step.status = 'completed';
        step.result = `步骤 ${step.name} 执行成功`;
        step.execution_time = 2.0;
        
        currentStepIndex++;
        executeStep();
      }, 2000);
    }
  };
  
  executeStep();
}

// === launch server ===
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port} (env=${process.env.NODE_ENV || 'production'})`);
  console.log('🚀 MCP工作流管理系统已启动');
  console.log('📊 可用的API端点:');
  console.log('   GET  /api/mcp/services - 获取MCP服务状态');
  console.log('   POST /api/mcp/services/start - 控制MCP服务');
  console.log('   GET  /api/workflows - 获取工作流定义');
  console.log('   POST /api/workflows/start - 启动工作流');
  console.log('   GET  /api/monitor/status - 获取系统状态');
});
