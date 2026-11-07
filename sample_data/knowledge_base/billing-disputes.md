---
title: "Handling Billing Disputes, Unauthorized Charges, and Chargebacks"
category: "billing"
tags: ["billing", "disputes", "chargebacks", "unauthorized_charge", "escalation"]
summary: "Protocol for investigating disputed credit card charges, chargeback prevention, and immediate billing escalation."
---

# Handling Billing Disputes, Unauthorized Charges, and Chargebacks

Billing disputes and chargeback notices require urgent, dedicated handling by human billing specialists.

## Escalation Policy
When a customer disputes an invoice, claims an unauthorized credit card transaction, or threatens an institutional bank chargeback, the ticket must immediately transition to the `escalated` status and route to the Senior Billing Team. Automated refund tools cannot execute on disputed or flagged transactions.

## Investigation Steps
1. Review invoice payment gateway transaction IDs and IP origins in the Stripe/Braintree billing portal.
2. Cross-reference invoice items against active seat licenses and workspace additions during the billing period.
3. If fraudulent card usage is confirmed, freeze the payment method, reverse the charges through the payment gateway, and notify the cardholder.

