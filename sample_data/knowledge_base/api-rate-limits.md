---
title: "REST API Rate Limits, Quotas, and Backoff Handling"
category: "api_failure"
tags: ["api", "rate_limit", "429", "backoff", "headers"]
summary: "Understanding CloudDesk REST API per-minute limits, rate limit headers, and implementing exponential backoff."
---

# REST API Rate Limits, Quotas, and Backoff Handling

To ensure high availability and fair multi-tenant resource distribution, CloudDesk enforces rate limits on all REST API endpoints.

## Rate Limits by Subscription Tier
- **Free**: 60 requests per minute (rpm)
- **Pro**: 200 requests per minute (rpm)
- **Business**: 500 requests per minute (rpm)
- **Enterprise**: 1,000 to 2,000 requests per minute (rpm) (custom burst configurations available upon request)

## Response Headers
Every API response returns standard rate limiting headers:
- `X-RateLimit-Limit`: Maximum requests permitted in the sliding 60-second window.
- `X-RateLimit-Remaining`: Number of requests remaining in the current window.
- `X-RateLimit-Reset`: Unix epoch timestamp when quota resets.

## Handling HTTP 429 Too Many Requests
When client applications exceed rate limits, the gateway returns `HTTP 429 Too Many Requests` along with a `Retry-After` header. Clients must implement exponential backoff with full jitter to avoid synchronous burst stampedes.

