---
title: "Storage Quotas, Trash Retention, and Space Management"
category: "storage_quota"
tags: ["storage", "quota", "uploads", "trash", "retention"]
summary: "How storage quotas are calculated, managing deleted file retention, and resolving upload errors."
---

# Storage Quotas, Trash Retention, and Space Management

CloudDesk workspaces have allocated disk storage quotas based on their active subscription plan.

## Storage Quotas by Plan
- **Free**: 10 GB total workspace storage
- **Pro**: 50 GB to 80 GB total workspace storage
- **Business**: 200 GB to 250 GB total workspace storage
- **Enterprise**: 1,000 GB+ with custom expansion packs

## Resolving Upload Errors (HTTP 403 Storage Quota Exceeded)
If file uploads fail with quota warnings despite deleting files:
1. **Empty the Trash**: Deleted files are moved to the workspace Trash folder and retained for 30 days before permanent purging. These files continue counting toward storage limits until the Trash is permanently emptied.
2. **Clear Video and Render Cache**: Cached export artifacts under Settings -> Storage can be cleared instantly.
3. **Upgrade Storage Plan**: Workspace owners can upgrade their subscription plan or add a 50GB storage expansion pack under Billing.

