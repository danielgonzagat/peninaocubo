Security Policy

Supported Versions

- Actively maintained: main branch

Reporting a Vulnerability

- Please report vulnerabilities via GitHub Issues or contact the maintainers privately if sensitive.
- Do not open public issues with exploit details. We will coordinate disclosure and fixes.

Handling Secrets

- Never commit API keys or credentials. Pre-commit runs secrets scanning.
- Use environment variables as configured in `pyproject.toml` and `penin/config.py`.
