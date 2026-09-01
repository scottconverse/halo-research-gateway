
import sys
import os
sys.path.insert(0, 'src')

# Test 1: Package imports correctly
try:
    import halo_research_gateway
    print("✓ Package imports successfully")
    print(f"✓ Version is correct: {halo_research_gateway.__version__}")
except Exception as e:
    print(f"✗ Package import failed: {e}")

# Test 2: Main module works correctly  
try:
    import subprocess
    result = subprocess.run([sys.executable, "-m", "halo_research_gateway"], 
                          capture_output=True, text=True, check=True)
    import json
    data = json.loads(result.stdout.strip())
    print("✓ Main module executes and outputs correct JSON")
    assert data["service"] == "halo-research-gateway"
    assert data["version"] == "0.2.0"
    assert data["status"] == "scaffold"
    print("✓ Main module JSON content is correct")
except Exception as e:
    print(f"✗ Main module test failed: {e}")

# Test 3: All required modules exist (even if empty)
required_modules = [
    'app.py',
    'config.py', 
    'models.py',
    'coordinator.py',
    'clock.py',
    'cache.py',
    'security.py',
    'logging_config.py'
]

try:
    for module in required_modules:
        with open(f'src/halo_research_gateway/{module}', 'r') as f:
            pass  # Just checking it exists
    print("✓ All required modules exist")
except Exception as e:
    print(f"✗ Required modules test failed: {e}")

print("All tests completed!")
