# Official API/pricing sources consulted — 2026-11-11

These are documentation reads, not model calls or account-access verification. No pricing or availability claim is inferred from third-party pages.

- OpenAI GPT-5.4 mini ID/default snapshot, default reasoning, prices and supported endpoint: https://developers.openai.com/api/docs/models/gpt-5.4-mini.md — requested snapshot gpt-5.4-mini-2026-03-17; input $0.75/output $4.50 per million tokens.
- OpenAI Responses request/reference: https://developers.openai.com/api/reference/resources/responses/methods/create — system/user input and bounded generation, response identity/usage.
- Anthropic Claude Haiku 4.5 ID, availability and prices: https://platform.claude.com/docs/en/models/haiku-4-5/overview — claude-haiku-4-5-20251001; $1/$5 per million tokens. Listed legacy status; no claim of account access or perpetual availability.
- Anthropic Messages request/reference: https://platform.claude.com/docs/en/api/messages/create — stateless messages, top-level system, max_tokens and usage. The prepared adapter pins the established 2023-06-01 version for the legacy model/key interface rather than silently using a changed current API schema; account acceptance remains unverified and an error stops.
- xAI Grok 4.3 model/default reasoning: https://docs.x.ai/developers/models/grok-4.3 — grok-4.3, configurable reasoning, documented default low; mutable alias, returned ID saved.
- xAI pricing: https://docs.x.ai/developers/pricing — $1.25/$2.50 per million short-context tokens for Grok 4.3.
- xAI Responses request/reference: https://docs.x.ai/developers/rest-api-reference/inference/responses — system/user input, max_output_tokens, model and usage. Context here is below long-context thresholds; no tools enabled.

No live FX rate is claimed. The EUR budget reserves 1.50 EUR per USD including fees/tax effects and a separate 1.50 price cushion; those are explicit ceilings to be confirmed for the run, not financial forecasts. If actual account pricing, conversion/fees or generation-limit semantics are not covered, do not execute. The runner is not a remote billing authority.
