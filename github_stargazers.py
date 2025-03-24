#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import os

def get_stargazers(repo_url, output_file='stargazers.csv', start_page=1, max_retries=3):
    """
    Scrape GitHub stargazers from a repository and save their URLs to a CSV file.
    
    Args:
        repo_url (str): The URL of the GitHub stargazers page (e.g., https://github.com/user/repo/stargazers)
        output_file (str): The name of the output CSV file
        start_page (int): The page to start scraping from (default: 1)
        max_retries (int): Maximum number of retry attempts for failed requests
    """
    # Extract the base URL and repo path
    base_url_match = re.match(r'(https://github.com/[^/]+/[^/]+)/stargazers', repo_url)
    if not base_url_match:
        base_url = re.sub(r'\?page=\d+$', '', repo_url)
        if not base_url.endswith('/stargazers'):
            base_url = base_url + '/stargazers'
    else:
        base_url = base_url_match.group(1) + '/stargazers'
    
    # Use provided start_page instead of extracting from URL
    page = start_page
    
    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # Use a set to keep track of unique usernames
    unique_stargazers = set()
    all_stargazers = []
    more_pages = True
    
    print(f"Starting to scrape stargazers from {base_url}, beginning at page {page}")
    
    # Create the directory for the output file if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Open CSV file for writing
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Username', 'GitHub URL'])  # Write header
        
        empty_pages_count = 0  # Counter for consecutive empty pages
        
        while more_pages:
            current_url = f"{base_url}?page={page}"
            print(f"Scraping page {page}: {current_url}")
            
            retries = 0
            while retries < max_retries:
                try:
                    response = requests.get(current_url, headers=headers)
                    response.raise_for_status()
                    break  # Success, exit retry loop
                except requests.exceptions.RequestException as e:
                    retries += 1
                    if retries >= max_retries:
                        print(f"Error fetching page {page} after {max_retries} attempts: {e}")
                        more_pages = False
                        break
                    print(f"Error fetching page {page}: {e}. Retrying ({retries}/{max_retries})...")
                    time.sleep(3)  # Wait longer between retries
            
            if not more_pages:
                break
                
            # Debug: Save the HTML content to inspect later if needed
            # with open(f"debug_page_{page}.html", "w", encoding="utf-8") as f:
            #     f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple selector patterns to find users
            user_elements = []
            
            # Method 1: Look for follow-list items (older GitHub layout)
            user_elements = soup.select('.follow-list-item')
            print(f"Method 1 found {len(user_elements)} users")
            
            # Method 2: Look for user links with specific attributes (newer GitHub layout)
            if not user_elements:
                user_elements = soup.select('a[data-hovercard-type="user"]')
                print(f"Method 2 found {len(user_elements)} users")
            
            # Method 3: Look for specific list structure in stargazers page
            if not user_elements:
                user_elements = soup.select('li.mb-2.mr-3.ml-0')
                print(f"Method 3 found {len(user_elements)} users")
            
            # Method 4: Look for div.d-inline-block with links
            if not user_elements:
                user_elements = soup.select('div.d-inline-block a[href^="/"]')
                print(f"Method 4 found {len(user_elements)} users")
            
            if not user_elements:
                empty_pages_count += 1
                print(f"No stargazers found on page {page}. This is empty page #{empty_pages_count}.")
                
                # If we've hit 3 consecutive empty pages, assume we've reached the end
                if empty_pages_count >= 3:
                    print("Hit 3 consecutive empty pages. Stopping.")
                    more_pages = False
                    break
                
                # Try the next page anyway
                page += 1
                time.sleep(2)  # Delay a bit longer before the next request
                continue
            
            # Reset empty pages counter since we found users
            empty_pages_count = 0
            
            page_stargazers_count = 0
            
            # Extract usernames and create GitHub URLs
            for user_element in user_elements:
                username = None
                
                # If the element itself is a link
                if user_element.name == 'a' and user_element.get('href'):
                    href = user_element.get('href').strip('/')
                    if '/' not in href:  # Ensure it's just a username, not a repo path
                        username = href
                    
                # Otherwise, look for a link inside it
                else:
                    link = user_element.select_one('a[href^="/"]')
                    if link and link.get('href'):
                        href = link.get('href').strip('/')
                        if '/' not in href:  # Ensure it's just a username, not a repo path
                            username = href
                
                # Alternative: try to get text content
                if not username and user_element.text:
                    username = user_element.text.strip()
                
                if username and username not in unique_stargazers:
                    unique_stargazers.add(username)
                    github_url = f"https://github.com/{username}"
                    all_stargazers.append((username, github_url))
                    writer.writerow([username, github_url])
                    print(f"Added stargazer: {username} - {github_url}")
                    page_stargazers_count += 1
            
            print(f"Added {page_stargazers_count} unique stargazers from page {page}")
            
            # Save progress periodically (every 10 pages)
            if page % 10 == 0:
                print(f"Progress checkpoint: Scraped {len(unique_stargazers)} unique stargazers so far")
                csvfile.flush()  # Ensure data is written to disk
            
            # Check if there's a next page (try multiple patterns)
            next_button = soup.select_one('a.next_page, a[rel="next"]')
            if not next_button:
                pagination = soup.select('div.pagination a')
                for link in pagination:
                    if link.text.strip() == 'Next' or link.get('rel') == ['next']:
                        next_button = link
                        break
                        
            if next_button and 'disabled' not in next_button.get('class', []):
                # If there's a next button and it's not disabled, move to the next page
                page += 1
            else:
                # If we still have users on this page but no next button,
                # let's try incrementing the page manually and see if more data exists
                page += 1
                
                # If we've gone beyond reasonable page numbers, break after a certain point
                if page > 1000:  # Reasonable upper limit, can be adjusted
                    print("Reached page 1000. Stopping to prevent excessive requests.")
                    more_pages = False
                    break
                
            # Be nice to GitHub's servers
            time.sleep(1.5)  # Slightly increased delay to be more respectful to GitHub
    
    print(f"\nScraping completed. Found {len(unique_stargazers)} unique stargazers.")
    print(f"Results saved to {output_file}")
    return all_stargazers

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape GitHub stargazers and save their URLs to a CSV file.')
    parser.add_argument('repo_url', help='The URL of the GitHub stargazers page (e.g., https://github.com/user/repo/stargazers)')
    parser.add_argument('--output', '-o', default='stargazers.csv', help='The name of the output CSV file')
    parser.add_argument('--start', '-s', type=int, default=1, help='Page to start scraping from (default: 1)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode to save HTML content')
    parser.add_argument('--retries', '-r', type=int, default=3, help='Maximum number of retry attempts for failed requests')
    
    args = parser.parse_args()
    
    get_stargazers(args.repo_url, args.output, args.start, args.retries) 