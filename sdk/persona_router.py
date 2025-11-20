"""
Persona Router Module

This module handles intelligent routing of requests to different AI personas
based on context, user preferences, and content requirements.
"""

import logging
from typing import Dict, Optional, List, Any
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class PersonaType(Enum):
    """Available AI persona types"""
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    ANALYTICAL = "analytical"


class RoutingStrategy(Enum):
    """Routing strategies for persona selection"""
    CONTENT_BASED = "content_based"
    USER_PREFERENCE = "user_preference"
    CONTEXT_AWARE = "context_aware"
    LOAD_BALANCED = "load_balanced"


@dataclass
class Persona:
    """Represents an AI persona configuration"""
    name: str
    persona_type: PersonaType
    description: str
    capabilities: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5


class PersonaRouter:
    """
    Routes requests to appropriate AI personas based on context and requirements.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Persona Router.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.personas = self._initialize_personas()
        self.routing_strategy = RoutingStrategy(
            self.config.get("routing_strategy", "context_aware")
        )
        self.request_history = []
        logger.info(f"PersonaRouter initialized with strategy: {self.routing_strategy.value}")

    def _initialize_personas(self) -> Dict[str, Persona]:
        """
        Initialize default personas.

        Returns:
            Dictionary of available personas
        """
        personas = {
            "professional": Persona(
                name="professional",
                persona_type=PersonaType.PROFESSIONAL,
                description="Professional and formal communication style",
                capabilities=["business_writing", "reports", "emails"],
                parameters={"temperature": 0.7, "formality": "high"}
            ),
            "creative": Persona(
                name="creative",
                persona_type=PersonaType.CREATIVE,
                description="Creative and imaginative content generation",
                capabilities=["storytelling", "creative_writing", "brainstorming"],
                parameters={"temperature": 0.9, "formality": "low"}
            ),
            "technical": Persona(
                name="technical",
                persona_type=PersonaType.TECHNICAL,
                description="Technical and precise explanations",
                capabilities=["coding", "documentation", "debugging"],
                parameters={"temperature": 0.5, "formality": "medium"}
            ),
            "casual": Persona(
                name="casual",
                persona_type=PersonaType.CASUAL,
                description="Casual and friendly conversation",
                capabilities=["chat", "general_conversation"],
                parameters={"temperature": 0.8, "formality": "low"}
            ),
            "educational": Persona(
                name="educational",
                persona_type=PersonaType.EDUCATIONAL,
                description="Educational and instructive content",
                capabilities=["teaching", "tutorials", "explanations"],
                parameters={"temperature": 0.6, "formality": "medium"}
            ),
            "analytical": Persona(
                name="analytical",
                persona_type=PersonaType.ANALYTICAL,
                description="Analytical and data-driven insights",
                capabilities=["analysis", "research", "data_interpretation"],
                parameters={"temperature": 0.4, "formality": "high"}
            )
        }

        # Load custom personas from config
        custom_personas = self.config.get("custom_personas", {})
        for name, config in custom_personas.items():
            personas[name] = Persona(
                name=name,
                persona_type=PersonaType(config.get("type", "casual")),
                description=config.get("description", ""),
                capabilities=config.get("capabilities", []),
                parameters=config.get("parameters", {})
            )

        return personas

    def route_request(
        self,
        content: str,
        context: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate persona.

        Args:
            content: The request content
            context: Optional context information
            user_preferences: Optional user preferences

        Returns:
            Dictionary containing routing decision and persona
        """
        logger.info("Routing request to appropriate persona")

        context = context or {}
        user_preferences = user_preferences or {}

        # Determine best persona based on strategy
        if self.routing_strategy == RoutingStrategy.USER_PREFERENCE:
            persona = self._route_by_user_preference(user_preferences)
        elif self.routing_strategy == RoutingStrategy.CONTENT_BASED:
            persona = self._route_by_content(content)
        elif self.routing_strategy == RoutingStrategy.LOAD_BALANCED:
            persona = self._route_load_balanced()
        else:  # CONTEXT_AWARE
            persona = self._route_context_aware(content, context, user_preferences)

        # Log routing decision
        self._log_routing(content, persona, context)

        return {
            "persona": persona.name,
            "persona_type": persona.persona_type.value,
            "description": persona.description,
            "parameters": persona.parameters,
            "routing_strategy": self.routing_strategy.value,
            "confidence": self._calculate_confidence(content, persona, context)
        }

    def _route_by_user_preference(self, user_preferences: Dict) -> Persona:
        """Route based on user preferences."""
        preferred_persona = user_preferences.get("preferred_persona", "casual")
        return self.personas.get(preferred_persona, self.personas["casual"])

    def _route_by_content(self, content: str) -> Persona:
        """Route based on content analysis."""
        content_lower = content.lower()

        # Simple keyword-based routing
        if any(word in content_lower for word in ["code", "function", "bug", "debug"]):
            return self.personas["technical"]
        elif any(word in content_lower for word in ["story", "imagine", "create"]):
            return self.personas["creative"]
        elif any(word in content_lower for word in ["analyze", "data", "metrics"]):
            return self.personas["analytical"]
        elif any(word in content_lower for word in ["learn", "teach", "explain"]):
            return self.personas["educational"]
        elif any(word in content_lower for word in ["business", "formal", "report"]):
            return self.personas["professional"]
        else:
            return self.personas["casual"]

    def _route_load_balanced(self) -> Persona:
        """Route based on load balancing."""
        # Simple round-robin for now
        # In production, this would consider actual load metrics
        persona_names = list(self.personas.keys())
        index = len(self.request_history) % len(persona_names)
        return self.personas[persona_names[index]]

    def _route_context_aware(
        self,
        content: str,
        context: Dict,
        user_preferences: Dict
    ) -> Persona:
        """
        Route based on comprehensive context analysis.

        Args:
            content: Request content
            context: Context information
            user_preferences: User preferences

        Returns:
            Selected persona
        """
        # Start with content-based routing
        persona = self._route_by_content(content)

        # Override with user preference if strongly indicated
        if user_preferences.get("preferred_persona"):
            preferred = user_preferences["preferred_persona"]
            if preferred in self.personas:
                persona = self.personas[preferred]

        # Consider context hints
        if context.get("domain"):
            domain = context["domain"]
            if domain == "technical":
                persona = self.personas["technical"]
            elif domain == "creative":
                persona = self.personas["creative"]

        return persona

    def _calculate_confidence(
        self,
        content: str,
        persona: Persona,
        context: Dict
    ) -> float:
        """
        Calculate confidence score for routing decision.

        Args:
            content: Request content
            persona: Selected persona
            context: Context information

        Returns:
            Confidence score between 0 and 1
        """
        # Placeholder confidence calculation
        # In production, this would use ML models or heuristics
        base_confidence = 0.7

        # Increase confidence if context domain matches persona type
        if context.get("domain") and context["domain"] == persona.persona_type.value:
            base_confidence += 0.2

        return min(base_confidence, 1.0)

    def _log_routing(self, content: str, persona: Persona, context: Dict):
        """Log routing decision for analytics."""
        log_entry = {
            "content_preview": content[:100],
            "persona": persona.name,
            "strategy": self.routing_strategy.value,
            "context": context
        }
        self.request_history.append(log_entry)
        logger.debug(f"Routed to persona: {persona.name}")

    def get_persona(self, persona_name: str) -> Optional[Persona]:
        """
        Get a specific persona by name.

        Args:
            persona_name: Name of the persona

        Returns:
            Persona object or None if not found
        """
        return self.personas.get(persona_name)

    def list_personas(self) -> List[Dict[str, Any]]:
        """
        List all available personas.

        Returns:
            List of persona information dictionaries
        """
        return [
            {
                "name": p.name,
                "type": p.persona_type.value,
                "description": p.description,
                "capabilities": p.capabilities
            }
            for p in self.personas.values()
        ]

    def add_persona(self, persona: Persona) -> bool:
        """
        Add a custom persona.

        Args:
            persona: Persona to add

        Returns:
            True if added successfully, False otherwise
        """
        if persona.name in self.personas:
            logger.warning(f"Persona {persona.name} already exists")
            return False

        self.personas[persona.name] = persona
        logger.info(f"Added custom persona: {persona.name}")
        return True

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics.

        Returns:
            Dictionary containing routing statistics
        """
        total_requests = len(self.request_history)
        if total_requests == 0:
            return {"total_requests": 0, "persona_usage": {}}

        persona_counts = {}
        for entry in self.request_history:
            persona = entry["persona"]
            persona_counts[persona] = persona_counts.get(persona, 0) + 1

        return {
            "total_requests": total_requests,
            "persona_usage": persona_counts,
            "strategy": self.routing_strategy.value
        }
