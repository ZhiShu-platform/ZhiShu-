# -*- coding: utf-8 -*-
"""
Modified graph.py for EmergencyManagementGraph
- UTF-8 clean
- Robust _process_input with validation and non-emergency routing
- Helper functions for safe Langfuse updates and session/user normalization
- Quick skip_workflow checks at the start of each async workflow node (example shown in each node)
- Integrated with new Langfuse integration module

Replace your original graph.py with this file (or copy the EmergencyManagementGraph class into it).
"""
import sys
import os
import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
load_dotenv()

# Import our new Langfuse integration module
from src.core.langfuse_integration import langfuse_manager, get_langfuse_handler

from src.core.models import (
    DisasterEvent, DisasterType, Location, AlertLevel,
    MultiModalInput, SensorData
)
from src.core.llm import llm_client

from src.MCP.client import mcp_client
from src.MCP.sdk import MCPClient, ToolExecutor as MCPToolExecutor
from src.agent.coordinator import disaster_coordinator

# Get Langfuse handler for LangGraph integration
langfuse_handler = get_langfuse_handler()

# Check Langfuse availability
if langfuse_manager.is_available():
    print("✅ Langfuse integration is ready in graph.py!")
else:
    print("⚠️ Langfuse integration not available. Running without tracing.")


class EmergencyManagementGraph:
    def __init__(self):
        self.graph = self._build_graph()
        self.coordinator = disaster_coordinator
        # Configurable threat keywords and thresholds
        self.threat_rules = {
            "wildfire": {"keywords": ["fire", "smoke", "burn", "heat", "flame"], "score": 0.3, "confidence": 0.7},
            "flood": {"keywords": ["flood", "water", "rain", "overflow", "surge"], "score": 0.3, "confidence": 0.8},
            "earthquake": {"keywords": ["earthquake", "seismic", "tremor", "shake", "quake"], "score": 0.4, "confidence": 0.9},
            "hurricane": {"keywords": ["hurricane", "storm", "wind", "cyclone", "typhoon"], "score": 0.3, "confidence": 0.75}
        }
        self.alert_thresholds = [
            (0.8, AlertLevel.CRITICAL),
            (0.6, AlertLevel.HIGH),
            (0.3, AlertLevel.MODERATE),
            (0.0, AlertLevel.LOW)
        ]

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(dict)
        workflow.add_node("input_processing", self._process_input)
        workflow.add_node("threat_detection", self._detect_threats)
        workflow.add_node("alert_generation", self._generate_alerts)
        workflow.add_node("agent_coordination", self._coordinate_agents)
        workflow.add_node("response_execution", self._execute_response)
        workflow.add_node("damage_assessment", self._assess_damage)
        workflow.add_node("reporting", self._generate_reports)
        workflow.add_node("generate_human_readable_summary", self._generate_human_readable_summary)
        workflow.set_entry_point("input_processing")
        workflow.add_edge("input_processing", "threat_detection")
        workflow.add_edge("threat_detection", "alert_generation")
        workflow.add_edge("alert_generation", "agent_coordination")
        workflow.add_edge("agent_coordination", "response_execution")
        workflow.add_edge("response_execution", "damage_assessment")
        workflow.add_edge("damage_assessment", "reporting")
        workflow.add_edge("reporting", "generate_human_readable_summary")
        workflow.add_edge("generate_human_readable_summary", END)
        
        # Use Langfuse handler if available
        config = {}
        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]
        
        return workflow.compile().with_config(config)

    # ---------------------- Helper utilities ----------------------
    def _ensure_session_user(self, input_data: Dict[str, Any]) -> (str, str):
        session_id = input_data.get("session_id") or input_data.get("session") or f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        user_id = input_data.get("user_id") or input_data.get("user", {}).get("id") or input_data.get("userid") or f"anonymous_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return session_id, user_id

    def _ensure_processing_log(self, state: Dict[str, Any]) -> List[str]:
        """确保processing_log字段存在且为列表类型"""
        if "processing_log" not in state:
            state["processing_log"] = []
        elif not isinstance(state["processing_log"], list):
            state["processing_log"] = [str(state["processing_log"])]
        return state["processing_log"]

    def _safe_langfuse_update_trace(self, session_id: str, user_id: str, metadata: Dict[str, Any]):
        """Safely update Langfuse trace using our new integration module."""
        try:
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                langfuse_manager.update_trace(self._current_trace_id, metadata)
        except Exception:
            # Never fail the main flow because of tracing
            pass

    def _collect_threat_keywords(self) -> List[str]:
        kws = []
        for rule in getattr(self, 'threat_rules', {}).values():
            kws.extend(rule.get('keywords', []))
        return list({k.lower() for k in kws if isinstance(k, str)})

    def _should_skip(self, state: Dict[str, Any]) -> bool:
        """Determine whether the remaining workflow should be skipped for this session."""
        # explicit skip flag OR non-emergency classification
        return bool(state.get('skip_workflow') or state.get('is_non_emergency'))

    def _mark_non_emergency(self, state: Dict[str, Any], note: Optional[str] = None):
        state['is_non_emergency'] = True
        state['processing_log'] = state.get('processing_log', [])
        msg = note or "Classified as non-emergency by heuristic checks."
        state['processing_log'].append(msg)

    # ---------------------- Core async workflow nodes ----------------------
    async def _process_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Robust input processing with Langfuse tracing:
        - Normalize fields and fill defaults to avoid 422
        - Lightweight non-emergency detection and early return
        - Defensive LLM preprocessing (fallback to heuristics on failure)
        - Complete Langfuse tracing integration
        """
        start_time = datetime.now()
        input_data = state.get('input_data') or state.get('input') or {}
        session_id, user_id = self._ensure_session_user(input_data)

        # Create Langfuse trace for this workflow execution
        if langfuse_manager.is_available():
            try:
                trace = langfuse_manager.create_trace(
                    name="emergency_management_workflow",
                    session_id=session_id,
                    user_id=user_id,
                    metadata={
                        "workflow_type": "emergency_management",
                        "start_time": start_time.isoformat(),
                        "input_type": input_data.get('type', 'user_prompt')
                    }
                )
                if trace:
                    self._current_trace_id = trace.id
                    state['langfuse_trace_id'] = trace.id
                    print(f"🔍 Langfuse trace created: {trace.id}")
            except Exception as e:
                print(f"⚠️ Failed to create Langfuse trace: {e}")
                self._current_trace_id = None

        # content normalization
        content = input_data.get('content')
        if content is None:
            possible_text = input_data.get('prompt') or input_data.get('text') or input_data.get('message') or ""
            if isinstance(possible_text, str):
                content = {'prompt': possible_text}
            else:
                content = possible_text or {}

        # location normalization
        location = {}
        lat = input_data.get('latitude') or input_data.get('lat')
        lon = input_data.get('longitude') or input_data.get('lon')
        if lat is not None and lon is not None:
            try:
                location = {'latitude': float(lat), 'longitude': float(lon), 'region': input_data.get('region') or input_data.get('area') or 'Unknown'}
            except Exception:
                location = {'region': input_data.get('region') or 'Unknown'}
        else:
            meta_loc = input_data.get('location') or (input_data.get('metadata') or {}).get('location')
            if isinstance(meta_loc, dict):
                location = meta_loc
            else:
                location = {'region': input_data.get('region') or 'Unknown'}

        # put normalized fields into state early
        state['session_id'] = session_id
        state['user_id'] = user_id
        state['selected_region'] = input_data.get('region') or location.get('region', 'Unknown')
        state['selected_model_choice'] = input_data.get('model', {}) or {}
        state['selected_datasets'] = input_data.get('datasets', []) or []

        # Build MultiModalInput defensively
        try:
            multi_input = MultiModalInput(
                input_id=f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                input_type=input_data.get('type', 'user_prompt'),
                content=content,
                metadata=input_data.get('metadata', {}) or {},
                timestamp=datetime.now(),
                location=Location(
                    latitude=location.get('latitude') if 'latitude' in location else None,
                    longitude=location.get('longitude') if 'longitude' in location else None,
                    region=location.get('region', 'Unknown')
                ) if location and ('latitude' in location or 'region' in location) else None
            )
        except Exception:
            multi_input = None

        # heuristics for non-emergency / casual chat
        text_to_check = ''
        if isinstance(content, dict):
            text_to_check = (content.get('prompt') or content.get('text') or content.get('message') or '').strip()
        elif isinstance(content, str):
            text_to_check = content.strip()
        else:
            try:
                text_to_check = str(content)[:1024].strip()
            except Exception:
                text_to_check = ''

        text_lower = text_to_check.lower() if isinstance(text_to_check, str) else ''
        threat_keywords = self._collect_threat_keywords()
        contains_threat_kw = any(kw in text_lower for kw in threat_keywords if kw)
        is_greeting = text_lower in {"你好", "您好", "hi", "hello", "hey"} or re.fullmatch(r"\d+", text_lower)

        # early non-emergency classification
        if (is_greeting or len(text_lower) <= 3) and not contains_threat_kw:
            processing_log = self._ensure_processing_log(state)
            processing_log.append(f"? Input classified as non-emergency (greeting/short) - Session: {session_id}")
            state['processed_input'] = {'disaster_indicators': [], 'raw_text': text_to_check}
            state['multi_input'] = multi_input
            self._mark_non_emergency(state, note="Non-emergency detected in _process_input")
            
            # Log non-emergency classification to Langfuse
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                try:
                    langfuse_manager.log_span(
                        trace_id=self._current_trace_id,
                        name="input_processing",
                        input=input_data,
                        output={"classification": "non_emergency", "reason": "greeting_or_short"},
                        metadata={"processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)}
                    )
                except Exception:
                    pass
            
            return await self._handle_non_emergency_input(state)

        # try LLM preprocessing defensively
        processed_data = {}
        try:
            if multi_input is not None and getattr(llm_client, 'process_multimodal_input', None):
                try:
                    processed_data = await llm_client.process_multimodal_input(multi_input.to_dict(), multi_input.input_type)
                except Exception as e:
                    processed_data = {'disaster_indicators': [], 'nlp_error': str(e), 'raw_text': text_to_check}
            else:
                indicators = []
                if contains_threat_kw:
                    indicators = [kw for kw in threat_keywords if kw in text_lower]
                processed_data = {'disaster_indicators': indicators, 'raw_text': text_to_check}
        except Exception as e:
            processed_data = {'disaster_indicators': [], 'raw_text': text_to_check, 'processing_exception': str(e)}

        if not isinstance(processed_data, dict):
            processed_data = {'disaster_indicators': [], 'raw_text': text_to_check}

        effective_indicators = processed_data.get('disaster_indicators', []) or []
        # if no indicators and no threat keywords, treat as non-emergency
        if not effective_indicators and not contains_threat_kw:
            processing_log = self._ensure_processing_log(state)
            processing_log.append(f"? No disaster indicators found; routing to non-emergency handler - Session: {session_id}")
            state['processed_input'] = processed_data
            state['multi_input'] = multi_input
            self._mark_non_emergency(state, note="No indicators found after preprocessing")
            
            # Log non-emergency classification to Langfuse
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                try:
                    langfuse_manager.log_span(
                        trace_id=self._current_trace_id,
                        name="input_processing",
                        input=input_data,
                        output={"classification": "non_emergency", "reason": "no_indicators"},
                        metadata={"processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)}
                    )
                except Exception:
                    pass
            
            return await self._handle_non_emergency_input(state)

        # regular path - emergency detected
        state['processed_input'] = processed_data
        state['multi_input'] = multi_input
        processing_log = self._ensure_processing_log(state)
        processing_log.append(
            f"? Input processed - Session: {session_id}, User: {user_id or 'Anonymous'} (Time: {datetime.now().strftime('%H:%M:%S')})"
        )
        
        # Log successful emergency input processing to Langfuse
        if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
            try:
                langfuse_manager.log_span(
                    trace_id=self._current_trace_id,
                    name="input_processing",
                    input=input_data,
                    output={
                        "classification": "emergency",
                        "disaster_indicators": effective_indicators,
                        "location": location,
                        "processed_input": processed_data
                    },
                    metadata={
                        "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                        "threat_keywords_found": len(effective_indicators)
                    }
                )
            except Exception:
                pass
        
        return state

    async def _detect_threats(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect threats with Langfuse tracing."""
        start_time = datetime.now()
        
        # QUICK SKIP CHECK: if session has been classified as non-emergency or explicitly requested to skip, exit early
        if self._should_skip(state):
            processing_log = self._ensure_processing_log(state)
            processing_log.append("? Skipping threat detection due to skip flag / non-emergency")
            # keep minimal threat_detection so downstream code can assume the key exists
            state['threat_detection'] = {"threat_score": 0.0, "detected_threats": [], "alert_level": AlertLevel.LOW, "detection_timestamp": datetime.now().isoformat()}
            
            # Log skip to Langfuse
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                try:
                    langfuse_manager.log_span(
                        trace_id=self._current_trace_id,
                        name="threat_detection",
                        input={"skip_reason": "non_emergency_or_skip_flag"},
                        output={"status": "skipped", "threat_score": 0.0},
                        metadata={"processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)}
                    )
                except Exception:
                    pass
            
            return state

        processed_input = state.get('processed_input', {})
        multi_input = state.get('multi_input')
        disaster_indicators = processed_input.get('disaster_indicators', [])
        threat_score = 0.0
        detected_threats = []
        
        for indicator in disaster_indicators:
            indicator_lower = indicator.lower()
            for dtype, rule in self.threat_rules.items():
                if any(kw in indicator_lower for kw in rule['keywords']):
                    threat_score += rule['score']
                    detected_threats.append({
                        'type': dtype,
                        'indicator': indicator,
                        'confidence': rule['confidence']
                    })
        
        for threshold, level in self.alert_thresholds:
            if threat_score >= threshold:
                alert_level = level
                break
        else:
            alert_level = AlertLevel.LOW
            
        state['threat_detection'] = {
            'threat_score': threat_score,
            'detected_threats': detected_threats,
            'alert_level': alert_level,
            'detection_timestamp': datetime.now().isoformat()
        }
        
        processing_log = self._ensure_processing_log(state)
        processing_log.append(f"Threats detected: {len(detected_threats)} (score: {threat_score:.2f})")
        
        # Log threat detection to Langfuse
        if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
            try:
                langfuse_manager.log_span(
                    trace_id=self._current_trace_id,
                    name="threat_detection",
                    input={
                        "disaster_indicators": disaster_indicators,
                        "processed_input": processed_input
                    },
                    output={
                        "threat_score": threat_score,
                        "detected_threats": detected_threats,
                        "alert_level": alert_level.value,
                        "threat_rules_applied": len(self.threat_rules)
                    },
                    metadata={
                        "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                        "indicators_processed": len(disaster_indicators)
                    }
                )
            except Exception:
                pass
        
        return state

    async def _generate_alerts(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if self._should_skip(state):
            processing_log = self._ensure_processing_log(state)
            processing_log.append("? Skipping alert generation due to skip flag / non-emergency")
            state['alerts'] = []
            return state

        threat_detection = state.get('threat_detection', {})
        multi_input = state.get('multi_input')
        detected_threats = threat_detection.get('detected_threats', [])
        alert_level = threat_detection.get('alert_level', AlertLevel.LOW)
        alerts = []
        for threat in detected_threats:
            if threat.get('confidence', 0) > 0.5:
                event_id = f"alert_{threat['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                alert = {
                    'alert_id': event_id,
                    'disaster_type': threat['type'],
                    'alert_level': alert_level.value,
                    'confidence': threat['confidence'],
                    'location': multi_input.location.to_dict() if multi_input and multi_input.location else {},
                    'description': f"Potential {threat['type']} detected: {threat['indicator']}",
                    'timestamp': datetime.now().isoformat(),
                    'requires_immediate_response': alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL],
                    'estimated_impact': self._estimate_impact(threat, alert_level)
                }
                alerts.append(alert)
        state['alerts'] = alerts
        state['processing_log'].append(f"Generated {len(alerts)} alerts")
        return state

    async def _coordinate_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if self._should_skip(state):
            state['processing_log'] = state.get('processing_log', []) + ["? Skipping agent coordination due to skip flag / non-emergency"]
            state['coordination_results'] = []
            return state

        alerts = state.get('alerts', [])
        coordination_results = []
        for alert in alerts:
            if alert.get('requires_immediate_response', False):
                coordination_input = {
                    'type': 'alert',
                    'alert_data': alert,
                    'location': alert.get('location', {}),
                    'severity': alert.get('alert_level', 'moderate')
                }
                try:
                    coordination_result = await self.coordinator.process_disaster_alert(coordination_input)
                    coordination_results.append(coordination_result)
                except Exception as e:
                    coordination_results.append({'error': str(e), 'alert_id': alert.get('alert_id', 'unknown')})
        state['coordination_results'] = coordination_results
        state['processing_log'].append(f"Coordinated response for {len(coordination_results)} critical alerts")
        return state

    async def _execute_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if self._should_skip(state):
            state['processing_log'] = state.get('processing_log', []) + ["? Skipping response execution due to skip flag / non-emergency"]
            state['response_execution'] = []
            return state

        coordination_results = state.get('coordination_results', [])
        response_execution = []
        for result in coordination_results:
            if 'final_report' in result:
                final_report = result['final_report']
                coordination_summary = final_report.get('coordination_summary', {})
                execution_result = {
                    'event_id': coordination_summary.get('event_id', 'unknown'),
                    'execution_timestamp': datetime.now().isoformat(),
                    'deployed_resources': result.get('resource_allocation', {}),
                    'response_teams': coordination_summary.get('activated_experts', []),
                    'execution_status': 'in_progress',
                    'estimated_completion': '4-6 hours',
                    'success_probability': final_report.get('success_probability', 0.7)
                }
                response_execution.append(execution_result)
        state['response_execution'] = response_execution
        state['processing_log'].append(f"Initiated response execution for {len(response_execution)} events")
        return state

    async def _assess_damage(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if self._should_skip(state):
            state['processing_log'] = state.get('processing_log', []) + ["? Skipping damage assessment due to skip flag / non-emergency"]
            state['damage_assessments'] = []
            state['mcp_calls_summary'] = []
            return state

        coordination_results = state.get('coordination_results', [])
        threat_detection = state.get('threat_detection', {})
        session_id = state.get('session_id', 'unknown')
        damage_assessments = []
        mcp_calls_summary = []
        executor = MCPToolExecutor(mcp_client)
        for result in coordination_results:
            if 'disaster_event' in result:
                disaster_event_data = result['disaster_event']
                location_data = disaster_event_data.get('location', {})
                disaster_type_str = disaster_event_data.get('disaster_type', 'wildfire')
                event_id = disaster_event_data.get('event_id', 'unknown')
                try:
                    assessment_tasks = []
                    task_types = []
                    call_descriptions = []
                    if disaster_type_str.lower() in ['hurricane', 'wildfire', 'earthquake', 'flood']:
                        try:
                            # Log CLIMADA MCP call start to Langfuse
                            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                                langfuse_manager.log_span(
                                    trace_id=self._current_trace_id,
                                    name="mcp_climada_start",
                                    input={
                                        "hazard_type": disaster_type_str,
                                        "region": location_data.get('region', 'Unknown'),
                                        "year_range": [2020, 2024]
                                    },
                                    metadata={"mcp_server": "climada", "call_type": "impact_assessment"}
                                )
                        except Exception:
                            pass
                        
                        assessment_tasks.append(executor.run_climada_impact_assessment(
                            hazard_type=disaster_type_str.lower(),
                            region=location_data.get('region', 'Unknown'),
                            year_range=[2020, 2024]
                        ))
                        task_types.append('climada_impact')
                        call_descriptions.append(f"CLIMADA impact assessment model - Disaster type: {disaster_type_str}, Region: {location_data.get('region', 'Unknown')}")
                        
                        if 'country_iso' in location_data:
                            assessment_tasks.append(executor.run_climada_exposure_analysis(
                                country_iso=location_data['country_iso'],
                                exposure_type='litpop'
                            ))
                            task_types.append('climada_exposure')
                            call_descriptions.append(f"CLIMADA exposure analysis model - Country: {location_data['country_iso']}")
                    
                    if disaster_type_str.lower() in ['flood', 'hurricane', 'storm']:
                        try:
                            # Log LISFLOOD MCP call start to Langfuse
                            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                                langfuse_manager.log_span(
                                    trace_id=self._current_trace_id,
                                    name="mcp_lisflood_start",
                                    input={
                                        "start_date": '2024-01-01',
                                        "end_date": '2024-12-31',
                                        "region": location_data.get('region', 'default'),
                                        "event_id": event_id
                                    },
                                    metadata={"mcp_server": "lisflood", "call_type": "flood_simulation"}
                                )
                        except Exception:
                            pass
                        
                        assessment_tasks.append(executor.run_lisflood_simulation(
                            start_date='2024-01-01',
                            end_date='2024-12-31',
                            settings_file=f"config/{location_data.get('region', 'default')}_settings.xml",
                            output_dir=f"./damage_assessment/{event_id}"
                        ))
                        task_types.append('lisflood_simulation')
                        call_descriptions.append(f"LISFLOOD flood simulation model - Region: {location_data.get('region', 'default')}")
                    
                    if assessment_tasks:
                        start_time = datetime.now()
                        assessment_results = await asyncio.gather(*assessment_tasks, return_exceptions=True)
                        end_time = datetime.now()
                        total_duration = (end_time - start_time).total_seconds() * 1000
                        
                        damage_assessment = {
                            'event_id': event_id,
                            'disaster_type': disaster_type_str,
                            'location': location_data,
                            'assessment_timestamp': datetime.now().isoformat(),
                            'models_used': [],
                            'results': {},
                            'mcp_calls_made': call_descriptions,
                            'total_duration_ms': int(total_duration)
                        }
                        
                        successful_calls = 0
                        for i, res in enumerate(assessment_results):
                            model_type = task_types[i] if i < len(task_types) else f'assessment_{i}'
                            if isinstance(res, Exception):
                                damage_assessment['results'][model_type] = {'error': str(res), 'status': 'failed', 'model': call_descriptions[i] if i < len(call_descriptions) else 'unknown'}
                                
                                # Log failed MCP call to Langfuse
                                if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                                    try:
                                        langfuse_manager.log_mcp_call(
                                            trace_id=self._current_trace_id,
                                            mcp_server=model_type.split('_')[0],
                                            tool_name=model_type,
                                            input_params={"event_id": event_id, "disaster_type": disaster_type_str},
                                            output_result={"error": str(res), "status": "failed"},
                                            success=False
                                        )
                                    except Exception:
                                        pass
                            else:
                                successful_calls += 1
                                damage_assessment['models_used'].append(model_type)
                                damage_assessment['results'][model_type] = res
                                
                                # Log successful MCP call to Langfuse
                                if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                                    try:
                                        langfuse_manager.log_mcp_call(
                                            trace_id=self._current_trace_id,
                                            mcp_server=model_type.split('_')[0],
                                            tool_name=model_type,
                                            input_params={"event_id": event_id, "disaster_type": disaster_type_str},
                                            output_result=res,
                                            success=True
                                        )
                                    except Exception:
                                        pass
                        
                        damage_assessment['summary'] = self._generate_damage_summary(damage_assessment['results'], disaster_type_str)
                        mcp_calls_summary.append({
                            'event_id': event_id,
                            'total_calls': len(assessment_tasks),
                            'successful_calls': successful_calls,
                            'models': call_descriptions,
                            'duration_ms': int(total_duration)
                        })
                        
                        # Log overall damage assessment completion to Langfuse
                        if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                            try:
                                langfuse_manager.log_span(
                                    trace_id=self._current_trace_id,
                                    name="damage_assessment_complete",
                                    input={
                                        "event_id": event_id,
                                        "disaster_type": disaster_type_str,
                                        "total_mcp_calls": len(assessment_tasks)
                                    },
                                    output={
                                        "successful_calls": successful_calls,
                                        "failed_calls": len(assessment_tasks) - successful_calls,
                                        "summary": damage_assessment['summary']
                                    },
                                    metadata={
                                        "total_duration_ms": int(total_duration),
                                        "success_rate": successful_calls / len(assessment_tasks) if assessment_tasks else 0
                                    }
                                )
                            except Exception:
                                pass
                        
                        damage_assessments.append(damage_assessment)
                    else:
                        damage_assessments.append({'event_id': event_id, 'disaster_type': disaster_type_str, 'error': 'No applicable damage assessment models for this disaster type', 'status': 'skipped'})
                except Exception as e:
                    damage_assessments.append({'event_id': event_id, 'disaster_type': disaster_type_str, 'error': str(e), 'status': 'failed'})
        state['damage_assessments'] = damage_assessments
        state['mcp_calls_summary'] = mcp_calls_summary
        total_mcp_calls = sum(call.get('total_calls') for call in mcp_calls_summary)
        successful_mcp_calls = sum(call.get('successful_calls') for call in mcp_calls_summary)
        state['processing_log'].append(
            f"?? Damage assessment completed - {total_mcp_calls} external model calls, {successful_mcp_calls} successful (assessed {len(damage_assessments)} events)"
        )
        return state

    def _generate_damage_summary(self, results: Dict[str, Any], disaster_type: str) -> Dict[str, Any]:
        summary = {"total_economic_damage": 0, "affected_population": 0, "risk_level": "unknown", "confidence": 0.0}
        try:
            if 'climada_impact' in results:
                climada_data = results['climada_impact'].get('data', {})
                if 'economic_damage' in climada_data:
                    summary['total_economic_damage'] = climada_data['economic_damage']
                if 'affected_population' in climada_data:
                    summary['affected_population'] = climada_data['affected_population']
                if 'confidence' in climada_data:
                    summary['confidence'] = max(summary['confidence'], climada_data['confidence'])
            if 'lisflood_simulation' in results:
                lisflood_data = results['lisflood_simulation'].get('data', {})
                if 'max_water_depth' in lisflood_data:
                    depth = lisflood_data['max_water_depth']
                    if depth > 2.0:
                        summary['risk_level'] = 'high'
                    elif depth > 1.0:
                        summary['risk_level'] = 'medium'
                    else:
                        summary['risk_level'] = 'low'
            if summary['total_economic_damage'] > 5000000:
                summary['risk_level'] = 'critical'
            elif summary['total_economic_damage'] > 1000000:
                summary['risk_level'] = 'high'
            elif summary['total_economic_damage'] > 100000:
                summary['risk_level'] = 'medium'
            else:
                summary['risk_level'] = 'low'
        except Exception as e:
            summary['error'] = f"Failed to generate summary: {str(e)}"
        return summary

    async def _generate_reports(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if self._should_skip(state):
            state['processing_log'] = state.get('processing_log', []) + ["? Skipping intermediate report generation due to skip flag / non-emergency"]
            # If there is already a final_report from non-emergency path, keep it. Otherwise build minimal report.
            if not state.get('final_report'):
                state['final_report'] = {
                    'report_id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'report_timestamp': datetime.now().isoformat(),
                    'processing_summary': {
                        'input_processed': bool(state.get('processed_input')),
                        'threats_detected': len(state.get('threat_detection', {}).get('detected_threats', [])),
                        'alerts_generated': len(state.get('alerts', [])),
                        'coordination_executed': len(state.get('coordination_results', [])),
                        'response_initiated': len(state.get('response_execution', [])),
                        'damage_assessed': len(state.get('damage_assessments', []))
                    },
                    'alerts': state.get('alerts', []),
                    'coordination_results': state.get('coordination_results', []),
                    'response_execution': state.get('response_execution', []),
                    'damage_assessments': state.get('damage_assessments', []),
                    'processing_log': state.get('processing_log', []),
                    'system_status': 'operational',
                    'recommendations': ['No action required for non-emergency input']
                }
            return state

        final_report = {
            'report_id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'report_timestamp': datetime.now().isoformat(),
            'processing_summary': {
                'input_processed': bool(state.get('processed_input')),
                'threats_detected': len(state.get('threat_detection', {}).get('detected_threats', [])),
                'alerts_generated': len(state.get('alerts', [])),
                'coordination_executed': len(state.get('coordination_results', [])),
                'response_initiated': len(state.get('response_execution', [])),
                'damage_assessed': len(state.get('damage_assessments', []))
            },
            'alerts': state.get('alerts', []),
            'coordination_results': state.get('coordination_results', []),
            'response_execution': state.get('response_execution', []),
            'damage_assessments': state.get('damage_assessments', []),
            'processing_log': state.get('processing_log', []),
            'system_status': 'operational',
            'recommendations': [
                'Continue monitoring situation',
                'Maintain resource readiness',
                'Update stakeholders',
                'Prepare for potential escalation'
            ]
        }
        state['final_report'] = final_report
        state['processing_log'].append('Final report generated')
        return state

    async def _handle_non_emergency_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state['is_non_emergency'] = True
        state['final_report'] = {
            'report_id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'report_timestamp': datetime.now().isoformat(),
            'processing_summary': {
                'input_processed': True,
                'threats_detected': 0,
                'alerts_generated': 0
            },
            'alerts': [],
            'note': 'δ��⵽������в����ǰ�����ƺ����ǽ����¼���'
        }
        state['human_readable_summary'] = state['final_report']['note']
        state['processing_log'] = state.get('processing_log', []) + ['Non-emergency input handled.']
        return state

    async def _generate_human_readable_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate human readable summary with complete Langfuse tracing."""
        start_time = datetime.now()
        
        # if skip, just return existing final report's note or build a short summary
        if self._should_skip(state):
            state['processing_log'] = state.get('processing_log', []) + ["? Skipping long summary generation due to skip flag / non-emergency"]
            if not state.get('human_readable_summary'):
                state['human_readable_summary'] = state.get('final_report', {}).get('note', 'No summary generated for non-emergency input.')
            
            # Log skip to Langfuse
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                try:
                    langfuse_manager.log_span(
                        trace_id=self._current_trace_id,
                        name="summary_generation",
                        input={"skip_reason": "non_emergency_or_skip_flag"},
                        output={"status": "skipped", "summary": state.get('human_readable_summary')},
                        metadata={"processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)}
                    )
                except Exception:
                    pass
            
            return state

        final_report = state.get('final_report')
        processing_log = state.get('processing_log', [])
        mcp_calls_summary = state.get('mcp_calls_summary', [])
        session_id = state.get('session_id', 'unknown')
        user_id = state.get('user_id')
        
        if not final_report:
            state['human_readable_summary'] = "Sorry, system processing failed, unable to generate report."
            
            # Log error to Langfuse
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                try:
                    langfuse_manager.log_span(
                        trace_id=self._current_trace_id,
                        name="summary_generation",
                        input={"final_report": final_report},
                        output={"error": "No final report available"},
                        metadata={"processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)}
                    )
                except Exception:
                    pass
            
            return state

        summary_data = {
            'processing_summary': final_report.get('processing_summary', {}),
            'alerts': final_report.get('alerts', []),
            'recommendations': final_report.get('recommendations', []),
            'processing_log': processing_log[-10:],
            'mcp_calls_summary': mcp_calls_summary[-5:],
            'session_id': session_id,
            'user_id': user_id
        }
        summary_json = json.dumps(summary_data, ensure_ascii=False, indent=2)
        if len(summary_json) > 3000:
            summary_json = summary_json[:3000] + '... (content truncated)'

        try:
            prompt_template = None
            try:
                prompt = langfuse_manager.get_prompt('emergency_summary_detailed', label='production')
                compiled_prompt = prompt.compile(
                    report_data=f"""```json\n{summary_json}\n```""",
                    session_id=session_id,
                    user_id=user_id or 'Anonymous',
                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    processing_steps=len(processing_log),
                    mcp_calls=sum(call.get('total_calls', 0) for call in mcp_calls_summary),
                    successful_mcp=sum(call.get('successful_calls', 0) for call in mcp_calls_summary)
                )
                prompt_template = compiled_prompt
                
                # Log prompt usage to Langfuse
                if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                    try:
                        langfuse_manager.log_span(
                            trace_id=self._current_trace_id,
                            name="prompt_retrieval",
                            input={"prompt_name": "emergency_summary_detailed"},
                            output={"prompt_retrieved": True},
                            metadata={"prompt_name": "emergency_summary_detailed"}
                        )
                    except Exception:
                        pass
                        
            except Exception as e:
                prompt_template = f"You are a professional emergency management AI assistant. Summary data:\n{summary_json}"
                
                # Log prompt fallback to Langfuse
                if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                    try:
                        langfuse_manager.log_span(
                            trace_id=self._current_trace_id,
                            name="prompt_retrieval",
                            input={"prompt_name": "emergency_summary_detailed"},
                            output={"prompt_retrieved": False, "fallback_used": True},
                            metadata={"error": str(e)}
                        )
                    except Exception:
                        pass

            messages = [{"role": "user", "content": prompt_template}]
            summary_start = datetime.now()
            summary = await llm_client.generate_response(messages=messages, temperature=0.3)
            summary_duration = (datetime.now() - summary_start).total_seconds() * 1000
            cleaned_summary = summary.strip()
            
            if len(cleaned_summary) < 50:
                cleaned_summary = self._generate_fallback_summary(summary_data, session_id, user_id)
            
            state['human_readable_summary'] = cleaned_summary
            
            # Log LLM generation to Langfuse
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                try:
                    langfuse_manager.log_generation(
                        trace_id=self._current_trace_id,
                        name="emergency_summary_generation",
                        model="llm_client",
                        prompt=str(prompt_template)[:1000],  # Truncate long prompts
                        completion=cleaned_summary[:1000],   # Truncate long completions
                        metadata={
                            "generation_duration_ms": int(summary_duration),
                            "summary_length": len(cleaned_summary),
                            "prompt_tokens": len(str(prompt_template)),
                            "completion_tokens": len(cleaned_summary)
                        }
                    )
                except Exception:
                    pass
            
            state['processing_log'].append(f"?? Natural language summary generated - Length: {len(cleaned_summary)} chars (Duration: {int(summary_duration)}ms)")
            
        except Exception as e:
            error_summary = self._generate_fallback_summary(summary_data, session_id, user_id)
            state['human_readable_summary'] = error_summary
            state['processing_log'].append(f"?? Natural language summary generation failed, using fallback: {str(e)}")
            
            # Log error to Langfuse
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                try:
                    langfuse_manager.log_span(
                        trace_id=self._current_trace_id,
                        name="summary_generation",
                        input={"summary_data": summary_data},
                        output={"error": str(e), "fallback_used": True},
                        metadata={"processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)}
                    )
                except Exception:
                    pass
        
        # Log final summary generation completion to Langfuse
        if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
            try:
                langfuse_manager.log_span(
                    trace_id=self._current_trace_id,
                    name="summary_generation_complete",
                    input={"final_report": final_report},
                    output={
                        "summary_length": len(state.get('human_readable_summary', '')),
                        "processing_complete": True
                    },
                    metadata={
                        "total_processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                        "workflow_steps_completed": len(processing_log)
                    }
                )
                
                # Flush all events to Langfuse
                langfuse_manager.flush()
                print(f"✅ Langfuse trace completed and flushed: {self._current_trace_id}")
                
            except Exception as e:
                print(f"⚠️ Failed to complete Langfuse trace: {e}")
        
        return state

    def _generate_fallback_summary(self, enhanced_summary: Dict[str, Any], session_id: str, user_id: str = None) -> str:
        processing_summary = enhanced_summary.get('processing_summary', {})
        summary_parts = []
        greeting = f"Hello{f', {user_id}' if user_id else ''}! Your emergency management analysis is complete."
        summary_parts.append(greeting)
        if processing_summary.get('input_processed'):
            summary_parts.append(f"This session ({session_id}) successfully executed {processing_summary.get('input_processed', True) and 1 or 0} analysis steps.")
        threats_detected = processing_summary.get('threats_detected', 0)
        if threats_detected > 0:
            summary_parts.append(f"The system detected {threats_detected} potential threats.")
        alerts_generated = processing_summary.get('alerts_generated', 0)
        if alerts_generated > 0:
            summary_parts.append(f"Based on threat analysis, {alerts_generated} alerts were generated.")
        total_mcp = enhanced_summary.get('processing_details', {}).get('total_mcp_calls', 0)
        successful_mcp = enhanced_summary.get('processing_details', {}).get('successful_mcp_calls', 0)
        if total_mcp > 0:
            summary_parts.append(f"{total_mcp} professional disaster assessment models were called, {successful_mcp} ran successfully.")
        damage_assessed = processing_summary.get('damage_assessed', 0)
        if damage_assessed > 0:
            summary_parts.append(f"Damage assessment completed for {damage_assessed} events.")
        recommendations = enhanced_summary.get('recommendations', [])
        if recommendations:
            summary_parts.append(f"System recommendation: {recommendations[0]}")
        summary_parts.append("All analysis data has been recorded in the tracking system. You can view the detailed report at any time.")
        return " ".join(summary_parts)

    async def process_emergency(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process emergency with complete Langfuse tracing."""
        try:
            # Initialize state with input data
            initial_state = {'input': input_data}
            
            # Execute the workflow
            result = await self.graph.ainvoke(initial_state)
            
            # Ensure final flush to Langfuse
            if langfuse_manager.is_available():
                try:
                    langfuse_manager.flush()
                except Exception as e:
                    print(f"⚠️ Final Langfuse flush failed: {e}")
            
            return result
            
        except Exception as e:
            # Log error to Langfuse if possible
            if langfuse_manager.is_available() and hasattr(self, '_current_trace_id'):
                try:
                    langfuse_manager.log_span(
                        trace_id=self._current_trace_id,
                        name="workflow_error",
                        input={"input_data": input_data},
                        output={"error": str(e)},
                        metadata={"error_type": type(e).__name__, "error": True}
                    )
                    langfuse_manager.flush()
                except Exception:
                    pass
            
            # Re-raise the exception
            raise

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status including Langfuse."""
        try:
            mcp_health = await mcp_client.health_check()
            coordinator_status = await self.coordinator.get_system_status()
            
            # Check Langfuse status
            langfuse_status = {
                "available": langfuse_manager.is_available(),
                "client_ready": langfuse_manager.client is not None if langfuse_manager.is_available() else False,
                "handler_ready": langfuse_manager.handler is not None if langfuse_manager.is_available() else False
            }
            
            return {
                'system_health': {
                    'timestamp': datetime.now().isoformat(),
                    'overall_status': 'healthy',
                    'mcp_connections': mcp_health,
                    'coordinator_status': coordinator_status,
                    'graph_status': 'operational',
                    'langfuse_status': langfuse_status
                }
            }
        except Exception as e:
            return {
                'system_health': {
                    'timestamp': datetime.now().isoformat(),
                    'overall_status': 'degraded',
                    'error': str(e),
                    'langfuse_status': {
                        "available": langfuse_manager.is_available(),
                        "error": "Health check failed"
                    }
                }
            }


# singleton manager to be imported by other modules
_graph_manager = EmergencyManagementGraph()
graph = _graph_manager.graph
async def process_emergency_event(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return await _graph_manager.process_emergency(input_data)
async def get_system_health() -> Dict[str, Any]:
    return await _graph_manager.get_system_health()
