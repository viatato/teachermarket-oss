# Material Complaint Policy

This document is a public-safe baseline for TeacherMarket self-hosters. It describes how reports about catalog materials should be received, reviewed, and resolved without exposing reporters or private educational files.

## Scope

A signed-in user may report a published material when they believe it:

- violates copyright or another person's rights;
- contains harmful, deceptive, discriminatory, or unlawful content;
- is materially different from its title, description, or previews;
- exposes personal data;
- is spam or otherwise violates the host community's published rules.

TeacherMarket connects users with independent authors. A report is a request for review, not an automatic finding against the author.

## Current Workflow

1. A user submits one report per material with a free-text reason.
2. The report is stored with status `open`, and an audit event is created.
3. An admin reviews the report and the relevant catalog metadata, previews, and private file only when necessary.
4. The admin may moderate the material using the existing approve, reject, hide, restore, or request-changes controls.
5. The admin marks the report `resolved`; that action is also audited.

Submitting the same material again returns the existing report instead of creating duplicates.

## Privacy

- Reporter identity is available only to authenticated admin workflows and the reporter's own API response. It must not be shown to the author or published in issues, screenshots, or public logs.
- Report reasons may contain personal data. Treat them as private support content and avoid copying them into public trackers.
- Product files remain private. Review them through the admin-only download flow and do not attach paid or private materials to tickets.
- Tell authors only what they need to understand and correct a moderation decision. Do not disclose the reporter's identity or unrelated account information.
- Audit and application logs must not contain Telegram tokens, signed `initData`, payment secrets, storage credentials, or full private files.

Self-hosters should publish a retention period appropriate to their jurisdiction and delete report content when it is no longer needed for moderation, appeals, or legal obligations.

## Admin Decision Guide

- **No violation:** leave the material unchanged and resolve the report.
- **Correctable metadata or preview issue:** request changes or hide the material until corrected, then resolve the report.
- **Clear policy violation:** hide or reject the material, record a concise reason, then resolve the report.
- **Credible legal, safety, or personal-data concern:** restrict access promptly, preserve only necessary evidence, and escalate to the deployment owner or qualified adviser.
- **Unclear case:** keep the report open while gathering the minimum necessary evidence. Avoid irreversible action based only on an unverified allegation.

Where practical, self-hosters should offer authors a private appeal path. Appeals should be reviewed by an admin who can see the original moderation record.

## Operational Expectations

- Define a private support channel and an incident owner before inviting users.
- Review urgent safety or personal-data reports promptly. Publish realistic response targets for ordinary reports.
- Limit admin access to the smallest practical group.
- Back up the database, protect backups, and include report records in the deployment's retention policy.
- Use aggregated counts rather than report text or identities in public transparency updates.

## Known OSS v1 Limits

- Reports have only `open` and `resolved` states; there is no separate dismissed, appealed, or reopened state.
- Resolving a report does not automatically hide or restore a product. Product moderation remains an explicit admin action.
- Reporter and author notifications are not a guaranteed workflow.
- The system does not classify legal claims or replace qualified legal review.

These limits are intentional for the small OSS v1 core. Deployments needing formal case management should add it as a private or optional module without weakening reporter privacy.
