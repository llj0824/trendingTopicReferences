import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import json

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
trendingVideosNums = 3
searchVideoNums = 3


def get_authenticated_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'google_client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('youtube', 'v3', credentials=creds)

def main():
    youtube = get_authenticated_service()

    try:
        # Get trending videos
        trending_videos = get_trending_videos(youtube)

        # Search for relevant videos
        search_terms = ["confidence", "exercise", "nutrition", "huberman", "mental health"]
        relevant_videos = search_videos(youtube, search_terms)

        # Combine data
        data = {
            'trending_videos': trending_videos,
            'relevant_videos': relevant_videos,
            'timestamp': datetime.datetime.now().isoformat()
        }

        # Log the data
        log_data(data)

        print(f"Data collected and saved to {datetime.datetime.now().strftime('%Y-%m-%d')}.log")

    except HttpError as e:
        print("An error occurred: %s" % e)

def get_trending_videos(youtube, max_results=trendingVideosNums):
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode="US",
        maxResults=max_results
    )
    response = request.execute()

    trending_videos = []
    for item in response['items']:
        video = {
            'title': item['snippet']['title'],
            'description': item['snippet']['description'],
            'view_count': item['statistics']['viewCount'],
            'like_count': item['statistics'].get('likeCount', 'N/A'),
            'comment_count': item['statistics'].get('commentCount', 'N/A'),
            'published_at': item['snippet']['publishedAt']
        }
        trending_videos.append(video)

    return trending_videos

def search_videos(youtube, search_terms, max_results=searchVideoNums):
    search_query = " | ".join(search_terms)
    
    # Calculate the date one week ago
    one_week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat() + "Z"
    
    request = youtube.search().list(
        part="snippet",
        q=search_query,
        type="video",
        maxResults=max_results,
        order="viewCount",  # This sorts by view count, which can help identify trending videos
        publishedAfter=one_week_ago
    )
    response = request.execute()

    relevant_videos = []
    for item in response['items']:
        video_response = youtube.videos().list(
            part="snippet,statistics,topicDetails",
            id=item['id']['videoId']
        ).execute()

        video_data = video_response['items'][0]

        video = {
            'title': video_data['snippet']['title'],
            'description': video_data['snippet']['description'],
            'channel_title': video_data['snippet']['channelTitle'],
            'published_at': video_data['snippet']['publishedAt'],
            'view_count': video_data['statistics'].get('viewCount', 'N/A'),
            'like_count': video_data['statistics'].get('likeCount', 'N/A'),
            'comment_count': video_data['statistics'].get('commentCount', 'N/A'),
            'topics': video_data.get('topicDetails', {}).get('topicCategories', [])
        }
        relevant_videos.append(video)

    return relevant_videos

def log_data(data):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    filename = f"{today}.log"
    
    divider = "*" * 30
    time_divider = f"{divider}\n ******     {current_time}     ****** \n{divider}\n"
    
    with open(filename, 'a') as f:
        f.write(time_divider)
        f.write(json.dumps(data, indent=2))
        f.write("\n\n")

if __name__ == "__main__":
    main()