import tweepy
import datetime
import json
from config import TWITTER_CREDENTIALS

# Twitter API credentials
bearer_token = TWITTER_CREDENTIALS["bearer_token"]

# Create client
client = tweepy.Client(bearer_token=bearer_token)

# List of relevant Twitter accounts (replace with actual usernames)
relevant_accounts = ["hubermanlab", "foundmyfitness", "PeterAttiaMD", "maxlugavere"]

def get_user_tweets(username, max_results=10):
    user = client.get_user(username=username)
    tweets = client.get_users_tweets(user.data.id, max_results=max_results, 
                                     tweet_fields=['created_at', 'public_metrics'])
    return tweets.data if tweets.data else []

def get_user_info(username):
    user = client.get_user(username=username, user_fields=['description', 'public_metrics'])
    return user.data

def log_data(data):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"{today}.log"
    
    with open(filename, 'a') as f:
        f.write(json.dumps(data, indent=2))
        f.write("\n\n")  # Add some space between entries

if __name__ == "__main__":
    all_data = []
    
    for account in relevant_accounts:
        user_info = get_user_info(account)
        tweets = get_user_tweets(account)
        
        account_data = {
            'username': account,
            'user_info': {
                'description': user_info.description,
                'followers_count': user_info.public_metrics['followers_count'],
                'tweet_count': user_info.public_metrics['tweet_count']
            },
            'recent_tweets': [
                {
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'retweet_count': tweet.public_metrics['retweet_count'],
                    'like_count': tweet.public_metrics['like_count']
                } for tweet in tweets
            ]
        }
        all_data.append(account_data)
    
    data_to_log = {
        'timestamp': datetime.datetime.now().isoformat(),
        'account_data': all_data
    }
    
    log_data(data_to_log)
    print(f"Data collected and saved to {datetime.datetime.now().strftime('%Y-%m-%d')}.log")