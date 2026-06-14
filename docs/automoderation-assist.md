# Optional Automoderation Assist

TeacherMarket may add an optional moderation assistant for product metadata and preview images. It must support human admins rather than replace them.

## Safety Contract

- Human admin approval remains required before a material is published.
- The feature is disabled by default.
- Private product files, buyer data, contact requests, Telegram `initData`, tokens, and payment data are never sent to an external model by default.
- A self-hoster must explicitly configure a provider and acknowledge its data-processing terms before external requests are enabled.
- Assistant output is advisory. It must not directly approve, reject, hide, suspend, or publish content.

## Proposed Scope

The first version may inspect:

- title, description, language, category, audience, and other submitted metadata;
- preview images selected by the author;
- deterministic signals such as missing fields, repeated text, suspicious links, or unsupported claims.

It should return structured findings:

```json
{
  "summary": "Short admin-facing summary",
  "flags": [
    {
      "code": "possible_personal_data",
      "severity": "review",
      "evidence": "Preview 2 may contain a phone number."
    }
  ],
  "provider": "configured-adapter",
  "policy_version": "v1"
}
```

The response should be stored separately from the product record and shown only to admins. Authors should receive the admin's moderation reason, not raw model reasoning or hidden policy prompts.

## Architecture

Use an adapter boundary such as:

```python
class ModerationAssistProvider(Protocol):
    async def analyze(self, request: ModerationAssistRequest) -> ModerationAssistResult:
        ...
```

Recommended implementations:

- `disabled`: default provider that performs no external processing;
- `rules`: local deterministic checks suitable for every self-hosted deployment;
- external providers: optional adapters maintained without embedded credentials.

Suggested configuration:

```text
MODERATION_ASSIST_PROVIDER=disabled
MODERATION_ASSIST_INCLUDE_PREVIEWS=false
MODERATION_ASSIST_RETENTION_DAYS=30
```

Provider credentials must use environment variables. Production validation should reject a selected external provider when its required credentials or privacy acknowledgement are missing.

## Data Minimization

1. Build the request from allow-listed metadata fields.
2. Remove direct contact details and storage keys where possible.
3. Do not include the main product file in the initial implementation.
4. Send previews only when the self-hoster explicitly enables that option.
5. Avoid retaining provider request/response bodies in general application logs.
6. Store only findings needed for admin review and delete them according to the configured retention period.

If previews can contain student names, faces, school details, or other personal data, self-hosters should leave preview analysis disabled unless they have a lawful basis and appropriate provider terms.

## Failure Behavior

- Provider timeout or outage must not block manual moderation.
- Invalid or unparseable output should be discarded and logged without private payloads.
- Low-confidence or conflicting findings should be labeled for review, never converted into an automatic rejection.
- Re-running analysis should create a new versioned result without silently changing the prior admin decision.

## Threats and Controls

- **Prompt injection in descriptions:** treat submitted content as data, require structured output, and never grant the provider tools or admin actions.
- **Sensitive-data disclosure:** allow-list fields, redact contacts, disable product-file upload, and document preview processing.
- **Biased or inconsistent flags:** keep human review, show concise evidence, and measure false positives before expanding scope.
- **Provider compromise or leakage:** minimize payloads, use short retention, rotate credentials, and support a local rules-only mode.
- **Automation bias:** label findings as assistant suggestions and require an explicit admin decision.

## Implementation Plan

1. Add the `disabled` and local `rules` adapters plus structured result schemas.
2. Add admin-only storage and UI for versioned findings.
3. Add explicit configuration and privacy documentation for preview processing.
4. Pilot on public-safe demo metadata and measure false positives.
5. Consider an external adapter only after the local workflow and deletion controls are verified.

No phase should make automoderation a release blocker or weaken the existing manual moderation path.
