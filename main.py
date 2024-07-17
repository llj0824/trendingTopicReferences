import tweepy
import datetime
import json
from config import TWITTER_CREDENTIALS

# Twitter API credentials
consumer_key = TWITTER_CREDENTIALS["consumer_key"]
consumer_secret = TWITTER_CREDENTIALS["consumer_secret"]
access_token = TWITTER_CREDENTIALS["access_token"]
access_token_secret = TWITTER_CREDENTIALS["access_token_secret"]

# Authenticate to Twitter
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Create API object
api = tweepy.API(auth)

tweetCountNum=20

# Function to search tweets
def search_tweets(query, count=tweetCountNum):
    tweets = []
    for tweet in tweepy.Cursor(api.search_tweets, q=query, lang="en", tweet_mode='extended').items(count):
        tweets.append({
            'text': tweet.full_text,
            'user': tweet.user.screen_name,
            'retweet_count': tweet.retweet_count,
            'favorite_count': tweet.favorite_count,
            'created_at': tweet.created_at.isoformat()
        })
    return tweets

# Function to get trending topics
def get_trending_topics(woeid=23424977):  # WOEID for United States
    trends = api.get_place_trends(woeid)
    return [trend['name'] for trend in trends[0]['trends']]

# Function to log data
def log_data(data):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"{today}.log"
    
    with open(filename, 'a') as f:
        f.write(json.dumps(data, indent=2))
        f.write("\n\n")  # Add some space between entries

# Main execution
if __name__ == "__main__":
    # Search terms (case-insensitive)
    search_terms = ["confidence", "exercise", "nutrition", "huberman", "myself"]
    
    # Construct the search query
    search_query = " OR ".join(search_terms)
    
    # Search for tweets
    tweets = search_tweets(search_query)
    
    # Get trending topics
    trending_topics = get_trending_topics()
    # Combine data
    data = {
        'search_query': search_query,
        'tweets': tweets,
        'trending_topics': trending_topics,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    # Log the data
    log_data(data)

    print(f"Data collected and saved to {datetime.datetime.now().strftime('%Y-%m-%d')}.log")