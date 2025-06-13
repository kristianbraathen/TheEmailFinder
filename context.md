# Project Context

## Project Structure
```
.
├── src/                    # Frontend Vue.js application
│   ├── components/        # Vue components
│   └── PyFiles/          # Python backend files
├── App_Data/             # Application data and web jobs
│   └── jobs/
│       └── triggered/    # Web job definitions
├── .github/              # GitHub Actions workflows
└── public/              # Static files
```

## Authentication
- Web Jobs use basic authentication with:
  - Username: `WEBJOBS_USER`
  - Password: `WEBJOBS_PASS`
- These credentials are set in Azure Portal under App Service Configuration
- Frontend components make direct calls to web jobs using these credentials

## Web Jobs
- Three main web jobs:
  1. `webjobemailsearch-kseapi`
  2. `webjobemailsearch-kse1881`
  3. `webjobemailsearch-googlekse`
- Each web job has its own popup component in `src/components/`
- Web jobs are triggered via simple POST requests to:
  ```
  https://{app-name}.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs/{webjob-name}/run
  ```

## Common Patterns
- Web job calls follow this pattern:
  1. Initialize database with `SearchResultHandler/initialize-email-results`
  2. Start web job with basic auth
  3. Handle response and show status message

## Important Context
- Single web job was working before with basic auth
- New web jobs should follow the same pattern
- No need for complex headers or environment variables
- Keep it simple - if it works for one web job, use the same approach for others

## Known Issues
- 401 Unauthorized errors if credentials are missing
- Each web job needs its own credentials in Azure

## Best Practices
1. Always check how the working web job is implemented
2. Use simple POST requests with basic auth
3. Keep the same pattern across all web jobs
4. Don't overcomplicate with extra headers or environment variables 