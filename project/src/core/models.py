"""Data models for the emergency management platform."""
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class DisasterType(Enum):
    """Disaster types supported by the platform."""
    WILDFIRE = "wildfire"
    FIRE = "fire"  # 添加FIRE类型，与WILDFIRE区分
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    HURRICANE = "hurricane"
    TYPHOON = "typhoon"  # 添加台风类型
    LANDSLIDE = "landslide"  # 添加滑坡类型
    VOLCANO = "volcano"  # 添加火山类型
    TSUNAMI = "tsunami"  # 添加海啸类型
    DROUGHT = "drought"  # 添加干旱类型
    STORM = "storm"  # 添加风暴类型
    OTHER = "other"  # 添加其他类型

class AlertLevel(Enum):
    """Alert levels for disaster warnings."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class AgentRole(Enum):
    """Agent roles in the multi-agent system."""
    COORDINATOR = "coordinator"
    DISASTER_EXPERT = "disaster_expert"
    MONITOR = "monitor"
    RESPONDER = "responder"
    ANALYST = "analyst"

@dataclass
class Location:
    """Geographic location data."""
    latitude: float
    longitude: float
    region: str
    country: str = "Unknown"
    elevation: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "region": self.region,
            "country": self.country,
            "elevation": self.elevation
        }

@dataclass
class SensorData:
    """Sensor data for disaster monitoring."""
    sensor_id: str
    sensor_type: str
    location: Location
    timestamp: datetime
    readings: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "location": self.location.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "readings": self.readings,
            "metadata": self.metadata
        }

@dataclass
class DisasterEvent:
    """Disaster event data structure."""
    event_id: str
    disaster_type: DisasterType
    location: Location
    start_time: datetime
    alert_level: AlertLevel
    description: str
    affected_area: float  # in square kilometers
    estimated_population: int
    confidence_score: float
    model_predictions: Dict[str, Any] = field(default_factory=dict)
    sensor_data: List[SensorData] = field(default_factory=list)
    response_actions: List[str] = field(default_factory=list)
    damage_assessment: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "disaster_type": self.disaster_type.value,
            "location": self.location.to_dict(),
            "start_time": self.start_time.isoformat(),
            "alert_level": self.alert_level.value,
            "description": self.description,
            "affected_area": self.affected_area,
            "estimated_population": self.estimated_population,
            "confidence_score": self.confidence_score,
            "model_predictions": self.model_predictions,
            "sensor_data": [data.to_dict() for data in self.sensor_data],
            "response_actions": self.response_actions,
            "damage_assessment": self.damage_assessment
        }

@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    sender_id: str
    receiver_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 5=critical
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority
        }

@dataclass
class MultiModalInput:
    """Multi-modal input data structure."""
    input_id: str
    input_type: str  # "text", "image", "sensor", "weather", "satellite"
    content: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: datetime
    location: Optional[Location] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_id": self.input_id,
            "input_type": self.input_type,
            "content": self.content if isinstance(self.content, (str, dict)) else "<binary_data>",
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "location": self.location.to_dict() if self.location else None
        }

@dataclass
class ModelResult:
    """Result from disaster prediction models."""
    model_name: str
    disaster_type: DisasterType
    prediction: Dict[str, Any]
    confidence: float
    processing_time: float
    timestamp: datetime
    input_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "disaster_type": self.disaster_type.value,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat(),
            "input_data": self.input_data
        }