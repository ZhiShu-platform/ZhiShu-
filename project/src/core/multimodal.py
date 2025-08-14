"""Multi-modal input processing for disaster monitoring."""
import base64
import json
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from PIL import Image
import io

from .models import MultiModalInput, Location, SensorData
from .llm import llm_client

class MultiModalProcessor:
    """Processor for handling multiple types of input data."""
    
    def __init__(self):
        self.supported_types = [
            "text", "image", "sensor", "weather", "satellite", 
            "seismic", "social_media", "emergency_call"
        ]
    
    async def process_text_input(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process text input for disaster indicators."""
        
        # Extract disaster-related keywords
        disaster_keywords = {
            "wildfire": ["fire", "smoke", "burn", "flame", "ash", "evacuation"],
            "flood": ["flood", "water", "rain", "overflow", "dam", "river"],
            "earthquake": ["earthquake", "shake", "tremor", "seismic", "collapse"],
            "hurricane": ["hurricane", "storm", "wind", "cyclone", "tornado"]
        }
        
        detected_indicators = []
        severity_score = 0.0
        
        content_lower = content.lower()
        
        for disaster_type, keywords in disaster_keywords.items():
            matches = [kw for kw in keywords if kw in content_lower]
            if matches:
                detected_indicators.extend([f"{disaster_type}: {match}" for match in matches])
                severity_score += len(matches) * 0.1
        
        # Extract location information
        location_indicators = self._extract_location_from_text(content)
        
        # Extract urgency indicators
        urgency_keywords = ["urgent", "emergency", "immediate", "critical", "help", "danger"]
        urgency_score = sum(1 for kw in urgency_keywords if kw in content_lower) * 0.2
        
        return {
            "input_type": "text",
            "disaster_indicators": detected_indicators,
            "severity": min(severity_score + urgency_score, 1.0),
            "urgency": min(urgency_score, 1.0),
            "location_info": location_indicators,
            "temporal_patterns": self._extract_temporal_patterns(content),
            "confidence": 0.7 if detected_indicators else 0.3,
            "raw_content": content,
            "processing_timestamp": datetime.now().isoformat()
        }
    
    async def process_image_input(self, image_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process image input for visual disaster indicators."""
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Analyze image properties
            width, height = image.size
            image_format = image.format
            
            # Simulate computer vision analysis
            # In real implementation, this would use CV models
            visual_indicators = self._analyze_image_for_disasters(image, metadata)
            
            return {
                "input_type": "image",
                "disaster_indicators": visual_indicators.get("indicators", []),
                "severity": visual_indicators.get("severity", 0.5),
                "visual_features": {
                    "smoke_detected": visual_indicators.get("smoke", False),
                    "fire_detected": visual_indicators.get("fire", False),
                    "flood_detected": visual_indicators.get("flood", False),
                    "damage_visible": visual_indicators.get("damage", False)
                },
                "image_metadata": {
                    "width": width,
                    "height": height,
                    "format": image_format,
                    "size_bytes": len(image_data)
                },
                "confidence": visual_indicators.get("confidence", 0.6),
                "processing_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "input_type": "image",
                "error": f"Image processing failed: {str(e)}",
                "disaster_indicators": [],
                "severity": 0.0,
                "confidence": 0.0,
                "processing_timestamp": datetime.now().isoformat()
            }
    
    async def process_sensor_input(self, sensor_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data for disaster indicators."""
        
        readings = sensor_data.get("readings", {})
        sensor_type = sensor_data.get("sensor_type", "unknown")
        
        # Analyze sensor readings based on type
        indicators = []
        severity = 0.0
        
        if sensor_type == "weather":
            indicators, severity = self._analyze_weather_data(readings)
        elif sensor_type == "seismic":
            indicators, severity = self._analyze_seismic_data(readings)
        elif sensor_type == "air_quality":
            indicators, severity = self._analyze_air_quality_data(readings)
        elif sensor_type == "water_level":
            indicators, severity = self._analyze_water_level_data(readings)
        
        return {
            "input_type": "sensor",
            "sensor_type": sensor_type,
            "disaster_indicators": indicators,
            "severity": severity,
            "sensor_readings": readings,
            "anomaly_detected": severity > 0.6,
            "confidence": 0.9 if indicators else 0.4,
            "processing_timestamp": datetime.now().isoformat()
        }
    
    async def process_satellite_input(self, satellite_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process satellite imagery and data."""
        
        # Simulate satellite data analysis
        indicators = []
        
        # Check for thermal anomalies (potential fires)
        thermal_data = satellite_data.get("thermal", {})
        if thermal_data.get("max_temperature", 0) > 45:  # Celsius
            indicators.append("thermal anomaly detected - potential wildfire")
        
        # Check for vegetation changes
        ndvi_data = satellite_data.get("ndvi", {})
        if ndvi_data.get("change", 0) < -0.3:
            indicators.append("vegetation stress detected")
        
        # Check for flood indicators
        water_detection = satellite_data.get("water_extent", 0)
        if water_detection > 0.5:
            indicators.append("water extent increased - potential flooding")
        
        severity = len(indicators) * 0.3
        
        return {
            "input_type": "satellite",
            "disaster_indicators": indicators,
            "severity": min(severity, 1.0),
            "satellite_analysis": {
                "thermal_anomalies": thermal_data.get("anomaly_count", 0),
                "vegetation_health": ndvi_data.get("average", 0.5),
                "water_coverage": water_detection,
                "cloud_coverage": satellite_data.get("cloud_cover", 0.0)
            },
            "confidence": 0.8,
            "processing_timestamp": datetime.now().isoformat()
        }
    
    async def process_social_media_input(self, social_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process social media posts for disaster indicators."""
        
        posts = social_data.get("posts", [])
        indicators = []
        severity_scores = []
        
        for post in posts:
            text = post.get("text", "")
            location = post.get("location", {})
            timestamp = post.get("timestamp", "")
            
            # Process text content
            text_analysis = await self.process_text_input(text, {"source": "social_media"})
            
            if text_analysis.get("disaster_indicators"):
                indicators.extend(text_analysis["disaster_indicators"])
                severity_scores.append(text_analysis["severity"])
        
        avg_severity = sum(severity_scores) / len(severity_scores) if severity_scores else 0.0
        
        return {
            "input_type": "social_media",
            "disaster_indicators": indicators,
            "severity": avg_severity,
            "posts_analyzed": len(posts),
            "relevant_posts": len(severity_scores),
            "trending_keywords": self._extract_trending_keywords(posts),
            "confidence": min(0.6 + (len(severity_scores) * 0.1), 0.9),
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _extract_location_from_text(self, text: str) -> Dict[str, Any]:
        """Extract location information from text."""
        
        # Simple location extraction (in real implementation, use NER)
        location_keywords = ["near", "at", "in", "around", "close to"]
        
        words = text.lower().split()
        locations = []
        
        for i, word in enumerate(words):
            if word in location_keywords and i + 1 < len(words):
                potential_location = words[i + 1]
                if len(potential_location) > 2:
                    locations.append(potential_location)
        
        return {
            "extracted_locations": locations,
            "confidence": 0.5 if locations else 0.0
        }
    
    def _extract_temporal_patterns(self, text: str) -> List[str]:
        """Extract temporal patterns from text."""
        
        temporal_keywords = [
            "now", "currently", "just happened", "minutes ago", 
            "hours ago", "this morning", "tonight", "yesterday"
        ]
        
        patterns = []
        text_lower = text.lower()
        
        for keyword in temporal_keywords:
            if keyword in text_lower:
                patterns.append(keyword)
        
        return patterns
    
    def _analyze_image_for_disasters(self, image: Image.Image, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image for disaster indicators using simulated CV."""
        
        # Simulate computer vision analysis
        # In real implementation, this would use trained models
        
        # Analyze based on image properties and metadata
        width, height = image.size
        pixel_data = np.array(image)
        
        # Simple color analysis
        avg_color = np.mean(pixel_data, axis=(0, 1))
        
        indicators = []
        severity = 0.0
        
        # Simulate fire/smoke detection based on color analysis
        if len(avg_color) >= 3:  # RGB
            red_dominance = avg_color[0] / (np.sum(avg_color) + 1)
            if red_dominance > 0.4:  # High red content
                indicators.append("potential fire or flames detected")
                severity += 0.7
            
            # Gray tones might indicate smoke
            color_variance = np.var(avg_color)
            if color_variance < 100:  # Low variance = grayish
                indicators.append("smoke or haze detected")
                severity += 0.5
        
        return {
            "indicators": indicators,
            "severity": min(severity, 1.0),
            "confidence": 0.6,
            "smoke": "smoke" in str(indicators),
            "fire": "fire" in str(indicators),
            "flood": False,  # Would need specialized analysis
            "damage": False  # Would need specialized analysis
        }
    
    def _analyze_weather_data(self, readings: Dict[str, Any]) -> tuple:
        """Analyze weather sensor readings."""
        
        indicators = []
        severity = 0.0
        
        temperature = readings.get("temperature", 20)
        humidity = readings.get("humidity", 50)
        wind_speed = readings.get("wind_speed", 10)
        pressure = readings.get("pressure", 1013)
        precipitation = readings.get("precipitation", 0)
        
        # Fire weather conditions
        if temperature > 35 and humidity < 20 and wind_speed > 25:
            indicators.append("extreme fire weather conditions")
            severity += 0.8
        elif temperature > 30 and humidity < 30:
            indicators.append("high fire danger conditions")
            severity += 0.6
        
        # Storm conditions
        if wind_speed > 80:
            indicators.append("hurricane-force winds detected")
            severity += 0.9
        elif wind_speed > 60:
            indicators.append("severe storm conditions")
            severity += 0.7
        
        # Heavy precipitation
        if precipitation > 50:
            indicators.append("extreme precipitation - flood risk")
            severity += 0.7
        elif precipitation > 25:
            indicators.append("heavy rainfall detected")
            severity += 0.5
        
        return indicators, min(severity, 1.0)
    
    def _analyze_seismic_data(self, readings: Dict[str, Any]) -> tuple:
        """Analyze seismic sensor readings."""
        
        indicators = []
        severity = 0.0
        
        magnitude = readings.get("magnitude", 0)
        acceleration = readings.get("acceleration", 0)
        frequency = readings.get("frequency", 0)
        
        if magnitude >= 7.0:
            indicators.append("major earthquake detected")
            severity += 1.0
        elif magnitude >= 6.0:
            indicators.append("strong earthquake detected")
            severity += 0.8
        elif magnitude >= 5.0:
            indicators.append("moderate earthquake detected")
            severity += 0.6
        elif magnitude >= 3.0:
            indicators.append("minor earthquake detected")
            severity += 0.3
        
        if acceleration > 0.5:  # g
            indicators.append("high ground acceleration")
            severity += 0.5
        
        return indicators, min(severity, 1.0)
    
    def _analyze_air_quality_data(self, readings: Dict[str, Any]) -> tuple:
        """Analyze air quality sensor readings."""
        
        indicators = []
        severity = 0.0
        
        pm25 = readings.get("pm2.5", 0)
        pm10 = readings.get("pm10", 0)
        co = readings.get("co", 0)
        
        if pm25 > 250:  # Very unhealthy
            indicators.append("hazardous air quality - potential fire")
            severity += 0.8
        elif pm25 > 150:  # Unhealthy
            indicators.append("poor air quality detected")
            severity += 0.6
        
        if co > 30:  # ppm
            indicators.append("high carbon monoxide levels")
            severity += 0.7
        
        return indicators, min(severity, 1.0)
    
    def _analyze_water_level_data(self, readings: Dict[str, Any]) -> tuple:
        """Analyze water level sensor readings."""
        
        indicators = []
        severity = 0.0
        
        water_level = readings.get("level", 0)
        flow_rate = readings.get("flow_rate", 0)
        normal_level = readings.get("normal_level", 5)
        
        level_ratio = water_level / (normal_level + 0.1)
        
        if level_ratio > 2.0:
            indicators.append("severe flooding detected")
            severity += 1.0
        elif level_ratio > 1.5:
            indicators.append("flood conditions detected")
            severity += 0.8
        elif level_ratio > 1.2:
            indicators.append("elevated water levels")
            severity += 0.6
        
        if flow_rate > 1000:  # m³/s
            indicators.append("extreme water flow")
            severity += 0.7
        
        return indicators, min(severity, 1.0)
    
    def _extract_trending_keywords(self, posts: List[Dict[str, Any]]) -> List[str]:
        """Extract trending keywords from social media posts."""
        
        word_count = {}
        disaster_related = []
        
        for post in posts:
            text = post.get("text", "").lower()
            words = text.split()
            
            for word in words:
                if len(word) > 3:  # Filter short words
                    word_count[word] = word_count.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        
        # Filter for disaster-related keywords
        disaster_keywords = [
            "fire", "smoke", "flood", "earthquake", "storm", "emergency",
            "evacuation", "disaster", "help", "rescue", "damage"
        ]
        
        for word, count in sorted_words[:20]:  # Top 20
            if any(keyword in word for keyword in disaster_keywords):
                disaster_related.append(word)
        
        return disaster_related[:10]  # Return top 10 disaster-related keywords

# Global processor instance
multimodal_processor = MultiModalProcessor()