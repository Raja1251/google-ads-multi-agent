# Security Policy

## Reporting Security Issues

We take the security of this project and your advertising accounts seriously.

If you believe you have discovered a vulnerability, security flaw, or potential credential exposure risk in this repository, please do **NOT** open a public issue.

Instead, please send an email to the repository maintainers or contact through GitHub's Private Vulnerability Reporting feature under the **Security** tab of this repository.

Please include:
1. A clear description of the vulnerability.
2. Steps to reproduce the issue safely in an isolated environment.
3. The potential impact on users or advertising data.

We will review your submission promptly and coordinate a fix before any public announcement.

## API Credential Safety Guidelines

1. **Never commit live credentials**: The `google-ads.yaml` file is explicitly ignored in `.gitignore`. Use `google-ads.yaml.example` as a template only.
2. **Use least-privilege API tokens**: Only grant required scopes in Google Cloud Console.
3. **Task Scheduler Safety**: When scheduling automated audits on Windows or Linux, run scripts under a standard user account rather than elevated root/SYSTEM privileges.
