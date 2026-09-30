# Security

This gateway is designed to keep credentials outside source control.

- Store provider keys only in environment variables or Render secrets.
- Never commit .env files, API keys, tokens, cookies, or runtime databases.
- The gateway API key is supplied through ADMIN_API_KEY.
- Provider credentials are forwarded only to the selected upstream provider.
- Keep /admin/status protected with ADMIN_API_KEY in production.
- Review provider terms, quotas, and privacy policies before production use.
- Do not enable debug logging that prints authorization headers or request secrets.

The repository intentionally excludes runtime state, credential databases, generated caches, and local agent worktrees.
