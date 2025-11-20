# AshborneSDK_v1

The AshborneSDK_v1 is a modular, production-grade AI Governance and Licensing SDK. It includes licensing enforcement, persona routing, output modulation, watermark verification, and infrastructure hooks. Designed for integration into AI applications and creator platforms.

## Features

- **License Enforcement**: Validate and manage license keys with support for multiple license types (Commercial, Personal, Educational, Trial, Enterprise)
- **Output Formatting**: Format and modulate AI-generated content with watermarking and content policy enforcement
- **Persona Routing**: Intelligent routing of requests to different AI personas based on context and user preferences
- **FastAPI Integration**: REST API with automatic Swagger/OpenAPI documentation
- **Extensible Architecture**: Modular design allows easy addition of custom engines and components
- **CLI Tools**: Builder PI scaffolding tool for rapid development

## Installation

### From Source

```bash
git clone https://github.com/ashbornemethod/AshborneSDK_v1.git
cd AshborneSDK_v1
pip install -r requirements.txt
```

### Using pip (Package)

```bash
pip install ashborne-sdk
```

### For Development

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
API_KEY=your-api-key-here
PORT=8000
LOG_LEVEL=INFO
WATERMARK_ENABLED=true
CONTENT_POLICY=moderate
ROUTING_STRATEGY=context_aware
```

### 2. Run the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

### 3. Use the SDK in Your Code

```python
from sdk import LicenseEnforcer, OutputFormatter, PersonaRouter

# Initialize components
license_enforcer = LicenseEnforcer()
output_formatter = OutputFormatter()
persona_router = PersonaRouter()

# Validate a license
result = license_enforcer.validate_license("your-license-key", "user-123")
print(result)

# Format output with watermarking
formatted = output_formatter.format_output(
    content="AI generated content",
    output_format=OutputFormat.MARKDOWN,
    metadata={"author": "AI"}
)

# Route to appropriate persona
routing = persona_router.route_request(
    content="Explain quantum computing",
    context={"domain": "technical"}
)
print(f"Routed to: {routing['persona']}")
```

## API Endpoints

### Health & Info
- `GET /` - Root endpoint (health check)
- `GET /health` - Health check
- `GET /version` - Get SDK version

### License Management
- `POST /license/validate` - Validate a license key
- `GET /license/info/{license_key}` - Get license information

### Output Formatting
- `POST /format` - Format AI-generated content with watermarking

### Persona Routing
- `POST /persona/route` - Route request to appropriate persona
- `GET /persona/list` - List available personas
- `GET /persona/stats` - Get routing statistics

## SDK Modules

### License Enforcer (`sdk/license_enforcer.py`)

Handles license validation and enforcement:

```python
from sdk import LicenseEnforcer

enforcer = LicenseEnforcer()

# Validate license
result = enforcer.validate_license("license-key", "user-id")

# Check feature access
has_access = enforcer.check_feature_access("license-key", "ai_generation")

# Get license info
info = enforcer.get_license_info("license-key")

# Revoke license
enforcer.revoke_license("license-key", "violation of terms")
```

### Output Formatter (`sdk/formatter.py`)

Formats and watermarks AI-generated content:

```python
from sdk import OutputFormatter
from sdk.formatter import OutputFormat

formatter = OutputFormatter({
    "watermark_enabled": True,
    "content_policy": "moderate"
})

# Format output
result = formatter.format_output(
    content="Your AI content",
    output_format=OutputFormat.JSON,
    metadata={"source": "AI Model"}
)

# Sanitize output
clean = formatter.sanitize_output(content)
```

### Persona Router (`sdk/persona_router.py`)

Routes requests to appropriate AI personas:

```python
from sdk import PersonaRouter

router = PersonaRouter({
    "routing_strategy": "context_aware"
})

# Route request
result = router.route_request(
    content="Write a technical document",
    context={"domain": "technical"},
    user_preferences={"preferred_persona": "professional"}
)

# List personas
personas = router.list_personas()

# Get routing stats
stats = router.get_routing_stats()
```

## Builder PI CLI Tool

The `builder_pi.py` script helps scaffold new engines and components:

### Create a New Engine

```bash
python builder_pi.py create-engine MyCustomEngine --description "My custom engine" --with-tests
```

### List Available Engines

```bash
python builder_pi.py list-engines
```

### Initialize a New Project

```bash
python builder_pi.py init-project --path ./my_new_project
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
```

### Linting

```bash
flake8 sdk/ main.py
```

### Type Checking

```bash
mypy sdk/
```

## Packaging and Publishing

### Build the Package

```bash
python setup.py sdist bdist_wheel
```

### Publish to PyPI

```bash
pip install twine
twine upload dist/*
```

## Project Structure

```
AshborneSDK_v1/
├── sdk/                          # Core SDK modules
│   ├── __init__.py              # Package initialization
│   ├── license_enforcer.py      # License validation & enforcement
│   ├── formatter.py             # Output formatting & watermarking
│   └── persona_router.py        # Persona routing logic
├── main.py                       # FastAPI application entrypoint
├── builder_pi.py                 # CLI scaffolding tool
├── setup.py                      # Package configuration
├── requirements.txt              # Python dependencies
├── .env.example                  # Example environment configuration
├── .gitignore                    # Git ignore rules
├── LICENSE                       # MIT License
└── README.md                     # This file
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | None (optional) |
| `HOST` | Server host address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WATERMARK_ENABLED` | Enable content watermarking | `true` |
| `CONTENT_POLICY` | Content filtering policy | `moderate` |
| `ROUTING_STRATEGY` | Persona routing strategy | `context_aware` |

### Content Policies

- **strict**: Strict content filtering with prohibited content removal
- **moderate**: Balanced filtering with basic sanitization
- **permissive**: Minimal filtering, maximum freedom

### Routing Strategies

- **context_aware**: Route based on comprehensive context analysis (recommended)
- **content_based**: Route based on content keywords and patterns
- **user_preference**: Route based on user-specified preferences
- **load_balanced**: Distribute requests evenly across personas

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:

- GitHub Issues: https://github.com/ashbornemethod/AshborneSDK_v1/issues
- Documentation: https://github.com/ashbornemethod/AshborneSDK_v1#readme

## Roadmap

- [ ] Integration with AWS services (S3, Lambda, DynamoDB)
- [ ] Advanced watermarking techniques (invisible, cryptographic)
- [ ] Machine learning-based persona routing
- [ ] Multi-language support
- [ ] Database persistence layer
- [ ] Advanced analytics and monitoring
- [ ] Plugin system for custom engines
- [ ] GraphQL API support

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

Built with ❤️ by the Ashborne Method team for the AI governance community.
