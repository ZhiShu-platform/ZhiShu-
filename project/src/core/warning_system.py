"""Disaster warning and alert system."""
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .models import DisasterEvent, DisasterType, AlertLevel, Location
from .llm import llm_client

class NotificationChannel(Enum):
    """Available notification channels."""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    RADIO = "radio"
    TV = "television"
    SOCIAL_MEDIA = "social_media"
    SIRENS = "sirens"
    MOBILE_ALERT = "mobile_alert"

@dataclass
class Alert:
    """Alert data structure."""
    alert_id: str
    disaster_type: DisasterType
    alert_level: AlertLevel
    location: Location
    title: str
    message: str
    instructions: List[str]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    affected_areas: List[str] = field(default_factory=list)
    estimated_population: int = 0
    channels: List[NotificationChannel] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "disaster_type": self.disaster_type.value,
            "alert_level": self.alert_level.value,
            "location": self.location.to_dict(),
            "title": self.title,
            "message": self.message,
            "instructions": self.instructions,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "affected_areas": self.affected_areas,
            "estimated_population": self.estimated_population,
            "channels": [ch.value for ch in self.channels]
        }

@dataclass
class AlertSubscription:
    """User alert subscription preferences."""
    user_id: str
    location: Location
    disaster_types: List[DisasterType]
    channels: List[NotificationChannel]
    min_alert_level: AlertLevel
    radius_km: float = 50.0  # Alert radius in kilometers
    
