import json

import requests

# Your API key
API_KEY = 'AIzaSyCCT1LtbzrZ2OYvd08gpSwvIR--NEEvYyw'

# Search for videos
search_url = 'https://www.googleapis.com/youtube/v3/search'
search_params = {
    'part': 'snippet',
    'q': 'Explore how traditional Chinese ingredients and dishes can effectively aid in managing diabetes, offering a fusion of taste and health.',
    'type': 'video',
    'key': API_KEY,
    'maxResults': 1  # Number of results to return
}

search_response = requests.get(search_url, params=search_params)
search_results = search_response.json()

# Get video IDs
video_ids = [item['id']['videoId'] for item in search_results['items']]

# Retrieve video details
videos_url = 'https://www.googleapis.com/youtube/v3/videos'
videos_params = {
    'part': 'snippet,contentDetails,statistics',
    'id': ','.join(video_ids),
    'key': API_KEY
}

videos_response = requests.get(videos_url, params=videos_params)
videos_details = videos_response.json()

# Analyze video details
for video in videos_details['items']:
    title = video['snippet']['title']
    description = video['snippet']['description']
    # Perform analysis to check if the video corresponds to your prompt
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(json.dumps(video, indent=1))
