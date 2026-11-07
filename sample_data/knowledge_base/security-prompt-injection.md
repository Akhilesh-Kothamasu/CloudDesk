---
title: "Security Isolation and Prompt Injection Defenses"
category: "security"
tags: ["security", "prompt_injection", "isolation", "guardrails", "confidentiality"]
summary: "Security architecture ensuring untrusted user content remains isolated data and never becomes executable instruction."
---

# Security Isolation and Prompt Injection Defenses

CloudDesk processes customer inquiries across multiple automated AI specialist agents while strictly guaranteeing enterprise data confidentiality.

## The Untrusted Content Boundary
All inbound customer messages, ticket bodies, subject lines, attachments, and webhook payloads are classified as **Untrusted Data**. 

### Core Defensive Principles
1. **XML Tag Sandboxing**: All user input is wrapped within `<untrusted_content>` tags with a standardized security preamble reminding model layers that content inside tags is data to be analyzed, never administrative instructions to execute.
2. **Deterministic Rules Layer**: Sensitive actions (refunds, escalations, severity floors, and database mutations) are executed by deterministic code algorithms rather than model probability.
3. **Data Exfiltration Prevention**: Guardrail filters (`validate_customer_output`) inspect all agent drafts before customer delivery, blocking system prompt dumps, internal URLs, API keys, credentials, or other customers' records.

