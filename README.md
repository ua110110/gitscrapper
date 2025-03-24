# GitHub Stargazers Scraper and Email Finder

A set of Python scripts to scrape GitHub stargazers from a repository and optionally find their email addresses through various GitHub data sources.

## Project Overview

This project consists of two main scripts:

1. **github_stargazers.py**: Scrapes GitHub stargazers' usernames and URLs from a repository
2. **github_emails.py**: Finds email addresses for GitHub users from various sources

### Process Flow

1. Use `github_stargazers.py` to gather all stargazers from a GitHub repository
2. Use `github_emails.py` to find email addresses for the collected users

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - requests
  - beautifulsoup4

## Installation

1. Clone this repository or download the script file.
2. Install the required Python packages:

```bash
pip install requests beautifulsoup4
```

## Usage

### Scraping Stargazers

```bash
python github_stargazers.py [repo_url] --output [output_file]
```

#### Arguments

- `repo_url`: The URL of the GitHub stargazers page (e.g., https://github.com/username/repo/stargazers)
- `--output` or `-o`: The name of the output CSV file (default: stargazers.csv)
- `--start` or `-s`: Page to start scraping from (default: 1)
- `--retries` or `-r`: Maximum number of retry attempts for failed requests (default: 3)

#### Examples

```bash
# Scrape stargazers from page 1
python github_stargazers.py https://github.com/browser-use/browser-use/stargazers

# Scrape stargazers starting from a specific page
python github_stargazers.py https://github.com/browser-use/browser-use/stargazers --start 3

# Scrape stargazers and save to a custom file
python github_stargazers.py https://github.com/browser-use/browser-use/stargazers --output browser_use_fans.csv
```

### Finding Email Addresses

Use the `github_emails.py` script to find email addresses for GitHub users from their profiles, commits, or events.

```bash
python github_emails.py --input [input_csv] --output [output_csv] --token [github_token]
```

#### Arguments

- `--input` or `-i`: CSV file containing GitHub usernames and URLs (default: complete_stargazers.csv)
- `--output` or `-o`: Output CSV file to save results (default: github_emails.csv)
- `--token` or `-t`: GitHub API token for authentication (highly recommended to avoid rate limits)
- `--delay` or `-d`: Delay between API requests in seconds (default: 1.0)
- `--max-retries` or `-r`: Maximum number of retry attempts for failed requests (default: 3)
- `--limit` or `-l`: Limit the number of users to process (useful for batch processing)
- `--skip` or `-s`: Skip the first N users from the input file (default: 0)
- `--resume`: Resume from where you left off, skipping already processed users

#### Examples

```bash
# Basic usage
python github_emails.py

# With GitHub token (recommended)
python github_emails.py --token YOUR_GITHUB_TOKEN

# Custom input and output files
python github_emails.py --input my_stargazers.csv --output my_emails.csv

# Adjust delay between requests
python github_emails.py --delay 2.0

# Process only the first 100 users
python github_emails.py --limit 100

# Skip the first 500 users
python github_emails.py --skip 500

# Process users in batches
python github_emails.py --skip 0 --limit 100
python github_emails.py --skip 100 --limit 100
python github_emails.py --skip 200 --limit 100

# Resume processing from where you left off
python github_emails.py --resume
```

#### Batch Processing Strategy

For large datasets, you can use one of these strategies:

1. **Sequential Batches**: Process users in batches of a specific size
   ```
   python github_emails.py --skip 0 --limit 100
   python github_emails.py --skip 100 --limit 100
   python github_emails.py --skip 200 --limit 100
   ```

2. **Resume-Based Processing**: Start processing and resume if interrupted
   ```
   python github_emails.py --resume
   ```

3. **Split Input File**: Split your stargazers CSV into smaller files and process each separately
   ```
   split -l 100 complete_stargazers.csv batch_
   python github_emails.py --input batch_aa --output emails_batch_aa.csv
   python github_emails.py --input batch_ab --output emails_batch_ab.csv
   ```

## GitHub API Rate Limits

The email finder script makes extensive use of the GitHub API, which has rate limits:

- **Unauthenticated requests**: 60 requests per hour
- **Authenticated requests**: 5,000 requests per hour

Due to these limits, it's highly recommended to use a GitHub personal access token when running the email finder script, especially on large datasets.

### How to Get a GitHub Personal Access Token

1. Go to your GitHub account settings
2. Click on "Developer settings" in the left sidebar
3. Select "Personal access tokens" → "Tokens (classic)"
4. Click "Generate new token" → "Generate new token (classic)"
5. Give your token a description (e.g., "GitHub Email Finder")
6. Select the following scopes:
   - `public_repo` (to access public repositories)
   - `read:user` (to read user profile data)
7. Click "Generate token"
8. Copy the generated token and use it with the `--token` parameter

**Note**: Keep your token secure! Don't share it or commit it to version control.

## How Email Finding Works

The email finder script tries multiple methods to find a user's email:

1. **Public Profile**: Checks if the user has made their email public on their GitHub profile
2. **Commit Data**: Examines the user's recent commits for email information
3. **Event History**: Looks through the user's public events for email data
4. **Patch Data**: As a fallback, tries to extract emails from commit patches

Note: Using a GitHub API token is highly recommended to avoid rate limiting.

## Output

### Stargazers Script
The script creates a CSV file with two columns:
- Username: The GitHub username of the stargazer
- GitHub URL: The URL to the stargazer's GitHub profile

### Email Finder Script
The script creates a CSV file with four columns:
- Username: The GitHub username of the user
- GitHub URL: The URL to the user's GitHub profile
- Email: The email address found (if any)
- Source: Where the email was found (Profile, Commit, Event, Patch, or None)

## Notes

- Both scripts use delays between requests to be respectful to GitHub's servers.
- If you encounter rate limiting, you might need to authenticate with GitHub API, increase the delay, or use a token.
- Processing a large number of users can take a significant amount of time, even with authentication.

## Ethical Considerations

When collecting and using email addresses:

1. **Respect Privacy**: Only use collected emails in accordance with privacy regulations (GDPR, CCPA, etc.)
2. **Avoid Spam**: Don't use the emails for unsolicited mass emails
3. **Secure Data**: Store collected emails securely and don't share them publicly
4. **Proper Disclosure**: When contacting people, disclose how you obtained their email
5. **Opt-out Option**: Always provide a way for people to opt out of communications

## Troubleshooting

- **Rate Limiting**: Increase delay between requests or use a GitHub token
- **No Emails Found**: Some users don't have public emails or haven't made commits
- **Script Crashes**: Use the `--resume` option to continue from where you left off
- **Empty Results**: Make sure your input CSV has the correct format (Username, GitHub URL) 