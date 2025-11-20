"""
License Enforcement Module

This module handles license validation, enforcement, and compliance
for AI models and content usage within the Ashborne ecosystem.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class LicenseType(Enum):
    """Supported license types"""
    COMMERCIAL = "commercial"
    PERSONAL = "personal"
    EDUCATIONAL = "educational"
    TRIAL = "trial"
    ENTERPRISE = "enterprise"


class LicenseStatus(Enum):
    """License validation statuses"""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    SUSPENDED = "suspended"


class LicenseEnforcer:
    """
    Enforces licensing rules and validates license keys for AI usage.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the License Enforcer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.cache = {}
        logger.info("LicenseEnforcer initialized")

    def validate_license(self, license_key: str, user_id: str) -> Dict:
        """
        Validate a license key for a specific user.

        Args:
            license_key: The license key to validate
            user_id: The user ID requesting validation

        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating license for user: {user_id}")

        # Check cache first
        cache_key = f"{license_key}:{user_id}"
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            # Simple cache return without expiry check for now
            logger.debug(f"Returning cached validation for {user_id}")
            return cached_result

        # Validate license key format
        if not self._validate_key_format(license_key):
            return {
                "status": LicenseStatus.INVALID.value,
                "valid": False,
                "message": "Invalid license key format",
                "user_id": user_id
            }

        # Perform license validation
        result = self._perform_validation(license_key, user_id)

        # Cache the result
        self.cache[cache_key] = result

        return result

    def _validate_key_format(self, license_key: str) -> bool:
        """
        Validate the format of a license key.

        Args:
            license_key: The key to validate

        Returns:
            True if valid format, False otherwise
        """
        # Basic format validation (can be enhanced)
        if not license_key or len(license_key) < 16:
            return False
        return True

    def _perform_validation(self, license_key: str, user_id: str) -> Dict:
        """
        Perform actual license validation logic.

        Args:
            license_key: The license key
            user_id: The user ID

        Returns:
            Validation result dictionary
        """
        # This is a placeholder - in production, this would check against a database
        # or external licensing service
        return {
            "status": LicenseStatus.VALID.value,
            "valid": True,
            "license_type": LicenseType.COMMERCIAL.value,
            "user_id": user_id,
            "expires_at": (datetime.now() + timedelta(days=365)).isoformat(),
            "features": ["ai_generation", "persona_routing", "watermarking"],
            "message": "License validated successfully"
        }

    def check_feature_access(self, license_key: str, feature: str) -> bool:
        """
        Check if a license allows access to a specific feature.

        Args:
            license_key: The license key
            feature: The feature to check

        Returns:
            True if feature is accessible, False otherwise
        """
        validation = self.validate_license(license_key, "system")
        if not validation.get("valid"):
            return False

        features = validation.get("features", [])
        return feature in features

    def get_license_info(self, license_key: str) -> Dict:
        """
        Get detailed information about a license.

        Args:
            license_key: The license key

        Returns:
            Dictionary containing license information
        """
        validation = self.validate_license(license_key, "system")
        return {
            "license_key": license_key[:8] + "****",  # Masked for security
            "status": validation.get("status"),
            "license_type": validation.get("license_type"),
            "expires_at": validation.get("expires_at"),
            "features": validation.get("features", [])
        }

    def revoke_license(self, license_key: str, reason: str) -> Dict:
        """
        Revoke a license.

        Args:
            license_key: The license key to revoke
            reason: Reason for revocation

        Returns:
            Dictionary containing revocation status
        """
        logger.warning(f"Revoking license: {license_key[:8]}**** - Reason: {reason}")

        # Clear from cache
        for key in list(self.cache.keys()):
            if key.startswith(license_key):
                del self.cache[key]

        return {
            "success": True,
            "message": f"License revoked: {reason}",
            "revoked_at": datetime.now().isoformat()
        }
