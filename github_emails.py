#!/usr/bin/env python3

import csv
import time
import os
import re
import requests
import argparse
from datetime import datetime

class GithubEmailFinder:
    def __init__(self, input_file, output_file, token=None, delay=1, max_retries=3,
                 start=1, stop=None, resume=False):
        """
        Initialize the GitHub email finder.
        
        Args:
            input_file (str): CSV file containing GitHub usernames and URLs
            output_file (str): Output CSV file to save results
            token (str): GitHub API token for authenticated requests
            delay (float): Delay between API requests to avoid rate limiting
            max_retries (int): Maximum number of retry attempts for failed requests
            start (int): Starting position (1-indexed) in the input file
            stop (int): Stopping position in the input file (None for all)
            resume (bool): Whether to resume from where we left off
        """
        self.input_file = input_file
        self.output_file = output_file
        self.delay = delay
        self.max_retries = max_retries
        self.start = max(1, start)  # Ensure start is at least 1
        self.stop = stop
        self.resume = resume
        
        # Set up GitHub API headers
        self.headers = {
            'User-Agent': 'GitHub-Email-Finder-Script',
            'Accept': 'application/vnd.github.v3+json',
        }
        
        if token:
            self.headers['Authorization'] = f'token {token}'
            print("Using authenticated GitHub API requests")
        else:
            print("WARNING: Using unauthenticated GitHub API requests. Rate limits will be stricter.")
            print("Consider providing a GitHub token with --token for better results.")
        
        # Statistics
        self.stats = {
            'total_users': 0,
            'emails_found': 0,
            'profile_emails': 0,
            'commit_emails': 0,
            'event_emails': 0,
            'no_email': 0,
            'api_errors': 0,
            'skipped': 0
        }
    
    def api_request(self, url):
        """Make a request to the GitHub API with retries."""
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(url, headers=self.headers)
                
                # Check for rate limiting
                remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
                if remaining < 5:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    sleep_time = max(reset_time - time.time(), 0) + 10
                    print(f"Rate limit nearly exhausted. Sleeping for {sleep_time:.0f} seconds until reset.")
                    time.sleep(sleep_time)
                elif remaining < 20:
                    # Add additional delay when approaching limit
                    print(f"Rate limit getting low: {remaining} requests remaining. Adding extra delay.")
                    time.sleep(self.delay * 2)
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                retries += 1
                if response.status_code == 404:
                    # Not found, no need to retry
                    print(f"Resource not found: {url}")
                    return None
                
                if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
                    # Handle rate limiting
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    sleep_time = max(reset_time - time.time(), 0) + 10
                    print(f"Rate limit exceeded. Sleeping for {sleep_time:.0f} seconds.")
                    time.sleep(sleep_time)
                else:
                    wait_time = self.delay * (2 ** retries)
                    print(f"Error accessing {url}: {e}. Retrying in {wait_time:.1f}s ({retries}/{self.max_retries})")
                    time.sleep(wait_time)
            
        self.stats['api_errors'] += 1
        print(f"Failed to access {url} after {self.max_retries} attempts")
        return None
    
    def get_profile_email(self, username):
        """Try to get email from a user's GitHub profile."""
        user_data = self.api_request(f"https://api.github.com/users/{username}")
        if not user_data:
            return None, None, None
        
        # Check for public email in profile
        email = user_data.get('email')
        # Get additional profile information
        location = user_data.get('location', '')
        company = user_data.get('company', '')
        
        if email:
            self.stats['profile_emails'] += 1
            
        return email, location, company
    
    def get_commit_emails(self, username, max_repos=10, max_commits=100):
        """Try to find email from a user's recent commits."""
        # Get user's repositories
        repos_data = self.api_request(f"https://api.github.com/users/{username}/repos?sort=updated&per_page={max_repos}")
        if not repos_data:
            return None
        
        for repo in repos_data:
            repo_name = repo['name']
            repo_owner = repo['owner']['login']
            
            # Only look at their own repos, not forks
            if repo_owner != username:
                continue
                
            # Get recent commits by the user
            commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits?author={username}&per_page={max_commits}"
            commits_data = self.api_request(commits_url)
            if not commits_data:
                continue
            
            for commit in commits_data:
                if isinstance(commit, dict) and 'commit' in commit:
                    # Extract email from commit
                    author = commit['commit'].get('author', {})
                    email = author.get('email')
                    if email and not email.endswith(('.noreply.github.com', 'users.noreply.github.com')):
                        self.stats['commit_emails'] += 1
                        return email
            
            # Add a slight delay between repo checks
            time.sleep(self.delay)
        
        return None
    
    def get_event_emails(self, username, max_events=30):
        """Try to find email from a user's public events."""
        events_data = self.api_request(f"https://api.github.com/users/{username}/events/public?per_page={max_events}")
        if not events_data:
            return None
        
        for event in events_data:
            # Check for push events which might contain commit information
            if event['type'] == 'PushEvent' and 'payload' in event:
                commits = event['payload'].get('commits', [])
                for commit in commits:
                    author = commit.get('author', {})
                    email = author.get('email')
                    if email and not email.endswith(('.noreply.github.com', 'users.noreply.github.com')):
                        self.stats['event_emails'] += 1
                        return email
        
        return None
    
    def extract_patch_email(self, username):
        """
        Extract email from the commit patches of a user.
        This is a fallback method that directly parses patch data from multiple repositories.
        """
        try:
            # Get user's repositories
            response = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15", 
                                     headers=self.headers)
            repos = response.json()
            
            for repo in repos:
                if not isinstance(repo, dict):
                    continue
                    
                repo_name = repo.get('name')
                if not repo_name:
                    continue
                
                # Try to get recent commits first
                commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits?author={username}&per_page=10"
                commits_response = self.api_request(commits_url)
                
                if not commits_response:
                    # Try HEAD patch as fallback
                    patch_url = f"https://github.com/{username}/{repo_name}/commit/HEAD.patch"
                    patch_response = requests.get(patch_url)
                    
                    if patch_response.status_code == 200:
                        # Extract email with regex
                        email_matches = re.findall(r'<([^<>@\s]+@[^<>\s]+)>', patch_response.text)
                        for email in email_matches:
                            if email and not email.endswith(('.noreply.github.com', 'users.noreply.github.com')):
                                return email
                else:
                    # Try to get patches for specific commits
                    for commit in commits_response:
                        if not isinstance(commit, dict) or 'sha' not in commit:
                            continue
                            
                        sha = commit['sha']
                        patch_url = f"https://github.com/{username}/{repo_name}/commit/{sha}.patch"
                        patch_response = requests.get(patch_url)
                        
                        if patch_response.status_code == 200:
                            # Extract email with regex
                            email_matches = re.findall(r'<([^<>@\s]+@[^<>\s]+)>', patch_response.text)
                            for email in email_matches:
                                if email and not email.endswith(('.noreply.github.com', 'users.noreply.github.com')):
                                    return email
                
                # Add a small delay
                time.sleep(self.delay)
        except Exception as e:
            print(f"Error extracting patch email for {username}: {e}")
        
        return None
    
    def get_already_processed_users(self):
        """Get a set of users that have already been processed if resuming."""
        if not self.resume or not os.path.exists(self.output_file):
            return set()
            
        processed_users = set()
        try:
            with open(self.output_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header
                for row in reader:
                    if row and len(row) >= 1:
                        processed_users.add(row[0])
            print(f"Found {len(processed_users)} already processed users.")
        except Exception as e:
            print(f"Error reading existing output file: {e}")
            
        return processed_users
    
    def process_users(self):
        """Process the input file and find emails for each user."""
        if not os.path.exists(self.input_file):
            print(f"Input file not found: {self.input_file}")
            return
        
        # Create the output directory if it doesn't exist
        output_dir = os.path.dirname(self.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Get already processed users if resuming
        already_processed = self.get_already_processed_users()
        
        # Prepare output file
        file_exists = os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0
        file_mode = 'a' if file_exists else 'w'
        
        with open(self.input_file, 'r', newline='', encoding='utf-8') as infile, \
             open(self.output_file, file_mode, newline='', encoding='utf-8') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            # Write header if file doesn't exist or is empty
            header = next(reader)  # Skip input header
            if not file_exists:
                writer.writerow(['Username', 'GitHub URL', 'Email', 'Location', 'Organization', 'Source'])
            
            start_time = time.time()
            processed = 0
            skipped_for_resume = 0
            current_position = 1  # 1-indexed position in the file
            
            # Skip users until we reach the start position
            while current_position < self.start:
                try:
                    next(reader)
                    current_position += 1
                except StopIteration:
                    print(f"Reached end of file before position {self.start}")
                    return
            
            # Store progress information
            progress_file = f"{self.output_file}.progress"
            last_save_time = time.time()
            
            # Process users
            for row in reader:
                if len(row) < 2:
                    continue
                
                # Check if we've reached the stop position
                if self.stop and current_position >= self.stop:
                    print(f"Reached stopping position {self.stop}. Stopping.")
                    break
                
                username = row[0]
                github_url = row[1]
                
                # Skip if already processed (when resuming)
                if self.resume and username in already_processed:
                    skipped_for_resume += 1
                    self.stats['skipped'] += 1
                    current_position += 1
                    continue
                
                self.stats['total_users'] += 1
                
                print(f"Processing user {username} ({current_position}/{self.stop or 'end'})...")
                
                # Try different methods to find email
                email = None
                location = None
                organization = None
                source = "None"
                
                # Method 1: Profile email
                profile_result = self.get_profile_email(username)
                if isinstance(profile_result, tuple) and len(profile_result) == 3:
                    profile_email, location, organization = profile_result
                    if profile_email:
                        email = profile_email
                        source = "Profile"
                
                # Method 2: Commit emails
                if not email:
                    email = self.get_commit_emails(username)
                    if email:
                        source = "Commit"
                
                # Method 3: Event emails
                if not email:
                    email = self.get_event_emails(username)
                    if email:
                        source = "Event"
                
                # Method 4: Patch extraction (fallback)
                if not email:
                    email = self.extract_patch_email(username)
                    if email:
                        source = "Patch"
                
                # Update stats
                if email:
                    self.stats['emails_found'] += 1
                else:
                    self.stats['no_email'] += 1
                
                # Write to output file
                writer.writerow([username, github_url, email or '', location or '', organization or '', source])
                outfile.flush()  # Ensure data is written to disk
                
                # Update progress after each user
                with open(progress_file, 'w') as pf:
                    pf.write(f"{self.stats['total_users']},{current_position},{self.start},{skipped_for_resume}")
                
                # Show progress
                processed += 1
                current_position += 1
                if processed % 5 == 0 or time.time() - last_save_time > 300:  # Report every 5 users or 5 minutes
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    if self.stop:
                        remaining = self.stop - current_position
                        eta = remaining / rate if rate > 0 else None
                        print(f"\nProgress: {processed} users processed ({current_position-1}/{self.stop})")
                    else:
                        print(f"\nProgress: {processed} users processed (position: {current_position-1})")
                    
                    print(f"Emails found: {self.stats['emails_found']} ({self.stats['emails_found']*100/processed:.1f}%)")
                    print(f"Rate: {rate:.2f} users/second")
                    if self.stop and eta:
                        print(f"ETA: {eta/60:.1f} minutes")
                    
                    last_save_time = time.time()
                    
                # Respect GitHub API rate limits with delay
                time.sleep(self.delay)
        
        # Clean up progress file
        if os.path.exists(progress_file):
            os.remove(progress_file)
    
    def print_stats(self):
        """Print statistics after processing."""
        print("\n==== GitHub Email Finder Statistics ====")
        print(f"Total users processed: {self.stats['total_users']}")
        if self.stats['skipped'] > 0:
            print(f"Users skipped (already processed): {self.stats['skipped']}")
        
        if self.stats['total_users'] > 0:
            success_rate = self.stats['emails_found'] * 100 / self.stats['total_users']
            print(f"Emails found: {self.stats['emails_found']} ({success_rate:.1f}% success rate)")
            print(f"  - From profiles: {self.stats['profile_emails']}")
            print(f"  - From commits: {self.stats['commit_emails']}")
            print(f"  - From events: {self.stats['event_emails']}")
            print(f"Users without emails: {self.stats['no_email']}")
        
        print(f"API errors encountered: {self.stats['api_errors']}")
        print(f"Results saved to: {self.output_file}")
        print("======================================")

def main():
    parser = argparse.ArgumentParser(description='Extract email addresses from GitHub stargazers')
    parser.add_argument('--input', '-i', default='complete_stargazers.csv',
                       help='Input CSV file with GitHub usernames and URLs')
    parser.add_argument('--output', '-o', default='github_emails.csv',
                       help='Output CSV file to save results')
    parser.add_argument('--token', '-t', help='GitHub API token for authentication')
    parser.add_argument('--delay', '-d', type=float, default=1.0,
                       help='Delay between API requests in seconds')
    parser.add_argument('--max-retries', '-r', type=int, default=3,
                       help='Maximum number of retry attempts for failed requests')
    parser.add_argument('--start', '-s', type=int, default=1, 
                       help='Starting position in the input file (1-indexed)')
    parser.add_argument('--stop', '-e', type=int, 
                       help='Stopping position in the input file')
    parser.add_argument('--resume', action='store_true',
                       help='Resume processing, skipping already processed users')
    
    args = parser.parse_args()
    
    print("GitHub Email Finder")
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    print(f"Delay between requests: {args.delay}s")
    
    if args.start > 1:
        print(f"Starting from position: {args.start}")
    if args.stop:
        print(f"Stopping at position: {args.stop}")
    if args.resume:
        print("Resuming from previous run, will skip already processed users")
    
    finder = GithubEmailFinder(
        input_file=args.input,
        output_file=args.output,
        token=args.token,
        delay=args.delay,
        max_retries=args.max_retries,
        start=args.start,
        stop=args.stop,
        resume=args.resume
    )
    
    finder.process_users()
    finder.print_stats()

if __name__ == "__main__":
    main() 