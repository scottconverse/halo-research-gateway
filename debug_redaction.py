
import sys
sys.path.insert(0, 'src')
from halo_research_gateway.logging_config import redact_url

# Test the golden case from constraints
input_url = "https://u:p@h/x?api_key=AAA&q=ok#f"
result = redact_url(input_url)
print(f"Input:  {input_url}")
print(f"Output: {result}")

# Check if it matches expected forms 
expected_forms = [
    "https://h/x?api_key=%5BREDACTED%5D&q=ok",  # Using URL encoding 
    "https://h/x?api_key=[REDACTED]&q=ok"       # Using literal brackets
]

print(f"Matches expected forms: {result in expected_forms}")
