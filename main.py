import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from llm_api_utils import LLM_API_Utils
import datetime
import json


"""
This codebase creates a trend-finding tool for content creation, focusing on YouTube data. 
It uses the YouTube API to fetch trending videos and search results, then analyzes them using GPT-4 to identify current trends and generate insights.

Key features include:
Fetching trending videos in specific categories [not very useful at all, can remove]
Searching for relevant videos based on given terms
Analyzing trends and generating new search terms using AI [useful, worth exploring and tuning more.]
Logging data and analysis results for future reference

Given a {userQuery} this tool can help you identify current trends and references to include in content to increase discoverability. 
"""
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
userQuery = "I'm making an article about Dr. Paul Conti's How to Improve Mental Health interview on Huberman Labs."
searchVideoNums = 5
videoCommentsNums = 5
relatedVideosNums = 2
llm_iterations = 3
llm_api_utils = LLM_API_Utils()

def main():
    youtube = get_authenticated_service()

    try:
        print(f"Finding trending topics for query: {userQuery}")
        log_data("", includeTimestampDivider=True) # starts a new log for this run.
        for iteration in range(llm_iterations):
            print(f"\nIteration {iteration + 1} analysis and search...")
            
            # Perform analysis to get new search terms.
            # Note: on initial search just uses userQuery
            latest_log = get_latest_log()
            new_search_terms = analyze_for_new_terms(latest_log, userQuery)
            
            # Perform new search with extracted terms and log results
            relevant_videos = search_and_log(youtube, new_search_terms, log_title=f'Iteration {iteration + 1} Relevant Videos')
        
        print("\nPerforming final analysis...")
        final_analysis = analyze_trends(get_latest_log(), userQuery)
        print("Final analysis complete. Logging results...")
        log_data(final_analysis, includeTimestampDivider=False)

        print(f"Data collection and analysis complete. Results saved to {datetime.datetime.now().strftime('%Y-%m-%d')}.log")

    except HttpError as e:
        print("An error occurred: %s" % e)

    print("Trend finder process completed.")

def analyze_for_new_terms(log_data, userQuery):
    system_role = "You are a world-class content strategist and trend analyst specializing in YouTube content. Your task is to analyze search results and identify both specific and broader, popular topics related to the user's query."

    prompt = f"""
        Analyze the following YouTube data and suggest relevant references and new search terms for further exploration:
        User Query: {userQuery}
        Data: {log_data}

        Provide the analysis addressing the following:
        1. Identify and list 3 specific references relevant to the user query.
        2. Explain why each reference is relevant.
        3. Suggest how each reference can be integrated into the content.
        4. Highlight potential engagement benefits.
        5. Recommend 3 new search terms for further exploration.

        Structure your response as follows:

        Explanation:
        1. [reference to include 1]
          - Relevance: [explain]
          - Integration method: [suggested method]
          - Engagement benefit: [explain]

        Search Terms:
        Specific:
        1. [specific_term1]: [brief explanation]
        2. [specific_term2]: [brief explanation]
        3. [specific_term3]: [brief explanation]

        Broader:
        1. [broad_term1]: [brief explanation]
        2. [broad_term2]: [brief explanation]


        <newSearchTerms>
        ["specific_term", "broad_term", a "broad_term" or "specific_term"]
        </newSearchTerms>

        Ensure that your response follows this exact structure, as it will be parsed programmatically.
    """

    analysis = llm_api_utils.call_gpt4(prompt=prompt, system_role=system_role)
    # Printing the raw response from the API

    print(f"Raw response from GPT-4 Analysis: {analysis}")
    return extract_tag(analysis, "newSearchTerms")

def search_and_log(youtube, search_terms, log_title):
    print(f"Searching for videos with terms: {', '.join(search_terms)}")
    relevant_videos = search_videos(youtube, search_terms)
    print(f"Found {len(relevant_videos)} relevant videos:")
    print_video_list(relevant_videos)

    logged_data = {
        'log_title': log_title,
        'search_terms': search_terms,
        'relevant_videos': relevant_videos,
        'timestamp': datetime.datetime.now().isoformat()
    }

    log_data(logged_data,includeTimestampDivider=False)
    return relevant_videos

def print_video_list(video_list, max_display=5):
    """Print a list of videos with their titles, limiting the output."""
    for i, video in enumerate(video_list[:max_display]):
        print(f"  {i+1}. {video['title']} (ID: {video['id']})")
    if len(video_list) > max_display:
        print(f"  ... and {len(video_list) - max_display} more")

