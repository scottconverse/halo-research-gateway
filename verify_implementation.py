
import sys
sys.path.insert(0, 'src')

from halo_research_gateway.logging_config import redact_url

# Test the exact golden case from constraints  
input_url = "https://u:p@h/x?api_key=AAA&q=ok#f"
result = redact_url(input_url)

print("Golden case verification:")
print(f"Input:  {input_url}")
print(f"Output: {result}")

# Check that it's one of the two expected forms (both are acceptable)
expected_forms = [
    "https://h/x?api_key=%5BREDACTED%5D&q=ok",
    "https://h/x?api_key=[REDACTED]&q=ok"
]

if result in expected_forms:
    print("✓ Matches expected golden case form")
else:
    print("✗ Does not match expected forms")

print("\nTesting sensitive parameter redaction:")
# Test that we handle sensitive parameters correctly
test_cases = [
    ("https://s3.amazonaws.com/bucket?X-Amz-Signature=abc123&other=value", "https://s3.amazonaws.com/bucket?X-Amz-Signature=%5BREDACTED%5D&other=value"),
    ("https://api.example.com/endpoint?sig=secret123&other=value", "https://api.example.com/endpoint?sig=%5BREDACTED%5D&other=value")
]

for input_url, expected in test_cases:
    result = redact_url(input_url)
    if result == expected:
        print(f"✓ Match: {input_url}")
    else:
        print(f"✗ Mismatch: {input_url}")
        print(f"  Expected: {expected}")  
        print(f"  Got:      {result}")
