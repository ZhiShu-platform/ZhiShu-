#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言处理器 - 支持一般性的自然语言对话
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .llm import llm_client


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: str
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    last_interaction: datetime
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加消息到对话历史"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        self.last_interaction = datetime.now()


class NaturalLanguageHandler:
    """自然语言处理器"""
    
    def __init__(self):
        self.llm_client = llm_client
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        
        # 对话意图分类器
        self.intent_patterns = {
            "greeting": [r"你好|hello|hi|hey|早上好|下午好|晚上好|您好"],
            "question": [r"什么是|怎么|如何|为什么|什么时候|哪里|谁"],
            "emergency": [r"火灾|地震|洪水|台风|暴雨|紧急|危险|救援"],
            "casual_chat": [r"聊天|闲聊|聊聊|说说|谈谈"]
        }
    
    def classify_intent(self, text: str) -> Tuple[str, float]:
        """分类用户意图"""
        text_lower = text.lower()
        best_intent = "casual_chat"
        best_score = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1.0
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        return best_intent, best_score
    
    async def process_natural_language(
        self, 
        text: str, 
        session_id: str, 
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理自然语言输入"""
        
        # 获取或创建对话上下文
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                conversation_history=[],
                user_preferences={},
                last_interaction=datetime.now()
            )
        
        conv_context = self.conversation_contexts[session_id]
        
        # 添加用户消息到历史
        conv_context.add_message("user", text, context)
        
        # 分类意图
        intent, confidence = self.classify_intent(text)
        
        # 生成响应
        response = await self._generate_response(text, intent, conv_context, context)
        
        # 添加助手响应到历史
        conv_context.add_message("assistant", response["content"], {
            "intent": intent,
            "confidence": confidence,
            "response_type": response["type"]
        })
        
        return {
            "content": response["content"],
            "intent": intent,
            "confidence": confidence,
            "response_type": response["type"],
            "type": response["type"],  # 添加type字段以保持兼容性
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "conversation_length": len(conv_context.conversation_history)
        }
    
    async def _generate_response(
        self, 
        text: str, 
        intent: str, 
        conv_context: ConversationContext,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """根据意图生成响应"""
        
        if intent == "greeting":
            return await self._generate_greeting_response(conv_context)
        elif intent == "question":
            return await self._generate_question_response(text, conv_context)
        elif intent == "emergency":
            return await self._generate_emergency_response(text, conv_context)
        else:
            return await self._generate_casual_response(text, conv_context)
    
    async def _generate_greeting_response(self, conv_context: ConversationContext) -> Dict[str, Any]:
        """生成问候响应"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_greeting = "早上好！"
        elif 12 <= hour < 18:
            time_greeting = "下午好！"
        else:
            time_greeting = "晚上好！"
        
        content = f"{time_greeting} 你好！我是应急管理系统的智能助手，很高兴为您服务。"
        
        return {
            "content": content,
            "type": "greeting"
        }
    
    async def _generate_question_response(
        self, 
        text: str, 
        conv_context: ConversationContext
    ) -> Dict[str, Any]:
        """生成问题响应"""
        
        system_prompt = """你是一个专业的应急管理助手，专门回答用户关于应急管理、安全知识、灾害预防等方面的问题。

请用专业、准确、易懂的语言回答用户问题。如果问题超出你的专业范围，请诚实说明并建议用户咨询相关专业人士。"""
        
        user_prompt = f"用户问题：{text}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.llm_client.generate_response(
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            return {
                "content": response,
                "type": "question_answer"
            }
            
        except Exception as e:
            return {
                "content": f"抱歉，我暂时无法回答您的问题。请稍后再试。",
                "type": "error_fallback"
            }
    
    async def _generate_emergency_response(
        self, 
        text: str, 
        conv_context: ConversationContext
    ) -> Dict[str, Any]:
        """生成紧急情况响应"""
        
        system_prompt = """你是一个专业的应急管理助手，专门处理紧急情况和灾害事件。

当用户报告紧急情况时，请：
1. 保持冷静和专业
2. 快速评估情况严重程度
3. 提供立即的行动建议
4. 提醒用户联系相关应急部门
5. 提供安全指导"""
        
        user_prompt = f"紧急情况报告：{text}\n\n请提供专业的应急建议和指导。"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.llm_client.generate_response(
                messages=messages,
                temperature=0.3,
                max_tokens=600
            )
            
            return {
                "content": response,
                "type": "emergency_guidance"
            }
            
        except Exception as e:
            return {
                "content": "检测到紧急情况！请立即拨打相关紧急电话：\n- 火灾：119\n- 医疗急救：120\n- 报警：110",
                "type": "emergency_fallback"
            }
    
    async def _generate_casual_response(
        self, 
        text: str, 
        conv_context: ConversationContext
    ) -> Dict[str, Any]:
        """生成闲聊响应"""
        
        system_prompt = """你是一个友好的应急管理助手，可以与用户进行轻松的闲聊。

闲聊要求：
1. 保持友好和幽默
2. 适当分享应急管理相关的有趣知识
3. 引导用户了解应急管理的重要性
4. 保持专业但不过于严肃"""
        
        user_prompt = f"用户说：{text}\n\n请用友好的方式回应，可以适当分享一些应急管理的小知识。"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.llm_client.generate_response(
                messages=messages,
                temperature=0.8,
                max_tokens=400
            )
            
            return {
                "content": response,
                "type": "casual_chat"
            }
            
        except Exception as e:
            return {
                "content": "哈哈，和你聊天很开心！应急管理虽然听起来严肃，但其实有很多有趣的知识。你想了解什么吗？",
                "type": "casual_fallback"
            }


# 全局实例
natural_language_handler = NaturalLanguageHandler()
