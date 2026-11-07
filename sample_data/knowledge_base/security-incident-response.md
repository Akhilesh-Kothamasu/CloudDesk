---
title: "Security Incident Response and Account Compromise Protocol"
category: "security"
tags: ["security", "breach", "escalation", "compromise", "sessions"]
summary: "Protocol for handling suspected unauthorized account access, credential compromise, and immediate escalation."
---

# Security Incident Response and Account Compromise Protocol

Customer security is the highest operational priority for CloudDesk.

## Mandatory Policy Escalation
Any report indicating unauthorized account access, suspicious login activity from foreign IP addresses, or potential data exfiltration **must be escalated immediately** to the Security Incident Response Team (SIRT). Under CloudDesk safety policy, automated agents are strictly forbidden from closing or resolving security tickets without human security engineer review.

## Immediate Containment Actions
1. **Revoke Active Sessions**: Under Workspace Settings -> Security, administrators can terminate all active JWT sessions and refresh tokens across all devices.
2. **Rotate API Keys**: Invalidate all production and staging API keys associated with the workspace.
3. **Enforce Global MFA**: Require multi-factor authentication on next login for all organization accounts.

