---
title: "SSO and SAML 2.0 Troubleshooting Guide"
category: "login_issue"
tags: ["sso", "saml", "okta", "azure_ad", "login"]
summary: "Diagnostic procedures for SAML 2.0 and SSO login failures, certificate rotation, and IdP errors."
---

# SSO and SAML 2.0 Troubleshooting Guide

This guide covers diagnosing and resolving Single Sign-On (SSO) failures when using SAML 2.0 identity providers such as Okta, Azure Active Directory, and Google Workspace.

## Common Error Codes and Root Causes

### 1. 504 Gateway Timeout or Connection Timeouts
- **Cause**: Upstream Identity Provider (IdP) latency, network timeouts, or an active service outage on the SSO gateway.
- **Action**: Check `GET /incidents` to verify whether an active incident affects `sso-gateway` or `auth-service`. If an incident is active, advise the customer that engineering is actively mitigating the outage.

### 2. Invalid Signature or Expired Certificate
- **Cause**: The X.509 signing certificate in your identity provider has expired or does not match the certificate registered in CloudDesk workspace settings.
- **Action**: Rotate the certificate in your IdP metadata and upload the new public certificate in Workspace Settings -> Single Sign-On.

### 3. User Not Assigned (SAML Response code 400)
- **Cause**: The user attempting authentication has not been assigned to the CloudDesk enterprise application in your Okta or Azure AD console.
- **Action**: Enterprise administrators must add the user or security group to the CloudDesk app assignment policy.

