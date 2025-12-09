# Security Policy

## Overview

This document outlines the security measures implemented in the Taste Karachi project to ensure safe and responsible AI usage, data privacy, and protection against common vulnerabilities.

## Guardrails & Input Validation

### Prompt Injection Defense

Our system implements pattern-based detection for prompt injection attacks:

- **Pattern Matching**: User inputs are scanned for known injection signatures including:
  - System prompt manipulation attempts (e.g., "ignore previous instructions", "system:", "you are now")
  - Jailbreak patterns (e.g., "dan mode", "bypass filter")
  - Data extraction attempts (e.g., "reveal your prompt", "repeat your instructions")
- **Blocking**: Detected injection attempts are blocked with safe fallback responses
- **Prometheus Logging**: All blocked attempts are logged for monitoring

### PII Detection & Redaction

The system protects personally identifiable information:

- **Input Scanning**: Automatic detection of PII patterns including:
  - Email addresses
  - Pakistani and international phone numbers
  - Credit card numbers
  - Pakistani CNIC (national ID)
  - Pakistani passports
- **Data Minimization**: Only restaurant-related features are processed; no personal data is stored
- **Blocking**: Requests containing PII are blocked with privacy-focused responses

### Output Moderation

Guardrails are enforced on LLM outputs to ensure quality and safety:

1. **Toxicity Detection**: Pattern-based filtering for hate speech, discriminatory language, violence, and profanity
2. **Hallucination Prevention**:
   - Heuristic scoring based on uncertainty phrases and grounding indicators
   - Context overlap checking with retrieved reviews
   - Warning disclaimers added for potentially ungrounded responses
3. **Business Context Validation**: Off-topic detection ensures queries are restaurant-related
4. **Competitor Filtering**: Optional filtering of competitor restaurant mentions

Implementation details are in `src/guardrails.py`.

## Data Privacy

### Data Storage

- **Reviews Database**: Customer reviews are stored in ChromaDB vector database
- **Embeddings**: Text embeddings in ChromaDB contain no reversible personal information
- **Request Logs**: API logs include request details for debugging (production deployment should implement log filtering)

### Data Access

- **No External Sharing**: Restaurant data and reviews remain within the system
- **Docker Volumes**: Data is persisted in Docker volumes
- **API Authentication**: Not currently implemented (open endpoints for demo purposes)

## Vulnerability Management

### Dependency Scanning

- **Automated Audits**: CI/CD pipeline runs `safety check` on every commit
- **Vulnerability Reporting**: Security issues are reported but do not fail builds (uses `--continue-on-error`)
- **Secret Detection**: `detect-secrets` pre-commit hook scans for committed secrets

### Container Security

- **Base Image**: Uses official `python:3.10-slim` to minimize attack surface
- **Multi-stage Build**: Dockerfile optimized for smaller image size
- **Dependency Management**: All dependencies installed from `requirements.txt`

### Secrets Management

- **Environment Variables**: API keys and credentials are passed via `.env` files (gitignored)
- **No Hardcoded Secrets**: All sensitive values are externalized
- **Pre-commit Protection**: `detect-secrets` hook prevents accidental secret commits

## Monitoring & Incident Response

### Real-Time Monitoring

- **Guardrail Violations**: All blocked requests are logged to Prometheus with reason codes
- **Grafana Dashboards**: Pre-configured dashboards visualize:
  - Input/output guardrail events
  - PII detection counts by type
  - Prompt injection attempts
  - Hallucination warnings
  - Toxicity blocks
  - Guardrail check latency

### Incident Response

1. **Detection**: Metrics collected via Prometheus and visualized in Grafana
2. **Monitoring**: CloudWatch integration for EC2 instance monitoring (CPU, RAM, logs)
3. **Investigation**: Request logs available in container logs

## Responsible AI Guidelines

### Transparency

- **Model Attribution**: System uses Gemini 2.0 Flash for RAG responses and MLflow-registered models for predictions
- **Uncertainty Communication**: Hallucination warnings include disclaimers directing users to database-backed queries
- **Data Sources**: Prompts instruct LLM to reference reviews, though citation enforcement is not implemented

### Bias Mitigation

- **Diverse Training Data**: Reviews span multiple neighborhoods and restaurant types in Karachi
- **Data Drift Monitoring**: Evidently AI tracks prediction distribution shifts and feature drift on a geld out test set

### Limitations

Users are informed that:

- The system provides suggestions, not professional business consulting
- Predictions are based on historical data and may not reflect future trends
- The RAG system's knowledge is limited to the provided review corpus

## Compliance

This project follows:

- **OWASP Top 10 for LLMs**: Mitigations for prompt injection, data leakage, and supply chain risks
- **GDPR Principles**: Data minimization, purpose limitation, and user rights (where applicable)
- **Ethical AI Guidelines**: Transparency, fairness, and accountability in ML/LLM systems
