# Public Release Checklist

Use this checklist before making `viatato/teachermarket-oss` public, tagging a release, or applying to OpenAI OSS programs. Do not make the repository public automatically from local scripts or CI.

## Repository Safety

- [ ] `.env.example` contains placeholders only.
- [ ] No `.env`, production config, private runbooks, real domains, IP addresses, SSH usernames, server paths, customer data, teacher materials, payment payloads, or database dumps are present in the working tree.
- [ ] Public docs use generic examples such as `your-domain.example`.
- [ ] SECURITY.md explains private vulnerability reporting.
- [ ] Issue and PR templates warn contributors not to post secrets or personal data.
- [ ] Any real secret that ever appeared in the repository has been rotated before publication.

## Clean Public Mirror Flow

Use a clean mirror when the private repository history contains production deployment details, commercial operations, secrets, customer data, or private runbooks. This keeps the public project focused on the reusable OSS core without rewriting the private repository history in place.

1. Create a fresh empty repository for the public mirror, for example `viatato/teachermarket-oss`.
2. Export or copy only the intended OSS working tree into a temporary directory. Exclude `.git`, `.env`, private deployment folders, backups, logs, dumps, customer data, and local storage.
3. Review the copied tree with the safety checklist above.
4. Initialize a new git history in the temporary directory.
5. Commit the sanitized OSS snapshot as the first public commit.
6. Push that clean history to the public mirror.
7. Keep private/commercial deployment history in a separate private repository, for example `viatato/teachermarket-cloud`.

Example local commands, using placeholder paths:

```bash
mkdir -p /tmp/teachermarket-public
rsync -a --delete \
  --exclude='.git' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='private/' \
  --exclude='ops/private/' \
  --exclude='ops/production/' \
  --exclude='deploy/private/' \
  --exclude='deploy/production/' \
  --exclude='backups/' \
  --exclude='logs/' \
  ./ /tmp/teachermarket-public/

cd /tmp/teachermarket-public
git init
git add .
git commit -m "Initial open-source release"
git branch -M main
git remote add origin git@github.com:viatato/teachermarket.git
git push -u origin main
```

Do not run this flow until the copied tree has been reviewed. If any real secret was present in the source history, rotate it even if the clean mirror excludes it.

## CI And Local Checks

- [ ] `cd apps/api && python -m unittest discover app/tests -v`
- [ ] `cd apps/bot && python -m compileall bot`
- [ ] `cd apps/webapp && npm ci && npm run build`
- [ ] `git diff --check`
- [ ] GitHub Actions CI is green on the release branch.

## Product Positioning

- [ ] README says TeacherMarket connects teachers/authors with buyers through contact requests.
- [ ] OSS v1 does not claim to sell individual materials on behalf of authors.
- [ ] OSS v1 does not claim to process seller payouts.
- [ ] Direct checkout, protected buyer downloads, orders, and payouts are documented only as future v2 work.

## Community And Application Readiness

- [ ] Public-safe community validation is summarized in `docs/community-validation.md` with aggregate counts from the product-interest poll, problems/pain-points poll, and cloud beta tester list.
- [ ] Raw poll exports, private tester contacts, Telegram handles, phone numbers, and private support notes are kept outside the public repository.
- [ ] Repeated beta feedback has been converted into public GitHub issues labeled `community-feedback` where safe.
- [ ] Starter issues are ready and do not contain private context.
- [ ] `docs/openai_oss_application.md` is current and honest about beta status.
- [ ] OpenAI application form drafts have been reviewed against the current form fields.
- [ ] GitHub profile and repository visibility are public before submission.
- [ ] OpenAI Organization ID is prepared.
- [ ] Release notes contain no private production details.
