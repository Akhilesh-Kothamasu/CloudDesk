---
title: "Data Loss Prevention and Version History Recovery"
category: "other"
tags: ["data_loss", "recovery", "versions", "backups", "escalation"]
summary: "Procedures for investigating missing files, restoring snapshot backups, and data loss escalation."
---

# Data Loss Prevention and Version History Recovery

CloudDesk maintains continuous snapshot backups and object versioning across all cloud storage clusters.

## Investigating Missing or Disappeared Files
When files appear missing or deleted without team record:
1. **Check Workspace Audit Logs**: Navigate to `/audit` to verify whether automated retention policies, integration sync scripts, or team members deleted the assets.
2. **Version History Rollback**: CloudDesk stores object versions for 90 days on Pro plans and 365 days on Enterprise plans. You can restore previous folder snapshots via Workspace Settings -> Backups.
3. **Escalation Mandate**: Reports of unexplained data deletion or corruption are designated as Critical severity policy cases and automatically routed to the Core Storage Infrastructure team.

