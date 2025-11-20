#!/usr/bin/env python3
"""
Demo script for AshborneSDK

This script demonstrates the core functionality of the AshborneSDK modules.
"""

from sdk import LicenseEnforcer, OutputFormatter, PersonaRouter
from sdk.formatter import OutputFormat, ContentPolicy
from sdk.persona_router import RoutingStrategy

print("=" * 60)
print("AshborneSDK v1.0.0 - Demo")
print("=" * 60)

# 1. License Enforcement Demo
print("\n1. License Enforcement Demo")
print("-" * 60)

enforcer = LicenseEnforcer()

# Validate a license
print("Validating license key...")
result = enforcer.validate_license("demo-license-key-123456", "user-demo-001")
print(f"  Status: {result['status']}")
print(f"  Valid: {result['valid']}")
print(f"  Type: {result['license_type']}")
print(f"  Features: {', '.join(result['features'])}")
print(f"  Expires: {result['expires_at']}")

# Check feature access
print("\nChecking feature access...")
has_access = enforcer.check_feature_access("demo-license-key-123456", "ai_generation")
print(f"  Access to 'ai_generation': {has_access}")

# Get license info
print("\nGetting license info...")
info = enforcer.get_license_info("demo-license-key-123456")
print(f"  Masked Key: {info['license_key']}")
print(f"  Status: {info['status']}")

# 2. Output Formatting Demo
print("\n\n2. Output Formatting Demo")
print("-" * 60)

formatter = OutputFormatter({
    "watermark_enabled": True,
    "content_policy": "moderate"
})

# Format as JSON
print("Formatting output as JSON...")
content = "This is AI-generated content created by AshborneSDK."
result = formatter.format_output(
    content,
    OutputFormat.JSON,
    metadata={"model": "gpt-4", "user": "demo-user"}
)
print(f"  Format: {result['format']}")
print(f"  Watermarked: {result['watermarked']}")
print(f"  Timestamp: {result['timestamp']}")
print(f"  Content Preview: {result['content'][:50]}...")

# Format as Markdown
print("\nFormatting as Markdown...")
result_md = formatter.format_output(
    {"title": "Demo", "text": "AI content"},
    OutputFormat.MARKDOWN
)
print(f"  Format: {result_md['format']}")
print(f"  Content: {result_md['content'][:80]}...")

# 3. Persona Routing Demo
print("\n\n3. Persona Routing Demo")
print("-" * 60)

router = PersonaRouter({
    "routing_strategy": "context_aware"
})

# List available personas
print("Available personas:")
personas = router.list_personas()
for persona in personas[:3]:  # Show first 3
    print(f"  - {persona['name']}: {persona['description']}")
print(f"  ... and {len(personas) - 3} more")

# Route a technical request
print("\nRouting technical request...")
request = "Explain how to implement a REST API in Python"
result = router.route_request(
    request,
    context={"domain": "technical"}
)
print(f"  Content: '{request}'")
print(f"  Routed to: {result['persona']} ({result['persona_type']})")
print(f"  Description: {result['description']}")
print(f"  Confidence: {result['confidence']:.2%}")
print(f"  Parameters: temperature={result['parameters']['temperature']}, "
      f"formality={result['parameters']['formality']}")

# Route a creative request
print("\nRouting creative request...")
request2 = "Write a story about a robot learning to paint"
result2 = router.route_request(
    request2,
    context={}
)
print(f"  Content: '{request2}'")
print(f"  Routed to: {result2['persona']} ({result2['persona_type']})")
print(f"  Description: {result2['description']}")
print(f"  Confidence: {result2['confidence']:.2%}")

# Get routing statistics
print("\nRouting statistics:")
stats = router.get_routing_stats()
print(f"  Total requests: {stats['total_requests']}")
print(f"  Persona usage: {stats['persona_usage']}")

print("\n" + "=" * 60)
print("Demo completed successfully!")
print("=" * 60)
print("\nNext steps:")
print("  1. Run 'python main.py' to start the FastAPI server")
print("  2. Visit http://localhost:8000/docs for API documentation")
print("  3. Use 'python builder_pi.py create-engine' to add custom engines")
print()
