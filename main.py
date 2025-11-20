"""
AshborneSDK - Main FastAPI Application

This is the main entrypoint for the Ashborne AI Governance SDK.
It provides REST API endpoints with Swagger documentation.
"""

import logging
import os
from typing import Dict, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from sdk import LicenseEnforcer, OutputFormatter, PersonaRouter
from sdk.license_enforcer import LicenseType
from sdk.formatter import OutputFormat

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ashborne_sdk.log")
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AshborneSDK API",
    description="Modular AI Governance and Licensing SDK with REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize SDK modules
license_enforcer = LicenseEnforcer()
output_formatter = OutputFormatter({
    "watermark_enabled": os.getenv("WATERMARK_ENABLED", "true").lower() == "true",
    "content_policy": os.getenv("CONTENT_POLICY", "moderate")
})
persona_router = PersonaRouter({
    "routing_strategy": os.getenv("ROUTING_STRATEGY", "context_aware")
})


# Request/Response Models
class LicenseValidationRequest(BaseModel):
    license_key: str = Field(..., description="License key to validate")
    user_id: str = Field(..., description="User ID requesting validation")


class LicenseValidationResponse(BaseModel):
    status: str
    valid: bool
    message: str
    license_type: Optional[str] = None
    features: Optional[list] = None
    expires_at: Optional[str] = None


class FormatRequest(BaseModel):
    content: Any = Field(..., description="Content to format")
    output_format: str = Field(default="text", description="Output format (text, json, markdown, html, xml)")
    metadata: Optional[Dict] = Field(default=None, description="Optional metadata")


class PersonaRoutingRequest(BaseModel):
    content: str = Field(..., description="Content to route")
    context: Optional[Dict] = Field(default=None, description="Context information")
    user_preferences: Optional[Dict] = Field(default=None, description="User preferences")


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


# Dependency for API key validation
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key from header."""
    expected_key = os.getenv("API_KEY")
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.post("/license/validate", response_model=LicenseValidationResponse)
async def validate_license(
    request: LicenseValidationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Validate a license key for a user.
    
    Args:
        request: License validation request
        api_key: API key from header
        
    Returns:
        License validation result
    """
    try:
        result = license_enforcer.validate_license(
            request.license_key,
            request.user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error validating license: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/license/info/{license_key}")
async def get_license_info(
    license_key: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get information about a license.
    
    Args:
        license_key: License key to query
        api_key: API key from header
        
    Returns:
        License information
    """
    try:
        info = license_enforcer.get_license_info(license_key)
        return info
    except Exception as e:
        logger.error(f"Error getting license info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/format")
async def format_output(
    request: FormatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Format AI-generated content with watermarking.
    
    Args:
        request: Format request
        api_key: API key from header
        
    Returns:
        Formatted output with metadata
    """
    try:
        # Validate output format
        valid_formats = ["text", "json", "markdown", "html", "xml"]
        if request.output_format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output format. Must be one of: {valid_formats}"
            )
        
        # Map string to OutputFormat enum
        format_map = {
            "text": OutputFormat.TEXT,
            "json": OutputFormat.JSON,
            "markdown": OutputFormat.MARKDOWN,
            "html": OutputFormat.HTML,
            "xml": OutputFormat.XML
        }
        
        result = output_formatter.format_output(
            request.content,
            format_map[request.output_format],
            request.metadata
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error formatting output: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/persona/route")
async def route_persona(
    request: PersonaRoutingRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Route a request to the appropriate AI persona.
    
    Args:
        request: Persona routing request
        api_key: API key from header
        
    Returns:
        Routing decision with persona information
    """
    try:
        result = persona_router.route_request(
            request.content,
            request.context,
            request.user_preferences
        )
        return result
    except Exception as e:
        logger.error(f"Error routing persona: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/persona/list")
async def list_personas(api_key: str = Depends(verify_api_key)):
    """
    List all available AI personas.
    
    Args:
        api_key: API key from header
        
    Returns:
        List of available personas
    """
    try:
        personas = persona_router.list_personas()
        return {"personas": personas}
    except Exception as e:
        logger.error(f"Error listing personas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/persona/stats")
async def get_persona_stats(api_key: str = Depends(verify_api_key)):
    """
    Get persona routing statistics.
    
    Args:
        api_key: API key from header
        
    Returns:
        Routing statistics
    """
    try:
        stats = persona_router.get_routing_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting persona stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/version")
async def get_version():
    """Get SDK version information."""
    return {
        "version": "1.0.0",
        "name": "AshborneSDK",
        "description": "Modular AI Governance and Licensing SDK"
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting AshborneSDK API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
