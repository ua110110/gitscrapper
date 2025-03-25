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
- `--start` or `-s`: Starting position in the input file (1-indexed, default: 1)
- `--stop` or `-e`: Stopping position in the input file (useful for batch processing)
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

# Process users from position 1 to 100
python github_emails.py --start 1 --stop 100

# Process the next batch of 100 users
python github_emails.py --start 101 --stop 200

# Process a specific range of users
python github_emails.py --start 500 --stop 550

# Resume processing from where you left off
python github_emails.py --resume
```

#### Batch Processing Strategy

For large datasets, you can use one of these strategies:

1. **Sequential Ranges**: Process users in specific ranges
   ```
   python github_emails.py --start 1 --stop 100
   python github_emails.py --start 101 --stop 200
   python github_emails.py --start 201 --stop 300
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
The script creates a CSV file with the following columns:
- Username: The GitHub username of the user
- GitHub URL: The URL to the user's GitHub profile
- Email: The email address found (if any)
- Location: The user's location from their GitHub profile (if available)
- Organization: The user's company/organization from their GitHub profile (if available)
- Source: Where the email was found (Profile, Commit, Event, Patch, or None)

## Notes

- Both scripts use delays between requests to be respectful to GitHub's servers.
- If you encounter rate limiting, you might need to authenticate with GitHub API, increase the delay, or use a token.
- Processing a large number of users can take a significant amount of time, even with authentication.
- The email finder script will automatically append to an existing output file, so you can process users in batches without overwriting previous results.
- The script collects additional profile information (location and organization) when available.

## Ethical Considerations

When collecting and using email addresses:

1. **Respect Privacy**: Only use collected emails in accordance with privacy regulations (GDPR, CCPA, etc.)
2. **Avoid Spam**: Don't use the emails for unsolicited mass emails
3. **Secure Data**: Store collected emails securely and don't share them publicly
4. **Proper Disclosure**: When contacting people, disclose how you obtained their email
5. **Opt-out Option**: Always provide a way for people to opt out of communications

# Discord Message Fetcher

A Python script to fetch messages from Discord channels and extract user information.

## Features

- Fetch messages from Discord channels using the Discord API
- Bidirectional pagination to get messages before and after a reference point
- Extract user information from messages (usernames, IDs, avatars, etc.)
- Export user data to CSV files
- Export message data to JSON files
- Find messages from specific users

## Usage

### Discord Authentication

To use the Discord message fetcher, you need a Discord authentication token. This can be obtained from your Discord web client:

1. Open Discord in your web browser
2. Press F12 to open Developer Tools
3. Go to the Network tab
4. Perform an action (like sending a message)
5. Find a request to the Discord API
6. Look for the "authorization" header in the request headers
7. Copy the token value

**Note**: Treat your Discord token like a password. Never share it publicly or commit it to version control.

### Running the Script

```bash
python discord_dm.py
```

When running the script without arguments, you will be prompted to enter your Discord authentication token and other configuration options.

You can also provide command-line arguments:

```bash
python discord_dm.py --token YOUR_DISCORD_TOKEN --channel CHANNEL_ID --user USER_ID
```

#### Command-line Arguments

- `-t`, `--token`: Discord authorization token
- `-c`, `--channel`: Discord channel ID to fetch messages from (default: 1303749221354311752)
- `-u`, `--user`: Target user ID to focus on (leave empty for all users)
- `-r`, `--reference`: Reference message ID for bidirectional fetching
- `-b`, `--before`: Maximum messages to fetch before reference point (default: 250)
- `-a`, `--after`: Maximum messages to fetch after reference point (default: 250)
- `-o`, `--output-dir`: Directory to save output files (default: discord_output)

#### Examples

```bash
# Basic usage with token
python discord_dm.py --token YOUR_DISCORD_TOKEN

# Specify channel and target user
python discord_dm.py --token YOUR_DISCORD_TOKEN --channel 1234567890 --user 9876543210

# Fetch messages around a specific reference point
python discord_dm.py --token YOUR_DISCORD_TOKEN --reference 1122334455

# Customize message count limits
python discord_dm.py --token YOUR_DISCORD_TOKEN --before 500 --after 300

# Change output directory
python discord_dm.py --token YOUR_DISCORD_TOKEN --output-dir my_discord_data

python discord_dm.py --token YOUR_DISCORD_TOKEN --channel Channel_ID --before 17000 --output-dir discord_output
```

### Environment Variables

You can also set your Discord token as an environment variable:

```bash
export DISCORD_TOKEN="your_discord_token_here"
```

### Output

The script generates two output files:

1. A CSV file containing user information with the following fields:
   - id: Discord user ID
   - username: Discord username
   - global_name: Global display name
   - discriminator: User discriminator
   - avatar: Avatar hash
   - bot: Boolean indicating if the user is a bot

2. A JSON file containing all messages with their complete metadata

## Technical Details

The script uses Discord's snowflake IDs for pagination, allowing it to retrieve messages before and after specific points in the conversation. It also handles rate limiting by implementing delays between API requests.

## Troubleshooting

- **API Errors**: Ensure your Discord token is valid and has not expired
- **Rate Limiting**: The script includes delays to manage rate limits, but you may need to adjust these if you encounter issues
- **No Messages Found**: Verify that the channel ID is correct and accessible with your token

## Troubleshooting

- **Rate Limiting**: Increase delay between requests or use a GitHub token
- **No Emails Found**: Some users don't have public emails or haven't made commits
- **Script Crashes**: Use the `--resume` option to continue from where you left off
- **Empty Results**: Make sure your input CSV has the correct format (Username, GitHub URL) 