class DisasterWarningSystem:
    """Centralized disaster warning and alert system."""
    
    def __init__(self):
        self.active_alerts = {}
        self.alert_history = []
        self.subscriptions = {}
        self.notification_handlers = {}
        
        # Initialize default alert templates
        self.alert_templates = self._initialize_alert_templates()
        
        # Register default notification handlers
        self._register_default_handlers()
    
    def _initialize_alert_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert message templates for different disaster types."""
        
        return {
            DisasterType.WILDFIRE.value: {
                AlertLevel.LOW.value: {
                    "title": "Fire Weather Warning",
                    "message": "Elevated fire danger conditions detected in {location}. Be prepared for potential fire activity.",
                    "instructions": [
                        "Monitor local conditions",
                        "Prepare evacuation kit",
                        "Clear defensible space around property",
                        "Stay informed through official channels"
                    ]
                },
                AlertLevel.MODERATE.value: {
                    "title": "Wildfire Watch",
                    "message": "Wildfire activity detected near {location}. Conditions are favorable for fire spread.",
                    "instructions": [
                        "Be ready to evacuate if necessary",
                        "Keep emergency kit accessible",
                        "Monitor air quality",
                        "Follow local evacuation routes"
                    ]
                },
                AlertLevel.HIGH.value: {
                    "title": "Wildfire Warning",
                    "message": "Active wildfire threatening {location}. Immediate preparation for evacuation required.",
                    "instructions": [
                        "Prepare to evacuate immediately",
                        "Gather essential items and documents",
                        "Close all windows and doors",
                        "Turn off gas utilities",
                        "Follow evacuation orders"
                    ]
                },
                AlertLevel.CRITICAL.value: {
                    "title": "EVACUATION ORDER - WILDFIRE",
                    "message": "IMMEDIATE EVACUATION REQUIRED for {location}. Life-threatening wildfire conditions.",
                    "instructions": [
                        "EVACUATE IMMEDIATELY",
                        "Take only essential items",
                        "Follow designated evacuation routes",
                        "Do not return until all-clear is given",
                        "Seek shelter at designated centers"
                    ]
                }
            },
            DisasterType.FLOOD.value: {
                AlertLevel.LOW.value: {
                    "title": "Flood Watch",
                    "message": "Flooding possible in {location} due to heavy rainfall or rising water levels.",
                    "instructions": [
                        "Monitor weather conditions",
                        "Avoid low-lying areas",
                        "Prepare emergency supplies",
                        "Stay away from storm drains"
                    ]
                },
                AlertLevel.MODERATE.value: {
                    "title": "Flood Advisory",
                    "message": "Minor flooding expected in {location}. Water levels rising.",
                    "instructions": [
                        "Avoid flooded roads",
                        "Move to higher ground if necessary",
                        "Secure loose outdoor items",
                        "Monitor local water levels"
                    ]
                },
                AlertLevel.HIGH.value: {
                    "title": "Flood Warning",
                    "message": "Significant flooding imminent in {location}. Take immediate protective action.",
                    "instructions": [
                        "Move to higher ground immediately",
                        "Avoid walking or driving through flood water",
                        "Prepare for possible evacuation",
                        "Turn off utilities if instructed"
                    ]
                },
                AlertLevel.CRITICAL.value: {
                    "title": "FLASH FLOOD EMERGENCY",
                    "message": "LIFE-THREATENING flooding occurring in {location}. Seek higher ground immediately.",
                    "instructions": [
                        "SEEK HIGHER GROUND IMMEDIATELY",
                        "Do not drive or walk through flood water",
                        "Call for help if trapped",
                        "Stay away from downed power lines",
                        "Follow evacuation orders"
                    ]
                }
            },
            DisasterType.EARTHQUAKE.value: {
                AlertLevel.LOW.value: {
                    "title": "Earthquake Advisory",
                    "message": "Minor earthquake activity detected near {location}. No immediate danger expected.",
                    "instructions": [
                        "Review earthquake safety procedures",
                        "Secure heavy objects",
                        "Check emergency supplies",
                        "Stay informed about aftershocks"
                    ]
                },
                AlertLevel.MODERATE.value: {
                    "title": "Earthquake Alert",
                    "message": "Moderate earthquake occurred near {location}. Aftershocks possible.",
                    "instructions": [
                        "Check for injuries and damage",
                        "Be prepared for aftershocks",
                        "Turn off gas if you smell leaks",
                        "Stay away from damaged buildings"
                    ]
                },
                AlertLevel.HIGH.value: {
                    "title": "Major Earthquake Warning",
                    "message": "Strong earthquake detected in {location}. Significant damage possible.",
                    "instructions": [
                        "Drop, Cover, and Hold On if shaking continues",
                        "Check for injuries and hazards",
                        "Exit damaged buildings carefully",
                        "Expect aftershocks",
                        "Use stairs, not elevators"
                    ]
                },
                AlertLevel.CRITICAL.value: {
                    "title": "MAJOR EARTHQUAKE EMERGENCY",
                    "message": "Severe earthquake in {location}. Widespread damage expected.",
                    "instructions": [
                        "Seek immediate medical attention for injuries",
                        "Stay in open areas away from buildings",
                        "Do not use damaged roads or bridges",
                        "Listen for emergency instructions",
                        "Help others if you are able"
                    ]
                }
            },
            DisasterType.HURRICANE.value: {
                AlertLevel.LOW.value: {
                    "title": "Tropical Storm Watch",
                    "message": "Tropical storm conditions possible in {location} within 48 hours.",
                    "instructions": [
                        "Monitor storm progress",
                        "Secure outdoor objects",
                        "Review evacuation plans",
                        "Stock emergency supplies"
                    ]
                },
                AlertLevel.MODERATE.value: {
                    "title": "Hurricane Watch",
                    "message": "Hurricane conditions possible in {location} within 48 hours.",
                    "instructions": [
                        "Complete storm preparations",
                        "Fuel vehicles and generators",
                        "Charge electronic devices",
                        "Review family emergency plan"
                    ]
                },
                AlertLevel.HIGH.value: {
                    "title": "Hurricane Warning",
                    "message": "Hurricane conditions expected in {location} within 36 hours.",
                    "instructions": [
                        "Complete all preparations immediately",
                        "Board up windows if necessary",
                        "Evacuate if in evacuation zone",
                        "Stay indoors during the storm"
                    ]
                },
                AlertLevel.CRITICAL.value: {
                    "title": "EXTREME HURRICANE WARNING",
                    "message": "Catastrophic hurricane impact imminent in {location}. Life-threatening conditions.",
                    "instructions": [
                        "SHELTER IN PLACE if evacuation not possible",
                        "Go to interior room on lowest floor",
                        "Stay away from windows",
                        "Do not go outside during eye of storm",
                        "Wait for all-clear from authorities"
                    ]
                }
            }
        }
    
    def _register_default_handlers(self):
        """Register default notification handlers."""
        
        # SMS handler
        self.notification_handlers[NotificationChannel.SMS] = self._send_sms
        
        # Email handler  
        self.notification_handlers[NotificationChannel.EMAIL] = self._send_email
        
        # Push notification handler
        self.notification_handlers[NotificationChannel.PUSH] = self._send_push
        
        # Mobile alert handler
        self.notification_handlers[NotificationChannel.MOBILE_ALERT] = self._send_mobile_alert
        
        # Social media handler
        self.notification_handlers[NotificationChannel.SOCIAL_MEDIA] = self._send_social_media
    
    async def generate_alert(
        self, 
        disaster_event: DisasterEvent,
        custom_message: Optional[str] = None
    ) -> Alert:
        """Generate an alert from a disaster event."""
        
        # Get alert template
        template = self.alert_templates.get(
            disaster_event.disaster_type.value, {}
        ).get(disaster_event.alert_level.value, {})
        
        if not template:
            # Fallback template
            template = {
                "title": f"{disaster_event.disaster_type.value.title()} Alert",
                "message": f"{disaster_event.disaster_type.value.title()} event detected in {disaster_event.location.region}",
                "instructions": ["Stay alert", "Follow official guidance", "Monitor conditions"]
            }
        
        # Format message with location
        message = custom_message or template["message"].format(
            location=disaster_event.location.region
        )
        
        # Determine notification channels based on alert level
        channels = self._select_channels(disaster_event.alert_level)
        
        # Set expiration time
        expires_at = datetime.now() + timedelta(
            hours=24 if disaster_event.alert_level in [AlertLevel.LOW, AlertLevel.MODERATE] else 12
        )
        
        alert = Alert(
            alert_id=f"alert_{disaster_event.event_id}_{datetime.now().strftime('%H%M%S')}",
            disaster_type=disaster_event.disaster_type,
            alert_level=disaster_event.alert_level,
            location=disaster_event.location,
            title=template["title"],
            message=message,
            instructions=template["instructions"],
            timestamp=datetime.now(),
            expires_at=expires_at,
            affected_areas=[disaster_event.location.region],
            estimated_population=disaster_event.estimated_population,
            channels=channels
        )
        
        return alert
    
    def _select_channels(self, alert_level: AlertLevel) -> List[NotificationChannel]:
        """Select appropriate notification channels based on alert level."""
        
        channel_map = {
            AlertLevel.LOW: [
                NotificationChannel.EMAIL,
                NotificationChannel.PUSH
            ],
            AlertLevel.MODERATE: [
                NotificationChannel.EMAIL,
                NotificationChannel.PUSH,
                NotificationChannel.SMS
            ],
            AlertLevel.HIGH: [
                NotificationChannel.SMS,
                NotificationChannel.EMAIL,
                NotificationChannel.PUSH,
                NotificationChannel.MOBILE_ALERT,
                NotificationChannel.SOCIAL_MEDIA
            ],
            AlertLevel.CRITICAL: [
                NotificationChannel.SMS,
                NotificationChannel.EMAIL,
                NotificationChannel.PUSH,
                NotificationChannel.MOBILE_ALERT,
                NotificationChannel.SOCIAL_MEDIA,
                NotificationChannel.SIRENS,
                NotificationChannel.RADIO,
                NotificationChannel.TV
            ]
        }
        
        return channel_map.get(alert_level, [NotificationChannel.EMAIL])
    
    async def issue_alert(self, alert: Alert) -> Dict[str, Any]:
        """Issue an alert through all specified channels."""
        
        # Store alert
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        notification_results = {}
        
        for channel in alert.channels:
            try:
                handler = self.notification_handlers.get(channel)
                if handler:
                    result = await handler(alert)
                    notification_results[channel.value] = {
                        "status": "sent",
                        "result": result
                    }
                else:
                    notification_results[channel.value] = {
                        "status": "error",
                        "error": "No handler registered"
                    }
            except Exception as e:
                notification_results[channel.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Use LLM to generate follow-up recommendations
        follow_up = await self._generate_follow_up_actions(alert)
        
        return {
            "alert_id": alert.alert_id,
            "issued_at": alert.timestamp.isoformat(),
            "notification_results": notification_results,
            "follow_up_actions": follow_up,
            "recipients_estimated": self._estimate_recipients(alert),
            "status": "issued"
        }
    
    async def _generate_follow_up_actions(self, alert: Alert) -> List[str]:
        """Generate follow-up actions using LLM."""
        
        prompt_data = {
            "alert": alert.to_dict(),
            "context": "disaster_warning_system"
        }
        
        try:
            recommendations = await llm_client.coordinate_agents(
                prompt_data,
                ["emergency_manager", "communications"]
            )
            
            return recommendations.get("agent_assignments", {}).get("communications", [
                "Monitor situation development",
                "Prepare situation updates",
                "Coordinate with local authorities",
                "Set up information hotlines"
            ])
            
        except Exception:
            # Fallback recommendations
            return [
                "Monitor situation development",
                "Prepare situation updates",
                "Coordinate with local authorities",
                "Set up information hotlines"
            ]
    
    def _estimate_recipients(self, alert: Alert) -> int:
        """Estimate number of alert recipients."""
        
        # Base estimate on population and alert radius
        base_population = alert.estimated_population
        
        # Adjust based on subscription patterns (simulated)
        subscription_rate = {
            AlertLevel.CRITICAL: 0.95,
            AlertLevel.HIGH: 0.85,
            AlertLevel.MODERATE: 0.70,
            AlertLevel.LOW: 0.50
        }.get(alert.alert_level, 0.50)
        
        return int(base_population * subscription_rate)
    
    async def update_alert(
        self, 
        alert_id: str, 
        new_level: Optional[AlertLevel] = None,
        additional_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing alert."""
        
        if alert_id not in self.active_alerts:
            raise ValueError(f"Alert {alert_id} not found")
        
        alert = self.active_alerts[alert_id]
        
        # Create updated alert
        if new_level:
            alert.alert_level = new_level
            alert.channels = self._select_channels(new_level)
        
        if additional_message:
            alert.message += f"\n\nUPDATE: {additional_message}"
        
        alert.timestamp = datetime.now()
        
        # Reissue alert
        result = await self.issue_alert(alert)
        result["update_type"] = "alert_updated"
        
        return result
    
    async def cancel_alert(self, alert_id: str, reason: str = "Situation resolved") -> Dict[str, Any]:
        """Cancel an active alert."""
        
        if alert_id not in self.active_alerts:
            raise ValueError(f"Alert {alert_id} not found")
        
        alert = self.active_alerts[alert_id]
        
        # Create cancellation alert
        cancel_alert = Alert(
            alert_id=f"cancel_{alert_id}",
            disaster_type=alert.disaster_type,
            alert_level=AlertLevel.LOW,
            location=alert.location,
            title=f"CANCELLED: {alert.title}",
            message=f"Previous alert has been cancelled. {reason}",
            instructions=["Normal activities may resume", "Stay informed of conditions"],
            timestamp=datetime.now(),
            channels=[NotificationChannel.SMS, NotificationChannel.EMAIL, NotificationChannel.PUSH]
        )
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        # Send cancellation
        result = await self.issue_alert(cancel_alert)
        result["cancellation_reason"] = reason
        
        return result
    
    # Notification handlers (simulated)
    async def _send_sms(self, alert: Alert) -> Dict[str, Any]:
        """Send SMS notification."""
        # Simulate SMS sending
        return {
            "method": "sms",
            "sent_at": datetime.now().isoformat(),
            "message_length": len(alert.message),
            "estimated_recipients": self._estimate_recipients(alert)
        }
    
    async def _send_email(self, alert: Alert) -> Dict[str, Any]:
        """Send email notification."""
        # Simulate email sending
        return {
            "method": "email",
            "sent_at": datetime.now().isoformat(),
            "subject": alert.title,
            "estimated_recipients": self._estimate_recipients(alert)
        }
    
    async def _send_push(self, alert: Alert) -> Dict[str, Any]:
        """Send push notification."""
        # Simulate push notification
        return {
            "method": "push_notification",
            "sent_at": datetime.now().isoformat(),
            "platforms": ["ios", "android"],
            "estimated_recipients": self._estimate_recipients(alert)
        }
    
    async def _send_mobile_alert(self, alert: Alert) -> Dict[str, Any]:
        """Send emergency mobile alert."""
        # Simulate emergency alert system
        return {
            "method": "emergency_alert_system",
            "sent_at": datetime.now().isoformat(),
            "cell_towers_targeted": 25,
            "estimated_recipients": self._estimate_recipients(alert)
        }
    
    async def _send_social_media(self, alert: Alert) -> Dict[str, Any]:
        """Send social media notification."""
        # Simulate social media posting
        return {
            "method": "social_media",
            "sent_at": datetime.now().isoformat(),
            "platforms": ["twitter", "facebook", "instagram"],
            "hashtags": [f"#{alert.disaster_type.value}alert", "#emergency"]
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for the specified hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = [
            alert.to_dict() for alert in self.alert_history
            if alert.timestamp >= cutoff
        ]
        
        return recent_alerts
    
    async def test_alert_system(self) -> Dict[str, Any]:
        """Test the alert system functionality."""
        
        # Create test alert
        test_location = Location(
            latitude=37.7749,
            longitude=-122.4194,
            region="Test Area"
        )
        
        test_alert = Alert(
            alert_id="test_alert_001",
            disaster_type=DisasterType.WILDFIRE,
            alert_level=AlertLevel.MODERATE,
            location=test_location,
            title="SYSTEM TEST - Wildfire Alert",
            message="This is a test of the emergency alert system. No action required.",
            instructions=["This is only a test", "Normal operations may continue"],
            timestamp=datetime.now(),
            channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH]
        )
        
        # Issue test alert
        result = await self.issue_alert(test_alert)
        result["test_mode"] = True
        
        return result

# Global warning system instance
warning_system = DisasterWarningSystem()