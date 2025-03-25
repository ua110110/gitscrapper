import requests
import json
import time
import csv
import os
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

class DiscordMessageFetcher:
    """
    A class to fetch messages from Discord API with pagination support
    """
    
    BASE_URL = "https://discord.com/api/v9"
    
    def __init__(self, auth_token: str, channel_id: str):
        """
        Initialize with Discord authentication token and channel ID
        
        Args:
            auth_token: Discord authorization token
            channel_id: Discord channel ID to fetch messages from
        """
        self.auth_token = auth_token
        self.channel_id = channel_id
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en;q=0.9',
            'authorization': auth_token,
            'priority': 'u=1, i',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-discord-timezone': 'Asia/Calcutta',
            'x-super-properties': 'eyJvcyI6Ik1hYyBPUyBYIiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1HQiIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChNYWNpbnRvc2g7IEludGVsIE1hYyBPUyBYIDEwXzE1XzcpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMzMuMC4wLjAgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6IjEzMy4wLjAuMCIsIm9zX3ZlcnNpb24iOiIxMC4xNS43IiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjM4MTY1MywiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiaGFzX2NsaWVudF9tb2RzIjpmYWxzZX0='
        }
        # Store all fetched users
        self.users = {}
    
    def fetch_messages(self, limit: int = 50, before: Optional[str] = None, after: Optional[str] = None, around: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch messages from a Discord channel with optional pagination
        
        Args:
            limit: Number of messages to fetch (max 100)
            before: Fetch messages before this message ID
            after: Fetch messages after this message ID
            around: Fetch messages around this message ID
            
        Returns:
            List of message objects
        """
        url = f"{self.BASE_URL}/channels/{self.channel_id}/messages"
        params = {'limit': limit}
        
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if around:
            params['around'] = around
            
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching messages: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return []
    
    def fetch_messages_before(self, message_id: Optional[str] = None, max_messages: int = 500) -> List[Dict[str, Any]]:
        """
        Fetch messages before a specific message ID
        
        Args:
            message_id: The message ID to fetch messages before
            max_messages: Maximum number of messages to fetch
            
        Returns:
            List of message objects
        """
        all_messages = []
        current_id = message_id
        
        while len(all_messages) < max_messages:
            batch_size = min(100, max_messages - len(all_messages))
            batch = self.fetch_messages(limit=batch_size, before=current_id)
            
            if not batch:
                break
                
            all_messages.extend(batch)
            print(f"Fetched {len(all_messages)} messages (before) so far...")
            
            # Update the current ID for pagination
            current_id = batch[-1]['id']
            
            # Respect rate limits
            time.sleep(1)
            
            if len(batch) < batch_size:
                break
                
        return all_messages
    
    def fetch_messages_after(self, message_id: str, max_messages: int = 500) -> List[Dict[str, Any]]:
        """
        Fetch messages after a specific message ID
        
        Args:
            message_id: The message ID to fetch messages after
            max_messages: Maximum number of messages to fetch
            
        Returns:
            List of message objects in chronological order
        """
        all_messages = []
        current_id = message_id
        
        while len(all_messages) < max_messages:
            batch_size = min(100, max_messages - len(all_messages))
            batch = self.fetch_messages(limit=batch_size, after=current_id)
            
            if not batch:
                break
                
            # Messages will be in reverse chronological order, so we need to get the oldest message ID
            all_messages = batch + all_messages  # Prepend to maintain chronological order
            print(f"Fetched {len(all_messages)} messages (after) so far...")
            
            # Update the current ID for pagination (get the newest message ID)
            current_id = batch[0]['id']
            
            # Respect rate limits
            time.sleep(1)
            
            if len(batch) < batch_size:
                break
                
        return all_messages
    
    def fetch_all_messages_bidirectional(self, reference_message_id: Optional[str] = None, max_before: int = 250, max_after: int = 250) -> List[Dict[str, Any]]:
        """
        Fetch messages both before and after a reference message ID
        
        Args:
            reference_message_id: The reference message ID to fetch around
            max_before: Maximum messages to fetch before the reference
            max_after: Maximum messages to fetch after the reference
            
        Returns:
            List of all message objects in chronological order
        """
        # If no reference ID is provided, just fetch recent messages
        if not reference_message_id:
            print("No reference message ID provided, fetching most recent messages...")
            return self.fetch_messages_before(None, max_before)
        
        # Fetch messages before the reference ID
        print(f"Fetching messages before reference ID: {reference_message_id}")
        before_messages = self.fetch_messages_before(reference_message_id, max_before)
        
        # Fetch messages after the reference ID
        print(f"Fetching messages after reference ID: {reference_message_id}")
        after_messages = self.fetch_messages_after(reference_message_id, max_after)
        
        # Reference message itself (might be fetched in either before or after queries)
        reference_message = None
        
        # Check if reference message is in either list
        for msg in before_messages + after_messages:
            if msg['id'] == reference_message_id:
                reference_message = msg
                break
        
        # If reference message wasn't found, fetch it specifically
        if not reference_message:
            reference_batch = self.fetch_messages(limit=1, around=reference_message_id)
            if reference_batch:
                reference_message = reference_batch[0]
        
        # Combine all messages in chronological order
        all_messages = before_messages + ([reference_message] if reference_message else []) + after_messages
        
        # Remove any duplicates by ID
        unique_messages = {}
        for msg in all_messages:
            unique_messages[msg['id']] = msg
        
        # Convert back to a list and sort by timestamp
        sorted_messages = sorted(unique_messages.values(), key=lambda m: m['timestamp'])
        
        print(f"Total unique messages fetched: {len(sorted_messages)}")
        return sorted_messages
    
    def extract_users_from_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Extract unique users from message objects
        
        Args:
            messages: List of message objects
            
        Returns:
            Dictionary of users with user ID as key
        """
        users = {}
        
        for message in messages:
            # Author of the message
            author = message.get('author', {})
            user_id = author.get('id')
            
            if user_id and user_id not in users:
                users[user_id] = {
                    'id': user_id,
                    'username': author.get('username'),
                    'global_name': author.get('global_name'),
                    'discriminator': author.get('discriminator'),
                    'avatar': author.get('avatar'),
                    'bot': author.get('bot', False)
                }
            
            # Mentioned users
            mentions = message.get('mentions', [])
            for mention in mentions:
                mention_id = mention.get('id')
                if mention_id and mention_id not in users:
                    users[mention_id] = {
                        'id': mention_id,
                        'username': mention.get('username'),
                        'global_name': mention.get('global_name'),
                        'discriminator': mention.get('discriminator'),
                        'avatar': mention.get('avatar'),
                        'bot': mention.get('bot', False)
                    }
        
        return users
    
    def find_messages_by_user(self, messages: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """
        Find all messages from a specific user
        
        Args:
            messages: List of message objects
            user_id: Discord user ID to filter by
            
        Returns:
            List of message objects from the specified user
        """
        return [msg for msg in messages if msg.get('author', {}).get('id') == user_id]
    
    def export_users_to_csv(self, users: Dict[str, Dict[str, Any]], filename: str = 'discord_users.csv'):
        """
        Export user data to a CSV file
        
        Args:
            users: Dictionary of user data
            filename: Output CSV filename
        """
        if not users:
            print("No users to export")
            return
            
        fieldnames = ['id', 'username', 'global_name', 'discriminator', 'avatar', 'bot']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for user_id, user_data in users.items():
                writer.writerow(user_data)
                
        print(f"Exported {len(users)} users to {filename}")
        
    def export_messages_to_json(self, messages: List[Dict[str, Any]], filename: str = 'discord_messages.json'):
        """
        Export messages to a JSON file
        
        Args:
            messages: List of message objects
            filename: Output JSON filename
        """
        if not messages:
            print("No messages to export")
            return
            
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(messages, jsonfile, indent=2)
                
        print(f"Exported {len(messages)} messages to {filename}")

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Fetch messages from Discord channels and extract user information')
    parser.add_argument('-t', '--token', help='Discord authorization token')
    parser.add_argument('-c', '--channel', default="1303749221354311752", help='Discord channel ID to fetch messages from')
    parser.add_argument('-u', '--user', default="498129674984226828", help='Target user ID to focus on (leave empty for all users)')
    parser.add_argument('-r', '--reference', help='Reference message ID for bidirectional fetching')
    parser.add_argument('-b', '--before', type=int, default=250, help='Maximum messages to fetch before reference point')
    parser.add_argument('-a', '--after', type=int, default=250, help='Maximum messages to fetch after reference point')
    parser.add_argument('-o', '--output-dir', default="discord_output", help='Directory to save output files')
    
    args = parser.parse_args()
    
    # Get Discord token from command-line arguments or input
    auth_token = args.token
    if not auth_token:
        auth_token = input("Enter your Discord authorization token: ")
    
    # Use the example token if still not provided
    if not auth_token:
        auth_token = "please enter your token"
        print(f"Using example token: {auth_token}")
    
    # Channel ID (use argument or default)
    channel_id = args.channel
    
    # Target user ID (use argument or None if empty)
    target_user_id = args.user if args.user else None
    
    # Reference message ID
    reference_message_id = args.reference
    
    # Message limits
    max_before = args.before
    max_after = args.after
    
    # Output directory
    output_dir = args.output_dir
    
    print("\nDiscord Message Fetcher")
    print("======================")
    print(f"Channel ID: {channel_id}")
    print(f"Target User ID: {target_user_id}")
    print(f"Reference Message ID: {reference_message_id}")
    print(f"Max Before: {max_before}")
    print(f"Max After: {max_after}")
    print(f"Output Directory: {output_dir}")
    
    # Allow interactive mode if running without command-line arguments
    if not any([args.token, args.channel != "1303749221354311752", args.user != "498129674984226828", 
                args.reference, args.before != 250, args.after != 250, args.output_dir != "discord_output"]):
        
        print("\nRunning in interactive mode. Press Enter to accept default values.")
        
        # Allow user to override default channel ID
        channel_id_input = input(f"Enter Discord channel ID (default: {channel_id}): ")
        if channel_id_input.strip():
            channel_id = channel_id_input.strip()
            
        # Allow user to override or clear target user ID
        target_user_input = input(f"Enter target user ID to focus on (default: {target_user_id}, leave empty for all users): ")
        if target_user_input.strip():
            target_user_id = target_user_input.strip()
        elif target_user_input == "":
            target_user_id = None
            
        # Allow user to set a reference message ID for bidirectional fetching
        reference_input = input("Enter reference message ID for bidirectional fetching (leave empty for most recent): ")
        if reference_input.strip():
            reference_message_id = reference_input.strip()
            
        # Get limits for message fetching
        try:
            before_input = input(f"Maximum messages to fetch before reference point (default: {max_before}): ")
            if before_input.strip():
                max_before = int(before_input)
                
            after_input = input(f"Maximum messages to fetch after reference point (default: {max_after}): ")
            if after_input.strip():
                max_after = int(after_input)
        except ValueError:
            print("Invalid input for message limits. Using defaults.")
    
    fetcher = DiscordMessageFetcher(auth_token, channel_id)
    
    # Fetch messages bidirectionally
    print("\nFetching messages bidirectionally...")
    
    try:
        messages = fetcher.fetch_all_messages_bidirectional(
            reference_message_id=reference_message_id,
            max_before=max_before,
            max_after=max_after
        )
        print(f"Total messages fetched: {len(messages)}")
        
        # Extract users
        print("\nExtracting users...")
        users = fetcher.extract_users_from_messages(messages)
        print(f"Total unique users: {len(users)}")
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Export data
        users_filename = f"{output_dir}/discord_users_{timestamp}.csv"
        messages_filename = f"{output_dir}/discord_messages_{timestamp}.json"
        
        fetcher.export_users_to_csv(users, users_filename)
        fetcher.export_messages_to_json(messages, messages_filename)
        
        # If a target user was specified, find their messages
        if target_user_id:
            target_messages = fetcher.find_messages_by_user(messages, target_user_id)
            print(f"\nFound {len(target_messages)} messages from user {target_user_id}")
            
            # Check if target user was found
            if target_user_id in users:
                user = users[target_user_id]
                print(f"\nTarget user details:")
                print(f"Username: {user.get('username')}")
                print(f"Global name: {user.get('global_name')}")
                print(f"Discriminator: {user.get('discriminator')}")
                
                # Export target user's messages to a separate file
                if target_messages:
                    target_messages_filename = f"{output_dir}/user_{target_user_id}_messages_{timestamp}.json"
                    with open(target_messages_filename, 'w', encoding='utf-8') as jsonfile:
                        json.dump(target_messages, jsonfile, indent=2)
                    print(f"Exported {len(target_messages)} messages from target user to {target_messages_filename}")
                
                # Display sample of messages from target user
                if target_messages:
                    print("\nSample messages from target user:")
                    for i, msg in enumerate(target_messages[:5]):
                        print(f"{i+1}. {msg.get('content', '[No content]')[:100]}...")
            else:
                print(f"\nTarget user {target_user_id} not found in the fetched messages.")
        
        print(f"\nAll data has been exported to the '{output_dir}' directory.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
