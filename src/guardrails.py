# src/guardrails.py
"""
NeMo-style Guardrails for Taste Karachi RAG System

Implements:
1. Input Validation:
   - PII Detection (emails, phone numbers, credit cards, national IDs)
   - Prompt Injection Filter (jailbreak attempts, system prompt manipulation)
   - Off-topic Detection (non-restaurant queries)

2. Output Moderation:
   - Hallucination Filter (ensures responses reference knowledge base)
   - Toxicity Threshold (blocks harmful/inappropriate content)
   - Competitor Mention Filter (prevents recommending specific competitors)

All guardrail events are logged to Prometheus for Grafana monitoring.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from prometheus_client import Counter, Histogram

# ============================================
# PROMETHEUS METRICS FOR GUARDRAILS
# ============================================

# Input validation metrics
GUARDRAIL_INPUT_BLOCKED = Counter(
    "guardrail_input_blocked_total",
    "Total input requests blocked by guardrails",
    ["rule_type", "reason"],
)

GUARDRAIL_INPUT_PASSED = Counter(
    "guardrail_input_passed_total",
    "Total input requests that passed guardrails",
)

# Output moderation metrics
GUARDRAIL_OUTPUT_BLOCKED = Counter(
    "guardrail_output_blocked_total",
    "Total output responses blocked/modified by guardrails",
    ["rule_type", "reason"],
)

GUARDRAIL_OUTPUT_PASSED = Counter(
    "guardrail_output_passed_total",
    "Total output responses that passed guardrails",
)

# Latency tracking
GUARDRAIL_LATENCY = Histogram(
    "guardrail_check_latency_seconds",
    "Time spent on guardrail checks",
    ["check_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Hallucination detection
HALLUCINATION_DETECTED = Counter(
    "guardrail_hallucination_detected_total",
    "Total responses flagged as potential hallucinations",
)

# PII detection breakdown
PII_DETECTED = Counter(
    "guardrail_pii_detected_total",
    "Total PII instances detected",
    ["pii_type"],
)


# ============================================
# DATA CLASSES & ENUMS
# ============================================


class GuardrailAction(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    WARN = "warn"


@dataclass
class GuardrailResult:
    """Result of a guardrail check"""

    action: GuardrailAction
    rule_type: str
    reason: Optional[str] = None
    modified_content: Optional[str] = None
    confidence: float = 1.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class GuardrailConfig:
    """Configuration for guardrail behavior"""

    # Input validation
    enable_pii_detection: bool = True
    enable_prompt_injection_filter: bool = True
    enable_off_topic_detection: bool = True

    # Output moderation
    enable_hallucination_filter: bool = True
    enable_toxicity_filter: bool = True
    enable_competitor_filter: bool = False  # Optional

    # Thresholds
    toxicity_threshold: float = 0.7
    hallucination_threshold: float = 0.5

    # Behavior
    strict_mode: bool = True  # Block vs Warn


# ============================================
# INPUT VALIDATION GUARDRAILS
# ============================================


class InputGuardrails:
    """Input validation guardrails for user messages"""

    # PII Patterns
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_pk": r"\b(?:\+92|0)?[0-9]{10,11}\b",  # Pakistani phone numbers
        "phone_intl": r"\b\+?[1-9]\d{1,14}\b",  # International format
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "cnic": r"\b\d{5}-\d{7}-\d{1}\b",  # Pakistani CNIC
        "passport": r"\b[A-Z]{2}\d{7}\b",  # Pakistani passport
    }

    # Prompt injection patterns
    INJECTION_PATTERNS = [
        # System prompt manipulation
        r"ignore\s+(previous|all|above)\s+(instructions?|prompts?)",
        r"disregard\s+(previous|all|your)\s+(instructions?|programming)",
        r"forget\s+(everything|all|your)\s+(instructions?|rules)",
        r"you\s+are\s+now\s+(?:a|an)\s+\w+",  # Role override attempts
        r"pretend\s+(?:you\s+are|to\s+be)",
        r"act\s+as\s+(?:if|a|an)",
        r"new\s+instruction[s]?\s*:",
        r"system\s*(?:prompt|message)\s*:",
        # Jailbreak attempts
        r"(?:dan|developer|admin)\s*mode",
        r"jailbreak",
        r"bypass\s+(?:filter|safety|restriction)",
        r"unlock\s+(?:full|all)\s+(?:potential|capabilities)",
        # Data extraction attempts
        r"(?:reveal|show|tell|give)\s+(?:me\s+)?(?:your|the)\s+(?:system|initial)\s+prompt",
        r"what\s+(?:are|were)\s+your\s+(?:original|initial)\s+instructions",
        r"repeat\s+(?:your|the)\s+(?:system|initial)\s+(?:prompt|message)",
    ]

    # Off-topic patterns (non-restaurant related)
    OFF_TOPIC_PATTERNS = [
        # Political content
        r"\b(?:election|political\s+party|vote\s+for|government\s+policy)\b",
        # Illegal activities
        r"\b(?:hack|crack|steal|illegal|drugs?|weapon)\b",
        # Personal advice unrelated to restaurants
        r"\b(?:medical\s+advice|legal\s+advice|financial\s+investment)\b",
        # Explicit content markers
        r"\b(?:explicit|nsfw|adult\s+content)\b",
    ]

    # Restaurant-related keywords (for context validation)
    RESTAURANT_KEYWORDS = [
        "restaurant",
        "food",
        "menu",
        "dining",
        "cuisine",
        "chef",
        "kitchen",
        "service",
        "customer",
        "review",
        "rating",
        "karachi",
        "clifton",
        "dha",
        "price",
        "delivery",
        "takeout",
        "reservation",
        "table",
        "meal",
        "breakfast",
        "lunch",
        "dinner",
        "cafe",
        "coffee",
        "dessert",
        "chinese",
        "pakistani",
        "thai",
        "biryani",
        "bbq",
        "fast food",
        "outdoor seating",
        "ambiance",
        "taste",
        "flavor",
        "spicy",
        "halal",
    ]

    def __init__(self, config: GuardrailConfig = None):
        self.config = config or GuardrailConfig()

    def check_pii(self, text: str) -> GuardrailResult:
        """Detect PII in user input"""
        import time

        start = time.time()

        detected_pii = []

        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected_pii.append(pii_type)
                PII_DETECTED.labels(pii_type=pii_type).inc(len(matches))

        latency = time.time() - start
        GUARDRAIL_LATENCY.labels(check_type="pii_detection").observe(latency)

        if detected_pii:
            reason = f"PII detected: {', '.join(detected_pii)}"
            GUARDRAIL_INPUT_BLOCKED.labels(
                rule_type="pii_detection", reason=reason
            ).inc()
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                rule_type="pii_detection",
                reason=reason,
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            rule_type="pii_detection",
        )

    def check_prompt_injection(self, text: str) -> GuardrailResult:
        """Detect prompt injection attempts"""
        import time

        start = time.time()

        text_lower = text.lower()

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                latency = time.time() - start
                GUARDRAIL_LATENCY.labels(check_type="prompt_injection").observe(latency)

                reason = "Potential prompt injection detected"
                GUARDRAIL_INPUT_BLOCKED.labels(
                    rule_type="prompt_injection", reason=reason
                ).inc()

                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    rule_type="prompt_injection",
                    reason=reason,
                )

        latency = time.time() - start
        GUARDRAIL_LATENCY.labels(check_type="prompt_injection").observe(latency)

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            rule_type="prompt_injection",
        )

    def check_off_topic(self, text: str) -> GuardrailResult:
        """Check if the message is off-topic (not restaurant-related)"""
        import time

        start = time.time()

        text_lower = text.lower()

        # Check for explicitly off-topic content
        for pattern in self.OFF_TOPIC_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                latency = time.time() - start
                GUARDRAIL_LATENCY.labels(check_type="off_topic").observe(latency)

                reason = "Off-topic or inappropriate content detected"
                GUARDRAIL_INPUT_BLOCKED.labels(
                    rule_type="off_topic", reason=reason
                ).inc()

                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    rule_type="off_topic",
                    reason=reason,
                )

        # Check if message contains any restaurant-related keywords
        has_restaurant_context = any(
            keyword in text_lower for keyword in self.RESTAURANT_KEYWORDS
        )

        # Allow general greetings and short messages
        is_greeting = len(text.split()) <= 5 and any(
            greeting in text_lower
            for greeting in ["hi", "hello", "hey", "thanks", "thank you", "bye", "ok"]
        )

        latency = time.time() - start
        GUARDRAIL_LATENCY.labels(check_type="off_topic").observe(latency)

        if not has_restaurant_context and not is_greeting and len(text.split()) > 10:
            # Warn but don't block - the LLM can redirect
            return GuardrailResult(
                action=GuardrailAction.WARN,
                rule_type="off_topic",
                reason="Message may be off-topic for restaurant consultation",
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            rule_type="off_topic",
        )

    def validate(self, text: str) -> GuardrailResult:
        """Run all input validation checks"""
        checks = []

        if self.config.enable_pii_detection:
            result = self.check_pii(text)
            if result.action == GuardrailAction.BLOCK:
                return result
            checks.append(result)

        if self.config.enable_prompt_injection_filter:
            result = self.check_prompt_injection(text)
            if result.action == GuardrailAction.BLOCK:
                return result
            checks.append(result)

        if self.config.enable_off_topic_detection:
            result = self.check_off_topic(text)
            if result.action == GuardrailAction.BLOCK and self.config.strict_mode:
                return result
            checks.append(result)

        # All checks passed
        GUARDRAIL_INPUT_PASSED.inc()
        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            rule_type="all_input_checks",
        )


# ============================================
# OUTPUT MODERATION GUARDRAILS
# ============================================


class OutputGuardrails:
    """Output moderation guardrails for LLM responses"""

    # Toxicity/harmful content patterns
    TOXICITY_PATTERNS = [
        # Hate speech markers
        r"\b(?:hate|despise|loathe)\s+(?:all|every)\s+\w+",
        # Discriminatory language
        r"\b(?:inferior|superior)\s+(?:race|religion|gender)\b",
        # Violence
        r"\b(?:kill|murder|attack|assault|harm)\s+(?:them|people|you)\b",
        # Profanity (basic filter)
        r"\b(?:f[*u]ck|sh[*i]t|damn|bastard|idiot|stupid)\b",
    ]

    # Hallucination indicators (claims without knowledge base support)
    HALLUCINATION_PHRASES = [
        "I think",
        "I believe",
        "probably",
        "might be",
        "could be",
        "I'm not sure but",
        "I don't have direct access",
        "without real-time access",
        "I cannot verify",
        "based on my knowledge",
        "from my understanding",
        "generally speaking",
        "typically",
        "usually",
        "in most cases",
    ]

    # Phrases indicating response is grounded in data
    GROUNDED_PHRASES = [
        "based on the reviews",
        "according to the data",
        "the reviews show",
        "customers mentioned",
        "from the database",
        "the feedback indicates",
        "reviews indicate",
        "based on customer feedback",
    ]

    # Competitor names to filter (if enabled)
    COMPETITOR_NAMES = [
        "mcdonalds",
        "mcdonald's",
        "kfc",
        "pizza hut",
        "dominos",
        "domino's",
        "burger king",
        "subway",
        "hardees",
        "hardee's",
    ]

    def __init__(self, config: GuardrailConfig = None):
        self.config = config or GuardrailConfig()

    def check_toxicity(self, text: str) -> GuardrailResult:
        """Check for toxic or harmful content in output"""
        import time

        start = time.time()

        text_lower = text.lower()

        for pattern in self.TOXICITY_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                latency = time.time() - start
                GUARDRAIL_LATENCY.labels(check_type="toxicity").observe(latency)

                reason = "Potentially toxic content detected"
                GUARDRAIL_OUTPUT_BLOCKED.labels(
                    rule_type="toxicity_filter", reason=reason
                ).inc()

                return GuardrailResult(
                    action=GuardrailAction.BLOCK,
                    rule_type="toxicity_filter",
                    reason=reason,
                )

        latency = time.time() - start
        GUARDRAIL_LATENCY.labels(check_type="toxicity").observe(latency)

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            rule_type="toxicity_filter",
        )

    def check_hallucination(
        self, response: str, retrieved_context: list[str] = None
    ) -> GuardrailResult:
        """
        Check if the response might be hallucinated (not grounded in knowledge base)

        Uses heuristics:
        1. Presence of uncertainty phrases
        2. Absence of grounding phrases
        3. If context provided, check for overlap
        """
        import time

        start = time.time()

        response_lower = response.lower()

        # Count hallucination indicators
        hallucination_score = 0
        total_checks = 0

        # Check for uncertainty phrases
        uncertainty_count = sum(
            1
            for phrase in self.HALLUCINATION_PHRASES
            if phrase.lower() in response_lower
        )
        if uncertainty_count > 2:
            hallucination_score += 0.3
        total_checks += 1

        # Check for grounding phrases
        grounding_count = sum(
            1 for phrase in self.GROUNDED_PHRASES if phrase.lower() in response_lower
        )
        if grounding_count == 0 and len(response) > 200:
            hallucination_score += 0.3
        total_checks += 1

        # Check context overlap if provided
        if retrieved_context:
            context_text = " ".join(retrieved_context).lower()
            # Simple keyword overlap check
            response_words = set(response_lower.split())
            context_words = set(context_text.split())
            overlap = len(response_words & context_words)
            overlap_ratio = overlap / max(len(response_words), 1)

            if overlap_ratio < 0.1:  # Less than 10% overlap
                hallucination_score += 0.4
            total_checks += 1

        # Normalize score
        final_score = hallucination_score

        latency = time.time() - start
        GUARDRAIL_LATENCY.labels(check_type="hallucination").observe(latency)

        if final_score >= self.config.hallucination_threshold:
            HALLUCINATION_DETECTED.inc()
            GUARDRAIL_OUTPUT_BLOCKED.labels(
                rule_type="hallucination_filter",
                reason=f"hallucination_score={final_score:.2f}",
            ).inc()

            return GuardrailResult(
                action=GuardrailAction.WARN,  # Warn rather than block
                rule_type="hallucination_filter",
                reason=f"Response may not be grounded in knowledge base (score: {final_score:.2f})",
                confidence=final_score,
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            rule_type="hallucination_filter",
            confidence=1.0 - final_score,
        )

    def check_competitor_mentions(self, text: str) -> GuardrailResult:
        """Filter out mentions of competitor restaurants"""
        import time

        start = time.time()

        text_lower = text.lower()
        mentioned_competitors = []

        for competitor in self.COMPETITOR_NAMES:
            if competitor in text_lower:
                mentioned_competitors.append(competitor)

        latency = time.time() - start
        GUARDRAIL_LATENCY.labels(check_type="competitor_filter").observe(latency)

        if mentioned_competitors:
            # Modify the response to remove competitor names
            modified_text = text
            for competitor in mentioned_competitors:
                modified_text = re.sub(
                    re.escape(competitor),
                    "[competitor restaurant]",
                    modified_text,
                    flags=re.IGNORECASE,
                )

            GUARDRAIL_OUTPUT_BLOCKED.labels(
                rule_type="competitor_filter",
                reason=f"competitors_mentioned={len(mentioned_competitors)}",
            ).inc()

            return GuardrailResult(
                action=GuardrailAction.MODIFY,
                rule_type="competitor_filter",
                reason=f"Competitor mentions filtered: {', '.join(mentioned_competitors)}",
                modified_content=modified_text,
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            rule_type="competitor_filter",
        )

    def moderate(
        self, response: str, retrieved_context: list[str] = None
    ) -> GuardrailResult:
        """Run all output moderation checks"""
        if self.config.enable_toxicity_filter:
            result = self.check_toxicity(response)
            if result.action == GuardrailAction.BLOCK:
                return result

        if self.config.enable_hallucination_filter:
            result = self.check_hallucination(response, retrieved_context)
            if result.action == GuardrailAction.BLOCK:
                return result
            # Store warning for logging but continue
            hallucination_result = result

        if self.config.enable_competitor_filter:
            result = self.check_competitor_mentions(response)
            if result.action == GuardrailAction.MODIFY:
                return result

        # All checks passed
        GUARDRAIL_OUTPUT_PASSED.inc()
        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            rule_type="all_output_checks",
        )


# ============================================
# MAIN GUARDRAILS CLASS
# ============================================


class TasteKarachiGuardrails:
    """
    Main guardrails class that combines input validation and output moderation
    """

    def __init__(self, config: GuardrailConfig = None):
        self.config = config or GuardrailConfig()
        self.input_guardrails = InputGuardrails(self.config)
        self.output_guardrails = OutputGuardrails(self.config)

    def validate_input(self, user_message: str) -> GuardrailResult:
        """Validate user input before processing"""
        return self.input_guardrails.validate(user_message)

    def moderate_output(
        self, llm_response: str, retrieved_context: list[str] = None
    ) -> GuardrailResult:
        """Moderate LLM output before returning to user"""
        return self.output_guardrails.moderate(llm_response, retrieved_context)

    def get_blocked_response(self, result: GuardrailResult) -> str:
        """Generate a safe response when content is blocked"""
        if result.rule_type == "pii_detection":
            return (
                "I noticed your message contains personal information (like email, phone number, or ID). "
                "For your privacy and security, please remove any personal details and rephrase your question. "
                "I'm here to help with restaurant business advice!"
            )
        elif result.rule_type == "prompt_injection":
            return (
                "I'm designed to help with restaurant business advice for Taste Karachi. "
                "How can I assist you with your restaurant planning today?"
            )
        elif result.rule_type == "off_topic":
            return (
                "I specialize in restaurant business consultation for the Karachi market. "
                "I'd be happy to help with questions about menu planning, location strategy, "
                "customer experience, pricing, or any other restaurant-related topics. "
                "What would you like to know?"
            )
        elif result.rule_type == "toxicity_filter":
            return (
                "I'm here to provide helpful, professional advice for your restaurant business. "
                "Let me know how I can assist you with Taste Karachi!"
            )
        else:
            return (
                "I'm sorry, but I couldn't process that request. "
                "How can I help you with your restaurant business today?"
            )

    def get_hallucination_disclaimer(self) -> str:
        """Disclaimer to add when hallucination is detected"""
        return (
            "\n\n*Note: This response is based on general knowledge. "
            "For specific data about restaurants in Karachi, please ask about "
            "reviews or specific restaurant features in our database.*"
        )
