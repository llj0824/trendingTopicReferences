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
userQuery = "I'm making an article about Dr. Paul Conti's How to Improve Mental Health interview on Huberman Labs."
categories = {
    1: 'Film & Animation',
    2: 'Autos & Vehicles',
    3: 'Music',
    4: 'Pets & Animals',
    5: 'Sports',
    6: 'Short Movies',
    7: 'Travel & Events',
    8: 'Gaming',
    9: 'Videoblogging',
    10: 'People & Blogs',
    11: 'Comedy',
    12: 'Entertainment',
    13: 'News & Politics',
    14: 'Howto & Style',
    15: 'Education',
    16: 'Science & Technology',
    17: 'Nonprofits & Activism',
    18: 'Movies',
    19: 'Anime/Animation',
    20: 'Action/Adventure',
    21: 'Classics',
    22: 'Comedy',
    23: 'Documentary',
    24: 'Drama',
    25: 'Family',
    26: 'Foreign',
    27: 'Horror',
    28: 'Sci-Fi/Fantasy',
    29: 'Thriller',
    30: 'Shorts',
    31: 'Shows',
    32: 'Trailers'
}
trendingVideosNums = 3
searchVideoNums = 3
llm_api_utils = LLM_API_Utils()

def main():
    youtube = get_authenticated_service()

    try:
        # Get trending videos in specific categories
        trending_videos = get_trending_videos_by_category(youtube, "27")  # Education category

        # Search for relevant videos
        search_terms = ["confidence", "exercise", "nutrition", "huberman", "mental health"]
        relevant_videos = search_videos(youtube, search_terms)

        # Get comments for relevant videos
        for video in relevant_videos:
            video['top_comments'] = get_video_comments(youtube, video['id'])

        # TODO: use LLM to generate new more directed and get related videos from them.

        # Combine data
        data = {
            'trending_videos': trending_videos,
            'related_videos': related_videos,
            'timestamp': datetime.datetime.now().isoformat()
        }

        # Log the data
        log_data(data)

        # Feed the log to LLM for analysis
        analysis_result = analyze_trends(get_latest_log())
        
        # Log the analysis result too
        log_data(analysis_result, includeTimestampDivider=False)

        print(f"Data collected and saved to {datetime.datetime.now().strftime('%Y-%m-%d')}.log")

    except HttpError as e:
        print("An error occurred: %s" % e)


def get_trending_videos_by_category(youtube, category_id, max_results=trendingVideosNums):
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode="US",
        videoCategoryId=category_id,
        maxResults=max_results
    )
    response = request.execute()

    trending_videos = []
    for item in response['items']:
        video = {
            'id': item['id'],
            'title': item['snippet']['title'],
            'description': item['snippet']['description'],
            'view_count': item['statistics']['viewCount'],
            'like_count': item['statistics'].get('likeCount', 'N/A'),
            'comment_count': item['statistics'].get('commentCount', 'N/A'),
            'published_at': item['snippet']['publishedAt']
        }
        trending_videos.append(video)
    return trending_videos

def get_video_comments(youtube, video_id, max_results=10):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        order="relevance"
    )
    response = request.execute()

    comments = []
    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']
        comments.append({
            'author': comment['authorDisplayName'],
            'text': comment['textDisplay'],
            'like_count': comment['likeCount'],
            'published_at': comment['publishedAt']
        })

    return comments

def get_related_videos(youtube, video_id, max_results=5):
    request = youtube.search().list(
        part="snippet",
        type="video",
        relatedToVideoId=video_id,
        maxResults=max_results
    )
    response = request.execute()

    related_videos = []
    for item in response['items']:
        video = {
            'id': item['id']['videoId'],
            'title': item['snippet']['title'],
            'description': item['snippet']['description'],
            'channel_title': item['snippet']['channelTitle'],
            'published_at': item['snippet']['publishedAt']
        }
        related_videos.append(video)

    return related_videos

def get_latest_log():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"{today}.log"
    with open(filename, 'r') as f:
        content = f.read()
    sections = content.split("*" * 30)
    return sections[-1]  # Return the last section

def analyze_trends(log_data):
    prompt = f"Analyze the following YouTube trending videos data and provide insights:\n\n{log_data}"
    analysis = LLMUtils.callLLM(prompt)
    print("Trend Analysis:")
    print(analysis)


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

def log_data(data, includeTimestampDivider=True):
    datasource = "YouTube"
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    filename = f"{today}.log"
    
    divider = "*" * 30
    time_divider = f"{divider}\n YouTube:{current_time} \n{divider}\n"
    
    with open(filename, 'a') as f:
        if includeTimestampDivider:
            f.write(time_divider)
        f.write(json.dumps(data, indent=2))
        f.write("\n\n")

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


if __name__ == "__main__":
    main()