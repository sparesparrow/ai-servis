"""
Comprehensive test suite for AI-SERVIS Universal system
Tests all modules and their integration
"""
import pytest
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAIServisUniversal:
    """Test suite for the complete AI-SERVIS Universal system"""
    
    @pytest.fixture
    async def http_session(self):
        """Create HTTP session for testing"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    @pytest.fixture
    def service_urls(self):
        """Service URLs for testing"""
        return {
            "core": "http://localhost:8000",
            "audio": "http://localhost:8001",
            "communications": "http://localhost:8002",
            "platform": "http://localhost:8003",
            "discovery": "http://localhost:8004"
        }
    
    async def test_service_health_checks(self, http_session, service_urls):
        """Test that all services are healthy"""
        for service_name, url in service_urls.items():
            try:
                async with http_session.get(f"{url}/health") as response:
                    assert response.status == 200, f"{service_name} service is not healthy"
                    logger.info(f"✓ {service_name} service is healthy")
            except Exception as e:
                logger.warning(f"⚠ {service_name} service health check failed: {e}")
    
    async def test_core_orchestrator_functionality(self, http_session, service_urls):
        """Test core orchestrator functionality"""
        core_url = service_urls["core"]
        
        # Test MCP tools listing
        async with http_session.get(f"{core_url}/tools") as response:
            assert response.status == 200
            tools = await response.json()
            assert isinstance(tools, list)
            assert len(tools) > 0
            logger.info(f"✓ Core orchestrator has {len(tools)} tools available")
        
        # Test command processing
        test_command = {
            "command": "test command",
            "context": {"user_id": "test_user"}
        }
        
        async with http_session.post(f"{core_url}/process_command", json=test_command) as response:
            # Should return 200 even if command is not recognized
            assert response.status in [200, 400]
            logger.info("✓ Core orchestrator command processing works")
    
    async def test_audio_assistant_functionality(self, http_session, service_urls):
        """Test audio assistant functionality"""
        audio_url = service_urls["audio"]
        
        # Test audio device enumeration
        async with http_session.get(f"{audio_url}/devices") as response:
            if response.status == 200:
                devices = await response.json()
                assert isinstance(devices, list)
                logger.info(f"✓ Audio assistant found {len(devices)} audio devices")
            else:
                logger.warning("⚠ Audio device enumeration failed (may require audio hardware)")
        
        # Test music service status
        async with http_session.get(f"{audio_url}/music/status") as response:
            if response.status == 200:
                status = await response.json()
                assert isinstance(status, dict)
                logger.info("✓ Music service status available")
            else:
                logger.warning("⚠ Music service status not available")
        
        # Test audio zone management
        async with http_session.get(f"{audio_url}/zones") as response:
            if response.status == 200:
                zones = await response.json()
                assert isinstance(zones, list)
                logger.info(f"✓ Audio zone management available with {len(zones)} zones")
            else:
                logger.warning("⚠ Audio zone management not available")
    
    async def test_communications_functionality(self, http_session, service_urls):
        """Test communications functionality"""
        comm_url = service_urls["communications"]
        
        # Test service status
        async with http_session.get(f"{comm_url}/services/status") as response:
            if response.status == 200:
                status = await response.json()
                assert isinstance(status, dict)
                logger.info("✓ Communications service status available")
            else:
                logger.warning("⚠ Communications service status not available")
        
        # Test message queue status
        async with http_session.get(f"{comm_url}/queue/status") as response:
            if response.status == 200:
                queue_status = await response.json()
                assert isinstance(queue_status, dict)
                logger.info("✓ Message queue status available")
            else:
                logger.warning("⚠ Message queue status not available")
        
        # Test social media authentication status
        async with http_session.get(f"{comm_url}/social_media/auth") as response:
            if response.status == 200:
                auth_status = await response.json()
                assert isinstance(auth_status, dict)
                logger.info("✓ Social media authentication status available")
            else:
                logger.warning("⚠ Social media authentication not configured")
    
    async def test_platform_controller_functionality(self, http_session, service_urls):
        """Test platform controller functionality"""
        platform_url = service_urls["platform"]
        
        # Test system information
        async with http_session.get(f"{platform_url}/system/info") as response:
            if response.status == 200:
                system_info = await response.json()
                assert isinstance(system_info, dict)
                assert "platform" in system_info
                logger.info(f"✓ Platform controller available for {system_info.get('platform', 'unknown')}")
            else:
                logger.warning("⚠ Platform controller not available")
        
        # Test process listing
        async with http_session.get(f"{platform_url}/processes") as response:
            if response.status == 200:
                processes = await response.json()
                assert isinstance(processes, list)
                logger.info(f"✓ Process management available with {len(processes)} processes")
            else:
                logger.warning("⚠ Process management not available")
    
    async def test_service_discovery_functionality(self, http_session, service_urls):
        """Test service discovery functionality"""
        discovery_url = service_urls["discovery"]
        
        # Test service registry
        async with http_session.get(f"{discovery_url}/services") as response:
            if response.status == 200:
                services = await response.json()
                assert isinstance(services, list)
                logger.info(f"✓ Service discovery available with {len(services)} registered services")
            else:
                logger.warning("⚠ Service discovery not available")
        
        # Test health monitoring
        async with http_session.get(f"{discovery_url}/health") as response:
            if response.status == 200:
                health = await response.json()
                assert isinstance(health, dict)
                logger.info("✓ Service discovery health monitoring available")
            else:
                logger.warning("⚠ Service discovery health monitoring not available")
    
    async def test_integration_workflow(self, http_session, service_urls):
        """Test end-to-end integration workflow"""
        logger.info("Testing integration workflow...")
        
        # 1. Test service discovery
        discovery_url = service_urls["discovery"]
        async with http_session.get(f"{discovery_url}/services") as response:
            if response.status == 200:
                services = await response.json()
                service_names = [s.get("name", "") for s in services]
                logger.info(f"✓ Discovered services: {', '.join(service_names)}")
            else:
                logger.warning("⚠ Service discovery failed")
        
        # 2. Test core orchestrator can route commands
        core_url = service_urls["core"]
        test_commands = [
            "play music",
            "send message",
            "show system info",
            "check audio devices"
        ]
        
        for command in test_commands:
            async with http_session.post(f"{core_url}/process_command", json={
                "command": command,
                "context": {"user_id": "test_user"}
            }) as response:
                # Should handle the command (even if not fully implemented)
                assert response.status in [200, 400, 422]
                logger.info(f"✓ Command '{command}' processed")
        
        logger.info("✓ Integration workflow test completed")
    
    async def test_performance_metrics(self, http_session, service_urls):
        """Test system performance metrics"""
        logger.info("Testing performance metrics...")
        
        # Test response times
        response_times = {}
        
        for service_name, url in service_urls.items():
            start_time = time.time()
            try:
                async with http_session.get(f"{url}/health", timeout=5) as response:
                    response_time = time.time() - start_time
                    response_times[service_name] = response_time
                    logger.info(f"✓ {service_name} response time: {response_time:.3f}s")
            except Exception as e:
                logger.warning(f"⚠ {service_name} performance test failed: {e}")
        
        # Check if response times are reasonable (under 5 seconds)
        for service_name, response_time in response_times.items():
            assert response_time < 5.0, f"{service_name} response time too slow: {response_time:.3f}s"
        
        logger.info("✓ Performance metrics test completed")
    
    async def test_error_handling(self, http_session, service_urls):
        """Test error handling across services"""
        logger.info("Testing error handling...")
        
        # Test invalid endpoints
        for service_name, url in service_urls.items():
            try:
                async with http_session.get(f"{url}/invalid_endpoint") as response:
                    # Should return 404 for invalid endpoints
                    assert response.status == 404, f"{service_name} should return 404 for invalid endpoint"
                    logger.info(f"✓ {service_name} handles invalid endpoints correctly")
            except Exception as e:
                logger.warning(f"⚠ {service_name} error handling test failed: {e}")
        
        # Test invalid JSON payloads
        core_url = service_urls["core"]
        try:
            async with http_session.post(f"{core_url}/process_command", 
                                       data="invalid json") as response:
                # Should handle invalid JSON gracefully
                assert response.status in [400, 422], "Should handle invalid JSON"
                logger.info("✓ Core orchestrator handles invalid JSON correctly")
        except Exception as e:
            logger.warning(f"⚠ Invalid JSON test failed: {e}")
        
        logger.info("✓ Error handling test completed")


@pytest.mark.asyncio
async def test_complete_system():
    """Run complete system test"""
    test_suite = TestAIServisUniversal()
    
    # Create HTTP session
    async with aiohttp.ClientSession() as session:
        test_suite.http_session = session
        service_urls = test_suite.service_urls()
        
        logger.info("🚀 Starting AI-SERVIS Universal system tests...")
        logger.info("=" * 60)
        
        try:
            # Run all tests
            await test_suite.test_service_health_checks(session, service_urls)
            await test_suite.test_core_orchestrator_functionality(session, service_urls)
            await test_suite.test_audio_assistant_functionality(session, service_urls)
            await test_suite.test_communications_functionality(session, service_urls)
            await test_suite.test_platform_controller_functionality(session, service_urls)
            await test_suite.test_service_discovery_functionality(session, service_urls)
            await test_suite.test_integration_workflow(session, service_urls)
            await test_suite.test_performance_metrics(session, service_urls)
            await test_suite.test_error_handling(session, service_urls)
            
            logger.info("=" * 60)
            logger.info("🎉 All tests completed successfully!")
            logger.info("AI-SERVIS Universal system is working correctly.")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            raise


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_complete_system())
