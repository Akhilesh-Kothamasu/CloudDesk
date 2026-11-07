---
title: "Workspace Permissions, Role Hierarchy, and External Sharing"
category: "workspace_permissions"
tags: ["permissions", "roles", "external_sharing", "rbac", "guests"]
summary: "Guide to workspace permission levels, role hierarchy, and managing external guest access."
---

# Workspace Permissions, Role Hierarchy, and External Sharing

CloudDesk provides granular Role-Based Access Control (RBAC) to protect sensitive corporate assets.

## Role Hierarchy
- **Viewer (Rank 1)**: Read-only access to tickets, customers, knowledge articles, and dashboard metrics. Action buttons and mutation endpoints are disabled.
- **Agent / Editor (Rank 2)**: Full capability to run workflows, send customer responses, add internal messages, and request escalations.
- **Admin (Rank 3)**: Complete control over billing, security policies, workspace members, external sharing settings, and integrations.

## Enabling External Sharing
If guest link creation fails with policy restriction warnings:
1. Workspace Admin must open Settings -> Security & Permissions.
2. Toggle "Allow External Guest Links" to Enabled.
3. Optionally specify domain whitelist restrictions (e.g. `@partnercorp.com`).

