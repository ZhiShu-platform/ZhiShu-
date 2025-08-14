"""Comprehensive system test for the emergency management platform."""
import asyncio
import json
import time
from datetime import datetime

from src.agent.graph import process_emergency_event, get_system_health
from src.agent.coordinator import disaster_coordinator
from src.MCP.client import mcp_client
from src.core.warning_system import warning_system
from src.core.multimodal import multimodal_processor

async def test_system_components():
    """Test all major system components."""
    
    print("🧪 EMERGENCY MANAGEMENT PLATFORM - SYSTEM TEST")
    print("=" * 60)
    
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "overall_status": "unknown"
    }
    
    # Test 1: MCP Client Health Check
    print("🔧 TEST 1: MCP Client Health Check")
    print("-" * 40)
    
    try:
        health_status = await mcp_client.health_check()
        test_results["tests"]["mcp_health"] = {
            "status": "passed",
            "details": health_status
        }
        
        print("✅ MCP Client Health Check: PASSED")
        print(f"   Models Available: {list(health_status['models'].keys())}")
        print(f"   Active Connections: {health_status['total_active']}")
        
    except Exception as e:
        test_results["tests"]["mcp_health"] = {
            "status": "failed",
            "error": str(e)
        }
        print(f"❌ MCP Client Health Check: FAILED - {e}")
    
    print()
    
    # Test 2: Multi-modal Processing
    print("🎭 TEST 2: Multi-modal Processing")
    print("-" * 40)
    
    try:
        # Test text processing
        text_result = await multimodal_processor.process_text_input(
            "Emergency! Large fire spreading rapidly near downtown. Heavy smoke visible. Evacuation needed!",
            {"source": "emergency_call"}
        )
        
        # Test sensor processing
        sensor_result = await multimodal_processor.process_sensor_input({
            "sensor_type": "weather",
            "readings": {
                "temperature": 45.0,
                "humidity": 12.0,
                "wind_speed": 40.0,
                "pressure": 1005.0
            }
        }, {"location": "test_area"})
        
        test_results["tests"]["multimodal"] = {
            "status": "passed",
            "text_indicators": len(text_result['disaster_indicators']),
            "sensor_severity": sensor_result['severity']
        }
        
        print("✅ Multi-modal Processing: PASSED")
        print(f"   Text Indicators Found: {len(text_result['disaster_indicators'])}")
        print(f"   Sensor Severity Score: {sensor_result['severity']:.2f}")
        
    except Exception as e:
        test_results["tests"]["multimodal"] = {
            "status": "failed",
            "error": str(e)
        }
        print(f"❌ Multi-modal Processing: FAILED - {e}")
    
    print()
    
    # Test 3: Disaster Coordinator
    print("🎯 TEST 3: Disaster Coordinator")
    print("-" * 40)
    
    try:
        coordinator_status = await disaster_coordinator.get_system_status()
        
        test_results["tests"]["coordinator"] = {
            "status": "passed",
            "available_agents": len(coordinator_status['available_agents']),
            "system_status": coordinator_status['system_status']
        }
        
        print("✅ Disaster Coordinator: PASSED")
        print(f"   Available Agents: {len(coordinator_status['available_agents'])}")
        print(f"   System Status: {coordinator_status['system_status']}")
        print(f"   Agent Types: {coordinator_status['available_agents']}")
        
    except Exception as e:
        test_results["tests"]["coordinator"] = {
            "status": "failed",
            "error": str(e)
        }
        print(f"❌ Disaster Coordinator: FAILED - {e}")
    
    print()
    
    # Test 4: Warning System
    print("📢 TEST 4: Warning System")
    print("-" * 40)
    
    try:
        warning_test = await warning_system.test_alert_system()
        
        test_results["tests"]["warning_system"] = {
            "status": "passed",
            "alert_issued": warning_test.get("status") == "issued",
            "test_mode": warning_test.get("test_mode", False)
        }
        
        print("✅ Warning System: PASSED")
        print(f"   Test Alert Status: {warning_test.get('status')}")
        print(f"   Estimated Recipients: {warning_test.get('recipients_estimated', 0)}")
        
        # Show notification results
        notification_results = warning_test.get('notification_results', {})
        print("   Notification Channels:")
        for channel, result in notification_results.items():
            print(f"      - {channel}: {result.get('status', 'unknown')}")
        
    except Exception as e:
        test_results["tests"]["warning_system"] = {
            "status": "failed",
            "error": str(e)
        }
        print(f"❌ Warning System: FAILED - {e}")
    
    print()
    
    # Test 5: Individual Model Calls
    print("🤖 TEST 5: Individual Model Calls")
    print("-" * 40)
    
    model_tests = {}
    
    # Test Cell2Fire
    try:
        from src.core.models import Location
        test_location = Location(latitude=37.7749, longitude=-122.4194, region="Test Area")
        
        cell2fire_result = await mcp_client.call_cell2fire_model(
            location=test_location,
            weather_data={"temperature": 35, "humidity": 20, "wind_speed": 30},
            fuel_data={"fuel_type": "mixed", "moisture": 8.0},
            ignition_points=[{"lat": 37.7749, "lon": -122.4194, "intensity": 100}]
        )
        
        model_tests["cell2fire"] = {
            "status": "passed",
            "confidence": cell2fire_result.confidence,
            "processing_time": cell2fire_result.processing_time
        }
        
        print(f"   ✅ Cell2Fire: PASSED (confidence: {cell2fire_result.confidence:.2f})")
        
    except Exception as e:
        model_tests["cell2fire"] = {"status": "failed", "error": str(e)}
        print(f"   ❌ Cell2Fire: FAILED - {e}")
    
    # Test CLIMADA
    try:
        from src.core.models import DisasterType
        
        climada_result = await mcp_client.call_climada_model(
            location=test_location,
            disaster_type=DisasterType.WILDFIRE,
            hazard_data={"intensity": 0.8, "duration": 6},
            exposure_data={"buildings": 100, "population": 500}
        )
        
        model_tests["climada"] = {
            "status": "passed",
            "confidence": climada_result.confidence,
            "processing_time": climada_result.processing_time
        }
        
        print(f"   ✅ CLIMADA: PASSED (confidence: {climada_result.confidence:.2f})")
        
    except Exception as e:
        model_tests["climada"] = {"status": "failed", "error": str(e)}
        print(f"   ❌ CLIMADA: FAILED - {e}")
    
    # Test LISFLOOD
    try:
        lisflood_result = await mcp_client.call_lisflood_model(
            location=test_location,
            precipitation_data={"intensity": 50, "duration": 12},
            terrain_data={"elevation": 100, "slope": 5.0}
        )
        
        model_tests["lisflood"] = {
            "status": "passed",
            "confidence": lisflood_result.confidence,
            "processing_time": lisflood_result.processing_time
        }
        
        print(f"   ✅ LISFLOOD: PASSED (confidence: {lisflood_result.confidence:.2f})")
        
    except Exception as e:
        model_tests["lisflood"] = {"status": "failed", "error": str(e)}
        print(f"   ❌ LISFLOOD: FAILED - {e}")
    
    # Test Pangu Weather
    try:
        pangu_result = await mcp_client.call_pangu_weather_model(
            location=test_location,
            forecast_hours=72
        )
        
        model_tests["pangu"] = {
            "status": "passed",
            "processing_time": pangu_result.get("processing_time", 0)
        }
        
        print(f"   ✅ Pangu Weather: PASSED")
        
    except Exception as e:
        model_tests["pangu"] = {"status": "failed", "error": str(e)}
        print(f"   ❌ Pangu Weather: FAILED - {e}")
    
    test_results["tests"]["models"] = model_tests
    print()
    
    # Test 6: End-to-End Emergency Processing
    print("🚨 TEST 6: End-to-End Emergency Processing")
    print("-" * 40)
    
    try:
        test_emergency = {
            "type": "sensor",
            "content": {
                "sensor_type": "weather",
                "readings": {
                    "temperature": 38.0,
                    "humidity": 18.0,
                    "wind_speed": 32.0,
                    "pressure": 1009.0
                }
            },
            "metadata": {"source": "test_sensor", "priority": "high"},
            "latitude": 37.7749,
            "longitude": -122.4194,
            "region": "Test Emergency Area"
        }
        
        start_time = time.time()
        emergency_result = await process_emergency_event(test_emergency)
        processing_time = time.time() - start_time
        
        test_results["tests"]["end_to_end"] = {
            "status": "passed",
            "processing_time": processing_time,
            "alerts_generated": len(emergency_result.get('alerts', [])),
            "coordination_executed": len(emergency_result.get('coordination_results', []))
        }
        
        print("✅ End-to-End Processing: PASSED")
        print(f"   Processing Time: {processing_time:.2f} seconds")
        print(f"   Alerts Generated: {len(emergency_result.get('alerts', []))}")
        print(f"   Coordination Results: {len(emergency_result.get('coordination_results', []))}")
        
    except Exception as e:
        test_results["tests"]["end_to_end"] = {
            "status": "failed",
            "error": str(e)
        }
        print(f"❌ End-to-End Processing: FAILED - {e}")
    
    print()
    
    # Test 7: System Health Check
    print("❤️  TEST 7: Overall System Health")
    print("-" * 40)
    
    try:
        system_health = await get_system_health()
        
        test_results["tests"]["system_health"] = {
            "status": "passed",
            "overall_status": system_health['system_health']['overall_status']
        }
        
        print("✅ System Health Check: PASSED")
        print(f"   Overall Status: {system_health['system_health']['overall_status']}")
        print(f"   Graph Status: {system_health['system_health']['graph_status']}")
        
    except Exception as e:
        test_results["tests"]["system_health"] = {
            "status": "failed",
            "error": str(e)
        }
        print(f"❌ System Health Check: FAILED - {e}")
    
    print()
    
    # Calculate overall test results
    passed_tests = sum(1 for test in test_results["tests"].values() 
                      if isinstance(test, dict) and test.get("status") == "passed")
    total_tests = len([t for t in test_results["tests"].values() if isinstance(t, dict)])
    
    # Add model test results
    if "models" in test_results["tests"]:
        model_results = test_results["tests"]["models"]
        model_passed = sum(1 for test in model_results.values() 
                          if test.get("status") == "passed")
        model_total = len(model_results)
        passed_tests += model_passed
        total_tests += model_total
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 80:
        test_results["overall_status"] = "healthy"
        status_emoji = "✅"
    elif success_rate >= 60:
        test_results["overall_status"] = "warning"
        status_emoji = "⚠️"
    else:
        test_results["overall_status"] = "critical"
        status_emoji = "❌"
    
    print("📊 OVERALL TEST RESULTS")
    print("=" * 30)
    print(f"{status_emoji} Overall Status: {test_results['overall_status'].upper()}")
    print(f"📈 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    print(f"🕒 Test Duration: {time.time() - start_time:.2f} seconds")
    print()
    
    print("📋 DETAILED RESULTS:")
    for test_name, result in test_results["tests"].items():
        if isinstance(result, dict):
            status = result.get("status", "unknown")
            emoji = "✅" if status == "passed" else "❌"
            print(f"{emoji} {test_name.replace('_', ' ').title()}: {status.upper()}")
    
    print()
    print("🏁 SYSTEM TEST COMPLETED")
    
    return test_results

async def run_performance_benchmark():
    """Run performance benchmarks."""
    
    print("⚡ PERFORMANCE BENCHMARK")
    print("=" * 30)
    
    # Benchmark 1: Alert Processing Speed
    print("🚨 Alert Processing Speed Test")
    
    test_scenarios = [
        {"type": "wildfire", "severity": "high"},
        {"type": "flood", "severity": "critical"},
        {"type": "earthquake", "severity": "moderate"}
    ]
    
    processing_times = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        start_time = time.time()
        
        test_data = {
            "type": "sensor",
            "content": {"sensor_type": "weather", "readings": {"temperature": 40}},
            "metadata": {"priority": scenario["severity"]},
            "latitude": 37.7749,
            "longitude": -122.4194,
            "region": f"Test Area {i}"
        }
        
        try:
            result = await process_emergency_event(test_data)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            print(f"   Scenario {i} ({scenario['type']}): {processing_time:.2f}s")
            
        except Exception as e:
            print(f"   Scenario {i} ({scenario['type']}): FAILED - {e}")
    
    if processing_times:
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)
        
        print(f"\n📊 Performance Summary:")
        print(f"   Average Processing Time: {avg_time:.2f}s")
        print(f"   Fastest Processing: {min_time:.2f}s")
        print(f"   Slowest Processing: {max_time:.2f}s")
        
        if avg_time < 5.0:
            print("   ✅ Performance: EXCELLENT")
        elif avg_time < 10.0:
            print("   ⚠️  Performance: GOOD")
        else:
            print("   ❌ Performance: NEEDS IMPROVEMENT")
    
    print()

if __name__ == "__main__":
    async def main():
        # Run system tests
        test_results = await test_system_components()
        
        # Run performance benchmark
        await run_performance_benchmark()
        
        # Save test results
        with open("test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        
        print(f"💾 Test results saved to test_results.json")
    
    asyncio.run(main())