"""
LLM integration for the emergency management platform.
This version supports both structured (JSON) and natural language outputs.
"""
import json
import os
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
from langfuse import observe, get_client

from .config import config
from .models import DisasterType, AlertLevel

class LLMClient:
    """LLM client with monitoring integration."""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(
            api_key=config.api.deepseek_api_key,
            base_url=config.api.deepseek_base_url
        )
        
        # Initialize Langfuse for monitoring
        if config.api.langfuse_secret_key and config.api.langfuse_public_key:
            # Set environment variables for get_client()
            os.environ["LANGFUSE_SECRET_KEY"] = config.api.langfuse_secret_key
            os.environ["LANGFUSE_PUBLIC_KEY"] = config.api.langfuse_public_key
            os.environ["LANGFUSE_HOST"] = config.api.langfuse_host
            
            try:
                self.langfuse = get_client()
            except Exception as e:
                print(f"Failed to initialize Langfuse: {e}")
                self.langfuse = None
        else:
            self.langfuse = None
    
    @observe()
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        agent_role: str = "assistant",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate response using DeepSeek API with monitoring.
        This is a core method that handles the API call.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            return content
            
        except Exception as e:
            raise e
            
    # --- 新增功能：生成自然语言报告 ---
    
    @observe()
    async def generate_natural_language_report(
        self,
        event_summary: str,
        disaster_type: DisasterType,
        alert_level: AlertLevel
    ) -> str:
        """
        Generates a detailed, natural language report for an emergency event.
        The LLM is instructed to respond in a clear, concise, and professional tone.
        """
        system_prompt = f"""You are an emergency management expert. Your task is to write a detailed, professional, and clear report based on the provided emergency event summary. The report should be easy for a human to understand and should include:
1.  **Situation Overview**: A brief summary of the event.
2.  **Disaster Type and Alert Level**: Clearly state the type of disaster and the current alert level.
3.  **Potential Impact**: Describe the potential consequences of the event.
4.  **Recommended Actions**: Provide a list of actionable steps for response teams and the public.
5.  **Next Steps**: What to do next (e.g., monitor, gather more data).

Please write the report in a natural, professional tone. Do not use JSON or any other structured format."""
        
        user_prompt = f"""Please generate an emergency report for the following event:
Event Summary: {event_summary}
Disaster Type: {disaster_type.value}
Alert Level: {alert_level.value}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用核心生成函数，返回自然语言文本
        response = await self.generate_response(
            messages=messages,
            agent_role="report_generator",
            temperature=0.6,
            max_tokens=1000
        )
        
        return response

    # --- 保留并修改原有 JSON 解析函数，移除不必要的 JSON 提示 ---

    @observe()
    async def analyze_disaster_data(
        self,
        disaster_data: Dict[str, Any],
        disaster_type: DisasterType
    ) -> Dict[str, Any]:
        """Analyze disaster data and provide expert assessment."""
        
        system_prompt = f"""You are an expert {disaster_type.value} analyst with extensive knowledge in disaster prediction and response.
Analyze the provided data and provide:
1.  Risk assessment (low/moderate/high/critical)
2.  Predicted impact and timeline
3.  Recommended response actions
4.  Confidence level (0-1)
5.  Key factors influencing the assessment

Respond in JSON format only."""
        
        user_prompt = f"Analyze this {disaster_type.value} data: {json.dumps(disaster_data, default=str)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.generate_response(
            messages=messages,
            agent_role=f"{disaster_type.value}_expert",
            temperature=0.3
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails - return natural language response
            return {
                "risk_assessment": "moderate",
                "predicted_impact": "Analysis failed, defaulting to moderate risk.",
                "recommended_actions": ["monitor situation", "prepare response teams"],
                "confidence": 0.5,
                "key_factors": ["data analysis incomplete"],
                "raw_response": response,  # 保留原始LLM响应
                "is_natural_language": True
            }
            
    @observe()
    async def coordinate_agents(
        self,
        event_data: Dict[str, Any],
        available_agents: List[str]
    ) -> Dict[str, Any]:
        """Coordinate multi-agent response to disaster event."""
        
        system_prompt = """You are the Disaster Response Coordinator. Your role is to:
1.  Assess the situation based on incoming data
2.  Assign specific tasks to available agents
3.  Set priorities and timelines
4.  Coordinate communication between agents
5.  Monitor overall response effectiveness

Available agent types: disaster_expert, monitor, responder, analyst

Respond with a coordination plan in JSON format including:
- situation_assessment
- agent_assignments (agent_type: [list of tasks])
- priorities (1-5 scale)
- timeline
- communication_protocol"""
        
        user_prompt = f"""Coordinate response for this event:
Event Data: {json.dumps(event_data, default=str)}
Available Agents: {available_agents}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.generate_response(
            messages=messages,
            agent_role="coordinator",
            temperature=0.4
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback coordination plan
            return {
                "situation_assessment": "Event requires immediate attention",
                "agent_assignments": {
                    "disaster_expert": ["analyze data", "predict evolution"],
                    "monitor": ["track conditions", "update status"],
                    "responder": ["prepare resources", "coordinate evacuation"],
                    "analyst": ["assess damage", "report findings"]
                },
                "priorities": [3, 4, 5, 2],
                "timeline": "immediate response required",
                "communication_protocol": "hourly updates"
            }
            
    @observe()
    async def process_multimodal_input(
        self,
        input_data: Dict[str, Any],
        input_type: str
    ) -> Dict[str, Any]:
        """Process multi-modal input and extract relevant information."""
        
        system_prompt = f"""You are a multi-modal data processor specialized in disaster monitoring.
Process the {input_type} input and extract:
1.  Disaster indicators
2.  Geographic information
3.  Severity indicators
4.  Temporal patterns
5.  Actionable insights

Respond in JSON format."""
        
        user_prompt = f"Process this {input_type} data: {json.dumps(input_data, default=str)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.generate_response(
            messages=messages,
            agent_role="multimodal_processor",
            temperature=0.5
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "disaster_indicators": [],
                "geographic_info": "unknown",
                "severity": "unknown",
                "temporal_patterns": [],
                "insights": ["requires further analysis"]
            }

# Global LLM client instance
llm_client = LLMClient()