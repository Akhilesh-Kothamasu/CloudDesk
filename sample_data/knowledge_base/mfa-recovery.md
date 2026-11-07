---
title: "MFA Account Lockout and Identity Recovery Procedure"
category: "login_issue"
tags: ["login_issue", "mfa", "totp", "lockout", "recovery"]
summary: "Steps to recover user accounts after failed multi-factor authentication attempts or lost TOTP devices."
---

# MFA Account Lockout and Identity Recovery Procedure

If a user loses access to their authenticator application (such as Google Authenticator or 1Password) or triggers an account lockout:

## Emergency Recovery Codes
When MFA is first configured, users are presented with 10 single-use emergency backup recovery codes.
1. On the MFA verification screen, click "Use Recovery Code".
2. Enter one of your saved 8-character emergency codes.
3. Once authenticated, go to Account Settings -> Security to re-bind your new authenticator device.

## Administrator Reset
If the user does not have access to their backup codes:
1. An organization Administrator can navigate to Settings -> Members.
2. Select the locked user's profile and click "Reset Multi-Factor Authentication".
3. The user receives a temporary cryptographic verification link via their registered email address to complete identity re-verification.

