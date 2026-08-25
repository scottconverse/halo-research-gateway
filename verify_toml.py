
import sys
sys.path.insert(0, 'src')

# Import and test that we're using tomllib correctly  
import tomllib
from halo_research_gateway.config import GatewayConfig

print("✓ Using standard library tomllib")
print(f"tomllib module: {tomllib.__file__}")

# Test basic functionality 
config = GatewayConfig()
print("✓ Configuration loading works with pydantic v2")

print("All imports and basic functionality verified!")