def extract_tag(analysis, searchTerm):
    start_tag = f"<{searchTerm}>"
    end_tag = f"</{searchTerm}>"
    start_index = analysis.find(start_tag) + len(start_tag)
    end_index = analysis.find(end_tag)
    terms_string = analysis[start_index:end_index].strip()
    return eval(terms_string)  # Convert string representation of list to actual list

def get_video_comments(youtube, video_id, max_results=videoCommentsNums):
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

def get_latest_log():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"{today}.log"
    with open(filename, 'r') as f:
        content = f.read()
    sections = content.split("*" * 30)
    return sections[-1]  # Return the last section

def analyze_trends(log_data, userQuery):
    system_role = """You are an expert content strategist and trend analyst. Your role is to analyze YouTube trending data and provide actionable insights for content creators. Ensure your response is structured and includes specific, clear recommendations. 

    Your analysis should include:
    - Trend analysis: Identifying and explaining trends, themes, or popular content
    - Actionable recommendations: How these insights can be applied to enhance content engagement and visibility.
    - Search exploration: Suggest new search terms based on relevance.
    """
    
    prompt = f"""
        Analyze the following YouTube trending data and suggest relevant references for our content creation:
        User Query: {userQuery}
        Data: {log_data}

        Provide the analysis addressing the following:
        1. Identify and list 3 specific references relevant to the user query.
        2. Explain why each reference is relevant.
        3. Suggest how each reference can be integrated into the content.
        4. Highlight potential engagement benefits.
        5. Recommend 3 new search terms for further exploration.

        Structure your response as follows:

        Explanation:
        1. [reference to include 1]
          - Relevance: [explain]
          - Integration method: [suggested method]
          - Engagement benefit: [explain]

        Search Terms:
        1. [term1]: [brief explanation]
        2. [term2]: [brief explanation]
        3. [term3]: [brief explanation]

        <newSearchTerms>
        ["term1", "term2", "term3"]
        </newSearchTerms>

        Ensure that your response follows this exact structure, as it will be parsed programmatically.
    """

    analysis = llm_api_utils.call_gpt4(prompt=prompt, system_role=system_role)
    print("Trend Analysis:")
    print(analysis)
    return analysis

def search_videos(youtube, search_terms, max_results=searchVideoNums):
    # Combine the search terms into a single query string separated by " | "
    search_query = " | ".join(search_terms)
    
    # Calculate the date one week ago in ISO format, required for YouTube API
    one_week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat() + "Z"
    
    # Create a search request to the YouTube API
    request = youtube.search().list(
        part="snippet",  # Request snippet information of the video
        q=search_query,  # Query string for searching videos
        type="video",  # Search only for videos
        maxResults=max_results,  # Maximum number of results to return
        order="relevance",  # Order results by view count
        publishedAfter=one_week_ago  # Filter videos published within the last week
    )
    
    # Execute the search request and get the response
    response = request.execute()

    # Initialize a list to store relevant video information
    relevant_videos = []

    # Loop through each item (video) in the search response
    for item in response['items']:
        # Create a request to get detailed information about the video using its ID
        video_response = youtube.videos().list(
            part="snippet,statistics,topicDetails",  # Request snippet, statistics, and topic details
            id=item['id']['videoId']  # Video ID to fetch details for
        ).execute()

        # Extract the video data from the response
        video_data = video_response['items'][0]

        # Get comments for this video (assuming a function `get_video_comments` exists)
        comments = get_video_comments(youtube, item['id']['videoId'])

        # Create a dictionary with the relevant video information
        video = {
            'id': item['id']['videoId'],  # Video ID
            'title': video_data['snippet']['title'],  # Video title
            'description': video_data['snippet']['description'],  # Video description
            'channel_title': video_data['snippet']['channelTitle'],  # Channel title
            'published_at': video_data['snippet']['publishedAt'],  # Publish date
            'view_count': video_data['statistics'].get('viewCount', 'N/A'),  # View count (default to 'N/A' if not available)
            'like_count': video_data['statistics'].get('likeCount', 'N/A'),  # Like count (default to 'N/A' if not available)
            'comment_count': video_data['statistics'].get('commentCount', 'N/A'),  # Comment count (default to 'N/A' if not available)
            'topics': video_data.get('topicDetails', {}).get('topicCategories', []),  # Topic categories (default to empty list if not available)
            'comments': comments  # Add comments fetched earlier to the video data
        }
        
        # Add the video information dictionary to the list of relevant videos
        relevant_videos.append(video)

    # Return the list of relevant videos
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
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'google_client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('youtube', 'v3', credentials=creds)

if __name__ == "__main__":
    main()