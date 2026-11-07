---
title: "Connecting and Troubleshooting the Slack Integration"
category: "integration"
tags: ["slack", "integration", "webhook", "notifications", "oauth"]
summary: "Setup guide for the Slack integration, re-authorizing webhooks, and channel routing."
---

# Connecting and Troubleshooting the Slack Integration

The CloudDesk Slack app posts real-time alerts for ticket creation, customer replies, and critical escalations directly into your team channels.

## Troubleshooting Invalid Auth or Stopped Alerts
If notifications stop arriving or integration status displays `invalid_auth`:
1. **OAuth Token Expiration**: If a workspace admin who originally authorized the Slack app leaves your company or is deactivated in Slack, the OAuth access token becomes invalid.
2. **Re-Authorization**: Go to Settings -> Integrations -> Slack, click "Reconnect App", and re-authorize using an active workspace admin account.
3. **Channel Permissions**: Ensure the `@CloudDesk Bot` has been invited (`/invite @CloudDesk`) into private alert channels.

