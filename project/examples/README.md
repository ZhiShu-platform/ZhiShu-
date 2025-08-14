# Emergency Management Platform - Examples

This directory contains comprehensive examples and test scenarios for the multi-modal multi-agent emergency platform.

## 🔥 Available Examples

### 1. Wildfire Scenario (`wildfire_scenario.py`)
Demonstrates a complete wildfire emergency response workflow:
- High-temperature, low-humidity weather conditions
- Multi-agent coordination between wildfire experts
- Cell2Fire model integration for fire spread prediction
- CLIMADA damage assessment
- Emergency alert generation and distribution
- Resource allocation and response planning

**Key Features:**
- Real-time weather data processing
- Expert agent analysis and recommendations
- Evacuation zone planning
- Multi-channel alert distribution

### 2. Flood Scenario (`flood_scenario.py`)
Simulates a severe flooding emergency with multi-modal data:
- River gauge and precipitation sensor data
- Social media monitoring for real-time situation awareness
- LISFLOOD model for flood prediction
- Multi-level evacuation planning
- Critical alert issuance

**Key Features:**
- Multi-modal input processing (sensors + social media)
- LISFLOOD integration for flood modeling
- Evacuation route planning
- Emergency broadcast coordination

### 3. System Test (`system_test.py`)
Comprehensive system testing and health monitoring:
- Component-by-component testing
- Performance benchmarking
- End-to-end workflow validation
- System health monitoring

**Test Coverage:**
- MCP client health checks
- Multi-modal processing validation
- Disaster coordinator functionality
- Warning system operation
- Individual model performance
- End-to-end emergency processing

## 🚀 Quick Start

### Prerequisites
1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   export DEEPSEEK_API_KEY="your_api_key"
   export LANGFUSE_SECRET_KEY="your_secret_key"
   export LANGFUSE_PUBLIC_KEY="your_public_key"
   export LANGFUSE_HOST="http://localhost:3000"
   ```

### Running Examples

1. **Wildfire Scenario:**
   ```bash
   cd examples
   python wildfire_scenario.py
   ```

2. **Flood Scenario:**
   ```bash
   cd examples
   python flood_scenario.py
   ```

3. **System Test:**
   ```bash
   cd examples
   python system_test.py
   ```

## 📊 Expected Output

### Wildfire Scenario Output
```
🔥 WILDFIRE EMERGENCY SCENARIO
==================================================
📍 Location: Yosemite National Park
🌡️  Temperature: 42.0°C
💧 Humidity: 15.0%
💨 Wind Speed: 35.0 km/h

🚨 STEP 1: Processing Emergency Input
------------------------------
✅ Processing completed at: 2024-01-15T10:30:45.123456
📊 Processing Summary:
   - Input Processed: True
   - Threats Detected: 1
   - Alerts Generated: 1
   ...
```

### System Test Output
```
🧪 EMERGENCY MANAGEMENT PLATFORM - SYSTEM TEST
============================================================
🔧 TEST 1: MCP Client Health Check
----------------------------------------
✅ MCP Client Health Check: PASSED
   Models Available: ['cell2fire', 'climada', 'lisflood', 'nfdrs4', 'pangu', 'aurora']
   Active Connections: 0
...
📊 OVERALL TEST RESULTS
==============================
✅ Overall Status: HEALTHY
📈 Success Rate: 85.7% (6/7)
```

## 🏗️ Architecture Overview

The examples demonstrate the complete disaster management workflow:

```
Input Processing → Threat Detection → Alert Generation → Agent Coordination → Response Execution → Damage Assessment → Reporting
```

### Multi-Agent Collaboration
- **Coordinator Agent**: Orchestrates overall response
- **Disaster Experts**: Specialized agents for each disaster type
- **Monitor Agents**: Continuous situation monitoring
- **Response Agents**: Resource allocation and deployment

### Model Integration (MCP)
- **Cell2Fire**: Wildfire spread simulation
- **CLIMADA**: Economic damage assessment
- **LISFLOOD**: Flood modeling and prediction
- **Pangu Weather**: Advanced weather forecasting
- **NFDRS4**: Fire danger rating
- **Aurora**: Climate modeling

### Multi-Modal Processing
- **Sensor Data**: Weather stations, seismic monitors, water gauges
- **Satellite Imagery**: Thermal detection, vegetation monitoring
- **Social Media**: Real-time situation reports
- **Emergency Calls**: Voice and text emergency communications
- **Weather Data**: Meteorological observations

## 🔧 Customization

### Adding New Scenarios
Create new scenario files following this template:

```python
async def run_custom_scenario():
    scenario_data = {
        "type": "sensor",  # or "image", "social_media", etc.
        "content": {
            # Your scenario-specific data
        },
        "metadata": {
            "source": "your_source",
            "priority": "high"
        },
        "latitude": 0.0,
        "longitude": 0.0,
        "region": "Your Area"
    }
    
    result = await graph.process_emergency(scenario_data)
    # Process and display results
    return result
```

### Modifying Alert Templates
Update warning system templates in `src/core/warning_system.py`:

```python
self.alert_templates[DisasterType.YOUR_TYPE] = {
    AlertLevel.HIGH: {
        "title": "Your Alert Title",
        "message": "Your alert message for {location}",
        "instructions": ["Step 1", "Step 2", "Step 3"]
    }
}
```

## 📈 Performance Metrics

The system is designed to meet these performance targets:
- **Alert Processing**: < 5 seconds end-to-end
- **Model Response**: < 30 seconds per model call
- **Multi-Agent Coordination**: < 10 seconds
- **System Availability**: 99.9%

## 🐛 Troubleshooting

### Common Issues

1. **Model Connection Failures**
   - Check MCP host configurations
   - Verify model container status
   - Review network connectivity

2. **API Rate Limits**
   - Implement backoff strategies
   - Monitor API usage
   - Use caching where appropriate

3. **Memory Issues**
   - Monitor system resources
   - Implement result pagination
   - Clear old data periodically

### Debug Mode
Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Langfuse Monitoring](https://langfuse.com/docs)
- [Cell2Fire Model](https://github.com/cell2fire/cell2fire)
- [CLIMADA Documentation](https://climada-python.readthedocs.io/)

## 🤝 Contributing

To add new examples or improve existing ones:

1. Follow the existing code structure
2. Include comprehensive error handling
3. Add detailed logging and output
4. Update this README with new examples
5. Test thoroughly with `system_test.py`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.