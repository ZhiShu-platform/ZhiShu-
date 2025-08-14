"""Example: Wildfire emergency response scenario."""
import asyncio
import json
from datetime import datetime

from src.agent.graph import process_emergency_event
from src.core.models import Location, DisasterType, AlertLevel
from src.core.multimodal import multimodal_processor
from src.core.warning_system import warning_system

async def run_wildfire_scenario():
    """Simulate a complete wildfire emergency response scenario."""
    
    print("🔥 WILDFIRE EMERGENCY SCENARIO")
    print("=" * 50)
    
    # Scenario: Wildfire detected in California forest area
    scenario_data = {
        "type": "sensor",
        "content": {
            "sensor_type": "weather",
            "readings": {
                "temperature": 42.0,      # High temperature
                "humidity": 15.0,         # Low humidity
                "wind_speed": 35.0,       # High wind speed
                "pressure": 1008.2,
                "precipitation": 0.0
            },
            "location": {
                "latitude": 37.8651,
                "longitude": -119.5383,
                "region": "Yosemite National Park",
                "country": "USA"
            }
        },
        "metadata": {
            "source": "weather_station_001",
            "priority": "high",
            "timestamp": datetime.now().isoformat()
        },
        "latitude": 37.8651,
        "longitude": -119.5383,
        "region": "Yosemite National Park"
    }
    
    print(f"📍 Location: {scenario_data['content']['location']['region']}")
    print(f"🌡️  Temperature: {scenario_data['content']['readings']['temperature']}°C")
    print(f"💧 Humidity: {scenario_data['content']['readings']['humidity']}%")
    print(f"💨 Wind Speed: {scenario_data['content']['readings']['wind_speed']} km/h")
    print()
    
    # Step 1: Process the emergency through the main graph
    print("🚨 STEP 1: Processing Emergency Input")
    print("-" * 30)
    
    try:
        result = await process_emergency_event(scenario_data)
        
        print(f"✅ Processing completed at: {result.get('report_timestamp')}")
        print(f"📊 Processing Summary:")
        summary = result.get('processing_summary', {})
        for key, value in summary.items():
            print(f"   - {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Step 2: Show alerts generated
        alerts = result.get('alerts', [])
        if alerts:
            print("🚨 STEP 2: Alerts Generated")
            print("-" * 30)
            for alert in alerts:
                print(f"Alert ID: {alert['alert_id']}")
                print(f"Type: {alert['disaster_type']}")
                print(f"Level: {alert['alert_level']}")
                print(f"Description: {alert['description']}")
                print(f"Requires Immediate Response: {alert['requires_immediate_response']}")
                
                impact = alert.get('estimated_impact', {})
                print(f"Estimated Impact:")
                print(f"   - Population: {impact.get('estimated_affected_population', 0)}")
                print(f"   - Area: {impact.get('estimated_affected_area', 0)} km²")
                print(f"   - Economic: ${impact.get('economic_impact_estimate', 0):,}")
                print()
        
        # Step 3: Show coordination results
        coordination_results = result.get('coordination_results', [])
        if coordination_results:
            print("🤝 STEP 3: Multi-Agent Coordination")
            print("-" * 30)
            for coord_result in coordination_results:
                if 'final_report' in coord_result:
                    final_report = coord_result['final_report']
                    coord_summary = final_report.get('coordination_summary', {})
                    
                    print(f"Event ID: {coord_summary.get('event_id')}")
                    print(f"Activated Experts: {coord_summary.get('activated_experts', [])}")
                    
                    resource_allocation = coord_result.get('resource_allocation', {})
                    if resource_allocation:
                        print("Resource Allocation:")
                        assignments = resource_allocation.get('resource_assignments', {})
                        for resource, amount in assignments.items():
                            print(f"   - {resource.replace('_', ' ').title()}: {amount}")
                    print()
        
        # Step 4: Show response execution
        response_execution = result.get('response_execution', [])
        if response_execution:
            print("⚡ STEP 4: Response Execution")
            print("-" * 30)
            for response in response_execution:
                print(f"Event ID: {response.get('event_id')}")
                print(f"Status: {response.get('execution_status')}")
                print(f"Estimated Completion: {response.get('estimated_completion')}")
                print(f"Success Probability: {response.get('success_probability', 0):.2f}")
                print(f"Response Teams: {response.get('response_teams', [])}")
                print()
        
        # Step 5: Show damage assessment
        damage_assessments = result.get('damage_assessments', [])
        if damage_assessments:
            print("💰 STEP 5: Damage Assessment (CLIMADA)")
            print("-" * 30)
            for assessment in damage_assessments:
                if 'prediction' in assessment:
                    prediction = assessment['prediction']
                    print(f"Model: {assessment.get('model_name', 'unknown')}")
                    print(f"Confidence: {assessment.get('confidence', 0):.2f}")
                    print(f"Economic Damage: ${prediction.get('economic_damage', 0):,.2f}")
                    print(f"Affected Buildings: {prediction.get('affected_buildings', 0)}")
                    print(f"Affected Population: {prediction.get('affected_population', 0)}")
                    print(f"Recovery Time: {prediction.get('recovery_time', 0)} days")
                    
                    infra_damage = prediction.get('infrastructure_damage', {})
                    if infra_damage:
                        print("Infrastructure Damage:")
                        for item, damage in infra_damage.items():
                            print(f"   - {item.replace('_', ' ').title()}: {damage}")
                    print()
        
        print("📋 STEP 6: System Recommendations")
        print("-" * 30)
        recommendations = result.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print()
        
        # Step 7: Test warning system
        print("📢 STEP 7: Warning System Test")
        print("-" * 30)
        
        # Generate alert from the first detected event
        if coordination_results and coordination_results[0].get('disaster_event'):
            disaster_event_data = coordination_results[0]['disaster_event']
            
            # Create a proper DisasterEvent object for the warning system
            from src.core.models import DisasterEvent
            
            location = Location(
                latitude=disaster_event_data['location']['latitude'],
                longitude=disaster_event_data['location']['longitude'],
                region=disaster_event_data['location']['region']
            )
            
            disaster_event = DisasterEvent(
                event_id=disaster_event_data['event_id'],
                disaster_type=DisasterType(disaster_event_data['disaster_type']),
                location=location,
                start_time=datetime.fromisoformat(disaster_event_data['start_time']),
                alert_level=AlertLevel(disaster_event_data['alert_level']),
                description=disaster_event_data['description'],
                affected_area=disaster_event_data['affected_area'],
                estimated_population=disaster_event_data['estimated_population'],
                confidence_score=disaster_event_data['confidence_score']
            )
            
            # Generate and issue alert
            alert = await warning_system.generate_alert(disaster_event)
            alert_result = await warning_system.issue_alert(alert)
            
            print(f"Alert Generated: {alert.title}")
            print(f"Message: {alert.message}")
            print("Instructions:")
            for i, instruction in enumerate(alert.instructions, 1):
                print(f"   {i}. {instruction}")
            print()
            print(f"Notification Channels: {[ch.value for ch in alert.channels]}")
            print(f"Estimated Recipients: {alert_result.get('recipients_estimated', 0)}")
            print()
        
        print("✅ WILDFIRE SCENARIO COMPLETED SUCCESSFULLY")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in wildfire scenario: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the wildfire scenario
    result = asyncio.run(run_wildfire_scenario())