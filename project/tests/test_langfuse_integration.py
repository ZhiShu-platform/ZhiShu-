#!/usr/bin/env python3
"""
Test script for Langfuse integration in the Emergency Management System.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.core.langfuse_integration import langfuse_manager, is_langfuse_available
from src.agent.graph import EmergencyManagementGraph

async def test_langfuse_basic():
    """Test basic Langfuse functionality."""
    print("🧪 Testing basic Langfuse functionality...")
    
    # Check if Langfuse is available
    if not is_langfuse_available():
        print("❌ Langfuse not available. Please check your configuration.")
        return False
    
    print("✅ Langfuse is available")
    
    # Test trace creation
    try:
        trace = langfuse_manager.create_trace(
            name="test_emergency_workflow",
            session_id="test_session_123",
            user_id="test_user_456"
        )
        if trace:
            print(f"✅ Trace created successfully: {trace.id}")
        else:
            print("❌ Failed to create trace")
            return False
    except Exception as e:
        print(f"❌ Trace creation failed: {e}")
        return False
    
    # Test span logging
    try:
        langfuse_manager.log_span(
            trace_id=trace.id,
            name="test_span",
            input={"test_input": "hello"},
            output={"test_output": "world"},
            metadata={"test": True}
        )
        print("✅ Span logged successfully")
    except Exception as e:
        print(f"❌ Span logging failed: {e}")
        return False
    
    # Test generation logging
    try:
        langfuse_manager.log_generation(
            trace_id=trace.id,
            name="test_generation",
            model="test-model",
            prompt="Test prompt",
            completion="Test completion"
        )
        print("✅ Generation logged successfully")
    except Exception as e:
        print(f"❌ Generation logging failed: {e}")
        return False
    
    # Test flush
    try:
        langfuse_manager.flush()
        print("✅ Events flushed successfully")
    except Exception as e:
        print(f"❌ Flush failed: {e}")
        return False
    
    return True

async def test_emergency_workflow():
    """Test emergency workflow with Langfuse tracing."""
    print("\n🧪 Testing emergency workflow with Langfuse...")
    
    try:
        # Create workflow instance
        workflow = EmergencyManagementGraph()
        print("✅ Emergency workflow created")
        
        # Test input data
        test_input = {
            "session_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": "test_user",
            "content": {
                "user_prompt": "There's a flood warning in Beijing area"
            },
            "location": {
                "latitude": 39.9042,
                "longitude": 116.4074,
                "region": "Beijing"
            },
            "type": "emergency_alert"
        }
        
        print("✅ Test input prepared")
        
        # Execute workflow
        print("🔄 Executing emergency workflow...")
        result = await workflow.process_emergency(test_input)
        
        print("✅ Workflow executed successfully")
        print(f"📊 Result keys: {list(result.keys())}")
        
        # Check if Langfuse trace was created
        if 'langfuse_trace_id' in result:
            print(f"🔍 Langfuse trace ID: {result['langfuse_trace_id']}")
        else:
            print("⚠️ No Langfuse trace ID in result")
        
        return True
        
    except Exception as e:
        print(f"❌ Emergency workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_system_health():
    """Test system health check."""
    print("\n🧪 Testing system health check...")
    
    try:
        workflow = EmergencyManagementGraph()
        health = await workflow.get_system_health()
        
        print("✅ Health check completed")
        print(f"📊 Health status: {health['system_health']['overall_status']}")
        
        if 'langfuse_status' in health['system_health']:
            langfuse_status = health['system_health']['langfuse_status']
            print(f"🔍 Langfuse status: {langfuse_status}")
        else:
            print("⚠️ No Langfuse status in health check")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Langfuse integration tests...")
    print("=" * 50)
    
    # Test 1: Basic Langfuse functionality
    test1_result = await test_langfuse_basic()
    
    # Test 2: Emergency workflow
    test2_result = await test_emergency_workflow()
    
    # Test 3: System health
    test3_result = await test_system_health()
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"✅ Basic Langfuse: {'PASS' if test1_result else 'FAIL'}")
    print(f"✅ Emergency Workflow: {'PASS' if test2_result else 'FAIL'}")
    print(f"✅ System Health: {'PASS' if test3_result else 'FAIL'}")
    
    if all([test1_result, test2_result, test3_result]):
        print("\n🎉 All tests passed! Langfuse integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the configuration and dependencies.")
    
    # Cleanup
    if langfuse_manager.is_available():
        langfuse_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
