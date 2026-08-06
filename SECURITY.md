# Security policy

## Supported version

Security fixes are applied to the current `main` branch. The latest stable snapshot is identified by the most recent version tag.

## Reporting a vulnerability

Do not open a public issue containing credentials, account identifiers, exploit details or private Snowflake information. Use GitHub private vulnerability reporting when it is available for the repository. Otherwise, contact the repository owner privately through the contact method listed on the GitHub profile.

Include:

- the affected file or component;
- reproduction steps that do not expose real credentials;
- the expected and observed behaviour;
- the potential impact;
- any suggested remediation.

## Credential handling

The repository must never contain `.env`, `dbt/profiles.yml`, Snowflake passwords, private keys, account locators, personal screenshots or generated files containing connection details. Public screenshots must be cropped before commit.

## Dependency and code scanning

GitHub Dependabot tracks Python and GitHub Actions updates. Pull requests are checked by dependency review, and CodeQL scans Python changes on pushes, pull requests and a weekly schedule.
