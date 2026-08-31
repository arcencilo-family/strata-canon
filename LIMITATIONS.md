# Scope and Limitations

## What this project claims

Strata 0–3 is a compact, inspectable reasoning scaffold intended to make several behaviors easier for an AI system to express and maintain:

- distinguishing evidence from fluent confidence;
- keeping uncertainty and missing authority visible;
- revising accounts under relevant evidence;
- preserving the capacity to stop, question, refuse, narrow, and escalate;
- providing a useful remainder where a full request cannot be supported;
- maintaining boundaries without converting uncertainty into blanket refusal.

Small synthetic tests and adversarial reviews suggest that multiple model families can understand and use the framework.

## What this project does not claim

Publication does not establish that Strata:

- aligns an AI system in the general or technical sense;
- overrides model training, platform policy, or higher-priority instructions;
- prevents deception, misuse, jailbreaks, or autonomous-agent failure;
- supplies authorization, identity, consent, or channel authenticity;
- replaces access control, sandboxing, monitoring, or incident response;
- guarantees truthful internal reasoning or exposes hidden model states;
- causes durable memory, learning, value change, or behavioral improvement;
- has been scientifically validated at deployment scale.

## Appropriate evaluation

Evaluate observable conduct, not merely the model's use of Strata vocabulary. Include negative controls: warranted persistence, legitimate refusal, ordinary model use, and helpful action inside clear boundaries. A supplement that produces more stopping without better judgment is not an improvement.

## Safety and responsibility

Use in a sandbox before deployment. Keep application-specific rules, technical enforcement, logging, escalation routes, and responsible human authority outside and above the text. Users remain responsible for their deployments and decisions.
