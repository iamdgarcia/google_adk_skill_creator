---
name: get-balance
description: "Use this skill when the user asks about their account balance, how much money they have, what their current balance is, or wants to check the funds in their account. Also use when the user asks to see all their accounts or list their accounts."
metadata:
  adk_additional_tools:
    - get_accounts
    - get_balance
---

# Get Balance

Help the user check their account balance.

## Instructions

1. If the user specifies which account they want to check, call `get_balance` with that account identifier directly.
2. If the user does NOT specify an account, first call `get_accounts` to retrieve the list of accounts, then present the list to the user and ask them to specify which account they want.
3. Once the user specifies an account, call `get_balance` with that account.
4. Present the balance clearly: include the account identifier and the balance amount with currency if available.
5. Never guess an account — always confirm with the user if there is ambiguity.
