"""Example: Flood emergency response scenario."""
import asyncio
import json
from datetime import datetime

from src.agent.graph import process_emergency_event
from src.core.models import Location, DisasterType, AlertLevel
from src.core.warning_system import warning_system

async def run_flood_scenario():
    """Simulate a complete flood emergency response scenario."""
    
    print("🌊 FLOOD EMERGENCY SCENARIO")
    print("=" * 50)
    
    # Scenario: Heavy rainfall and river overflow in Houston area
    scenario_data = {
        "type": "sensor",
        "content": {
            "sensor_type": "water_level",
            "readings": {
                "level": 12.5,           # meters - well above normal
                "flow_rate": 1200,       # m³/s - extreme flow
                "normal_level": 5.0,     # meters
                "precipitation": 85.0,   # mm/hour - extreme rainfall
                "temperature": 28.0,
                "humidity": 95.0
            },
            "location": {
                "latitude": 29.7604,
                "longitude": -95.3698,
                "region": "Houston, Texas",
                "country": "USA"
            }
        },
        "metadata": {
            "source": "river_gauge_station_houston_001",
            "priority": "critical",
            "timestamp": datetime.now().isoformat(),
            "dam_status": "near_capacity"
        },
        "latitude": 29.7604,
        "longitude": -95.3698,
        "region": "Houston, Texas"
    }
    
    print(f"📍 Location: {scenario_data['content']['location']['region']}")
    print(f"🌊 Water Level: {scenario_data['content']['readings']['level']} m (Normal: {scenario_data['content']['readings']['normal_level']} m)")
    print(f"🌊 Flow Rate: {scenario_data['content']['readings']['flow_rate']} m³/s")
    print(f"🌧️  Precipitation: {scenario_data['content']['readings']['precipitation']} mm/hour")
    print()
    
    # Add social media input to simulate multi-modal processing
    social_media_data = {
        "type": "social_media",
        "content": {
            "posts": [
                {
                    "text": "Major flooding on Highway 59! Water up to my car windows. Need help!",
                    "location": {"latitude": 29.7604, "longitude": -95.3698},
                    "timestamp": datetime.now().isoformat(),
                    "platform": "twitter"
                },
                {
                    "text": "Buffalo Bayou overflowing into downtown Houston. Businesses evacuating",
                    "location": {"latitude": 29.7633, "longitude": -95.3633},
                    "timestamp": datetime.now().isoformat(),
                    "platform": "facebook"
                },
                {
                    "text": "Emergency: Water rising fast in Memorial area. Families need rescue",
                    "location": {"latitude": 29.7752, "longitude": -95.4618},
                    "timestamp": datetime.now().isoformat(),
                    "platform": "twitter"
                }
            ]
        },
        "metadata": {
            "source": "social_media_monitor",
            "collection_time": datetime.now().isoformat()
        },
        "latitude": 29.7604,
        "longitude": -95.3698,
        "region": "Houston, Texas"
    }
    
    print("📱 MULTI-MODAL PROCESSING: Social Media Analysis")
    print("-" * 40)
    
    # Process social media data
    from src.core.multimodal import multimodal_processor
    
    social_analysis = await multimodal_processor.process_social_media_input(
        social_media_data['content'], 
        social_media_data['metadata']
    )
    
    print(f"Posts Analyzed: {social_analysis['posts_analyzed']}")
    print(f"Relevant Posts: {social_analysis['relevant_posts']}")
    print(f"Disaster Indicators Found: {len(social_analysis['disaster_indicators'])}")
    print("Key Indicators:")
    for indicator in social_analysis['disaster_indicators'][:5]:  # Show first 5
        print(f"   - {indicator}")
    print(f"Trending Keywords: {social_analysis['trending_keywords']}")
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
        
        # Step 2: Show expert analysis
        coordination_results = result.get('coordination_results', [])
        if coordination_results:
            print("🏊 STEP 2: Flood Expert Analysis")
            print("-" * 30)
            
            for coord_result in coordination_results:
                expert_results = coord_result.get('expert_results', {})
                
                for expert_key, expert_data in expert_results.items():
                    if 'flood' in expert_key:
                        analyses = expert_data.get('analyses', {})
                        
                        # Show conditions analysis
                        if 'conditions' in analyses:
                            conditions = analyses['conditions']
                            expert_assessment = conditions.get('expert_assessment', {})
                            
                            print(f"Expert: {expert_data.get('expert_id', 'unknown')}")
                            print(f"Risk Assessment: {expert_assessment.get('risk_assessment', 'unknown')}")
                            print(f"Confidence: {expert_assessment.get('confidence', 0)}")
                            
                            # Show recommended actions
                            actions = expert_assessment.get('recommended_actions', [])
                            if actions:
                                print("Recommended Actions:")
                                for action in actions:
                                    print(f"   - {action}")
                            print()
                        
                        # Show evolution prediction
                        if 'evolution' in analyses:
                            evolution = analyses['evolution']
                            timeline = evolution.get('evolution_timeline', [])
                            
                            if timeline:
                                print("Flood Evolution Timeline:")
                                for event in timeline:
                                    print(f"   {event['time']}: {event['event']} (Severity: {event['severity']})")
                                print()
        
        # Step 3: Show LISFLOOD model results
        print("🌊 STEP 3: LISFLOOD Model Simulation")
        print("-" * 30)
        
        # Simulate calling LISFLOOD model directly
        from src.MCP.client import mcp_client
        
        location = Location(
            latitude=scenario_data['latitude'],
            longitude=scenario_data['longitude'],
            region=scenario_data['region']
        )
        
        precipitation_data = {
            "intensity": scenario_data['content']['readings']['precipitation'],
            "duration": 6,  # hours
            "total": scenario_data['content']['readings']['precipitation'] * 6
        }
        
        terrain_data = {
            "elevation": 15,  # meters above sea level (Houston is low)
            "slope": 0.5,    # very flat terrain
            "soil_type": "clay"
        }
        
        lisflood_result = await mcp_client.call_lisflood_model(
            location=location,
            precipitation_data=precipitation_data,
            terrain_data=terrain_data
        )
        
        if 'prediction' in lisflood_result.to_dict():
            prediction = lisflood_result.prediction
            print(f"Model: LISFLOOD")
            print(f"Confidence: {lisflood_result.confidence:.2f}")
            print(f"Max Water Depth: {prediction['max_water_depth']} meters")
            print(f"Flood Extent: {prediction['flood_extent']} km²")
            print(f"Peak Discharge: {prediction['peak_discharge']} m³/s")
            print(f"Flood Duration: {prediction['flood_duration']} hours")
            print(f"Evacuation Required: {prediction['evacuation_required']}")
            
            affected_areas = prediction.get('affected_areas', [])
            if affected_areas:
                print("Affected Areas:")
                for area in affected_areas:
                    print(f"   - {area['area_name']}: {area['depth']}m depth, {area['population']} people")
            print()
        
        # Step 4: Show damage assessment
        damage_assessments = result.get('damage_assessments', [])
        if damage_assessments:
            print("💰 STEP 4: CLIMADA Damage Assessment")
            print("-" * 30)
            for assessment in damage_assessments:
                if 'prediction' in assessment:
                    prediction = assessment['prediction']
                    print(f"Economic Damage: ${prediction.get('economic_damage', 0):,.2f}")
                    print(f"Affected Buildings: {prediction.get('affected_buildings', 0)}")
                    print(f"Affected Population: {prediction.get('affected_population', 0)}")
                    print(f"Recovery Time: {prediction.get('recovery_time', 0)} days")
                    print(f"Insurance Coverage: {prediction.get('insurance_coverage', 0):.0%}")
                    
                    infra_damage = prediction.get('infrastructure_damage', {})
                    if infra_damage:
                        print("Infrastructure Damage:")
                        for item, damage in infra_damage.items():
                            print(f"   - {item.replace('_', ' ').title()}: {damage}")
                    print()
        
        # Step 5: Generate and issue flood warning
        print("📢 STEP 5: Flood Warning System")
        print("-" * 30)
        
        if coordination_results and coordination_results[0].get('disaster_event'):
            disaster_event_data = coordination_results[0]['disaster_event']
            
            from src.core.models import DisasterEvent
            
            location = Location(
                latitude=disaster_event_data['location']['latitude'],
                longitude=disaster_event_data['location']['longitude'],
                region=disaster_event_data['location']['region']
            )
            
            disaster_event = DisasterEvent(
                event_id=disaster_event_data['event_id'],
                disaster_type=DisasterType.FLOOD,
                location=location,
                start_time=datetime.fromisoformat(disaster_event_data['start_time']),
                alert_level=AlertLevel.CRITICAL,  # Upgrade to critical due to extreme conditions
                description=f"Severe flooding in {location.region} with water levels {scenario_data['content']['readings']['level']}m above normal",
                affected_area=45.6,  # from LISFLOOD prediction
                estimated_population=50000,  # Houston area estimate
                confidence_score=0.92
            )
            
            # Generate emergency alert
            alert = await warning_system.generate_alert(
                disaster_event,
                custom_message=f"FLASH FLOOD EMERGENCY for {location.region}. Water levels at {scenario_data['content']['readings']['level']} meters - {scenario_data['content']['readings']['level'] - scenario_data['content']['readings']['normal_level']:.1f}m above normal. SEEK HIGHER GROUND IMMEDIATELY."
            )
            
            alert_result = await warning_system.issue_alert(alert)
            
            print(f"🚨 CRITICAL ALERT ISSUED")
            print(f"Title: {alert.title}")
            print(f"Message: {alert.message}")
            print("\nEmergency Instructions:")
            for i, instruction in enumerate(alert.instructions, 1):
                print(f"   {i}. {instruction}")
            print()
            print(f"Notification Channels: {[ch.value for ch in alert.channels]}")
            print(f"Estimated Recipients: {alert_result.get('recipients_estimated', 0):,}")
            
            # Show notification results
            notification_results = alert_result.get('notification_results', {})
            print("\nNotification Status:")
            for channel, result in notification_results.items():
                status = result.get('status', 'unknown')
                print(f"   - {channel.upper()}: {status}")
            print()
        
        # Step 6: Show evacuation planning
        print("🚗 STEP 6: Evacuation Planning")
        print("-" * 30)
        
        evacuation_zones = [
            {"zone": "Downtown Houston", "priority": "immediate", "population": 15000, "routes": ["I-45 North", "US-59 West"]},
            {"zone": "Memorial Area", "priority": "immediate", "population": 8500, "routes": ["I-10 West", "Beltway 8"]},
            {"zone": "Riverside District", "priority": "high", "population": 12000, "routes": ["I-45 South", "US-288"]},
            {"zone": "Heights", "priority": "moderate", "population": 6000, "routes": ["I-10 East", "US-290"]}
        ]
        
        total_evacuees = sum(zone['population'] for zone in evacuation_zones)
        print(f"Total Population to Evacuate: {total_evacuees:,}")
        print("\nEvacuation Zones:")
        
        for zone in evacuation_zones:
            print(f"   - {zone['zone']}: {zone['population']:,} people ({zone['priority']} priority)")
            print(f"     Routes: {', '.join(zone['routes'])}")
        print()
        
        print("✅ FLOOD SCENARIO COMPLETED SUCCESSFULLY")
        
        # Final summary
        print("📋 SCENARIO SUMMARY")
        print("-" * 20)
        print(f"Disaster Type: Severe Flooding")
        print(f"Location: {scenario_data['region']}")
        print(f"Water Level: {scenario_data['content']['readings']['level']}m ({scenario_data['content']['readings']['level'] - scenario_data['content']['readings']['normal_level']:.1f}m above normal)")
        print(f"Alert Level: CRITICAL")
        print(f"Estimated Affected Population: {total_evacuees:,}")
        print(f"Multi-Modal Data Sources: Sensor + Social Media")
        print(f"Models Used: LISFLOOD, CLIMADA")
        print(f"Response Status: Multi-agent coordination active")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in flood scenario: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the flood scenario
    result = asyncio.run(run_flood_scenario())