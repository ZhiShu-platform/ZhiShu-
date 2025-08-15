const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
require('dotenv').config();
// 如果需要从后端调用其他API，建议使用axios或node-fetch
const fetch = require('node-fetch'); // 确保已安装: npm install node-fetch@2

const app = express();
const port = process.env.PORT || 3000;

// --- 中间件 ---
app.use(cors());
app.use(bodyParser.json());

// --- 数据库连接配置 ---
const pool = new Pool({
  user: process.env.DB_USER,
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD,
  port: process.env.DB_PORT || 5432,
});

// --- API 路由 ---


app.post('/api/register', async (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ message: '用户名和密码不能为空' });
  }

  try {
    const salt = await bcrypt.genSalt(10);
    const passwordHash = await bcrypt.hash(password, salt);

    const newUser = await pool.query(
      "INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING id, username",
      [username, passwordHash]
    );

    res.status(201).json({
      message: '注册成功',
      user: newUser.rows[0]
    });

  } catch (err) {
    if (err.code === '23505') { 
      return res.status(409).json({ message: '注册失败：用户名已存在' });
    }
    console.error(err.message);
    res.status(500).json({ message: '服务器错误' });
  }
});

app.post('/api/login', async (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ message: '用户名和密码不能为空' });
  }

  try {
    const userResult = await pool.query("SELECT * FROM users WHERE username = $1", [username]);

    if (userResult.rows.length === 0) {
      return res.status(401).json({ message: '登录失败：用户名或密码错误' });
    }

    const user = userResult.rows[0];
    const isMatch = await bcrypt.compare(password, user.password_hash);

    if (!isMatch) {
      return res.status(401).json({ message: '登录失败：用户名或密码错误' });
    }

    res.status(200).json({
      message: '登录成功',
      user: {
        id: user.id,
        username: user.username,
      }
    });

  } catch (err) {
    console.error(err.message);
    res.status(500).json({ message: '服务器错误' });
  }
});


// ==========================================================
// === 新增：处理AI聊天请求的API端点 (Proxy to LangGraph) ===
// ==========================================================
app.post('/api/chat', async (req, res) => {
  const { question, context } = req.body;

  if (!question) {
    return res.status(400).json({ message: '问题内容不能为空' });
  }

  try {
    // --- 关键步骤：调用LangGraph应急管理系统 ---

    // 1. 将前端数据转换为LangGraph期望的input_data格式
    const input_data = {
      user_question: question,
      region: context.region || '未指定',
      model_info: context.model ? {
        name: context.model.name,
        type: context.model.type || 'unknown'
      } : null,
      datasets: context.datasets && context.datasets.length > 0 
        ? context.datasets.map(d => ({ name: d.name, source: d.source }))
        : [],
      emergency_type: 'general_inquiry', // 可以根据问题内容智能分类
      severity_level: 'low', // 默认低级别查询
      timestamp: new Date().toISOString()
    };

    console.log("--- Sending to LangGraph ---");
    console.log("Input Data:", JSON.stringify(input_data, null, 2));
    console.log("-----------------------------");
    
    // 2. 调用LangGraph API
    const langgraphUrl = 'http://10.0.3.4:2024/process_emergency_event';
    
    const langgraphResponse = await fetch(langgraphUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input_data })
    });

    if (!langgraphResponse.ok) {
      const errorText = await langgraphResponse.text();
      throw new Error(`LangGraph服务调用失败: ${errorText}`);
    }

    const langgraphResult = await langgraphResponse.json();
    
    console.log("--- LangGraph Response ---");
    console.log("Result:", JSON.stringify(langgraphResult, null, 2));
    console.log("-------------------------");
    
    // 3. 从final_report中提取用户友好的回复
    let aiReply = '';
    
    if (langgraphResult.final_report) {
      const report = langgraphResult.final_report;
      
      // 构建综合回复
      let replyParts = [];
      
      if (report.alerts && report.alerts.length > 0) {
        replyParts.push(`**警报信息:**\n${report.alerts.map(alert => `- ${alert.message || alert.description || JSON.stringify(alert)}`).join('\n')}`);
      }
      
      if (report.recommendations && report.recommendations.length > 0) {
        replyParts.push(`**建议措施:**\n${report.recommendations.map(rec => `- ${rec.action || rec.description || JSON.stringify(rec)}`).join('\n')}`);
      }
      
      if (report.processing_log && report.processing_log.length > 0) {
        const lastLog = report.processing_log[report.processing_log.length - 1];
        if (lastLog.message) {
          replyParts.push(`**分析结果:** ${lastLog.message}`);
        }
      }
      
      if (report.summary) {
        replyParts.push(`**总结:** ${report.summary}`);
      }
      
      // 如果没有有效内容，使用原始数据的字符串表示
      if (replyParts.length === 0) {
        aiReply = `基于您的问题"${question}"，我已经通过应急管理系统进行了分析。系统返回了详细的处理结果，包含了多个方面的信息。如需要更具体的分析，请提供更多背景信息。`;
      } else {
        aiReply = replyParts.join('\n\n');
      }
    } else {
      aiReply = `抱歉，应急管理系统处理您的请求时出现了问题。请稍后重试或联系系统管理员。`;
    }

    // 4. 将回复发送回前端
    res.status(200).json({ reply: aiReply });

  } catch (err) {
    console.error('LangGraph Chat API Error:', err.message);
    res.status(500).json({ message: `与应急管理系统通信时发生错误: ${err.message}` });
  }
});

// ==========================================================
// === LangGraph Health Check API ===
// ==========================================================
app.get('/api/langgraph/health', async (req, res) => {
  try {
    const healthUrl = 'http://10.0.3.4:2024/system_health';
    
    const healthResponse = await fetch(healthUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!healthResponse.ok) {
      const errorText = await healthResponse.text();
      throw new Error(`Health check failed: ${errorText}`);
    }

    const healthResult = await healthResponse.json();
    
    res.status(200).json({
      success: true,
      langgraph_status: healthResult
    });

  } catch (err) {
    console.error('LangGraph Health Check Error:', err.message);
    res.status(500).json({ 
      success: false,
      message: `LangGraph健康检查失败: ${err.message}`,
      langgraph_status: null
    });
  }
});


// --- 启动服务器 ---
app.listen(port, () => {
  console.log(`后端服务运行在 http://localhost:${port}`);
});