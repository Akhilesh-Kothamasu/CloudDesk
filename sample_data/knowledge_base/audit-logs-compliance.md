---
title: "Compliance Auditing, Event Retention, and Log Export"
category: "account"
tags: ["account", "audit", "compliance", "soc2", "export"]
summary: "Understanding the CloudDesk audit logging architecture, actor tracking, and compliance exports."
---

# Compliance Auditing, Event Retention, and Log Export

To satisfy SOC 2 Type II, ISO 27001, and HIPAA compliance mandates, CloudDesk maintains an append-only audit log of all system mutations.

## Tracked Events
Every mutating API request writes an immutable record to the `audit_logs` table capturing:
- `actor`: User email, agent identifier, or background job ID
- `actor_type`: Classification (`user`, `agent`, or `system`)
- `action`: Specific mutation performed (e.g., `ticket_reply`, `refund_approved`, `role_changed`)
- `resource_type` and `resource_id`: The affected entity
- `details`: JSON payload of changed attributes (with sensitive credentials redacted)
- `request_id`: Tracing correlation identifier matching HTTP `X-Request-ID`

## Log Export and Retention
Enterprise organizations can stream audit events in real-time to Amazon S3, Datadog, or Splunk via configured webhook sinks in Workspace Settings -> Compliance.

