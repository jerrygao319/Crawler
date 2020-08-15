# Get the Twitter API key
 1. Visit the [Twitter Developers site](https://developer.twitter.com/) and sign in with your Twitter account
 2. Go to [Twitter Application](https://dev.twitter.com/apps/) and create an Twitter application. (Your interface may different from mine.)
 ![apps](https://raw.githubusercontent.com/jerry0319/Crawler/master/pic/apps.jpg)
 3. At the detail page, you can see the API key & secret.
 ![detail](https://raw.githubusercontent.com/jerry0319/Crawler/master/pic/detail.jpg)
 ![API key](https://raw.githubusercontent.com/jerry0319/Crawler/master/pic/API%20key.jpg)
 4. Then generate the access token and secret.
 ![generate](https://raw.githubusercontent.com/jerry0319/Crawler/master/pic/generate.jpg)
 ![access token](https://raw.githubusercontent.com/jerry0319/Crawler/master/pic/access%20token.jpg)
 
 # Crawl the Tweets
 * Some libraries will help you crawl the data. (BTW, I used [Tweepy](https://www.tweepy.org/))
 * The above API key is used when crawling the data.
 My code is as follows:
 ```python
import tweepy

auth = tweepy.OAuthHandler("Your API key", "Your API key secret")
auth.set_access_token("Your access token", "Your access token")
api = tweepy.API(auth)
```
* You can refer to the [GET statuses/lookup](https://developer.twitter.com/en/docs/twitter-api/v1/tweets/post-and-engage/api-reference/get-statuses-lookup) method to get tweets by ID. It can get up to 100 tweets at a time.
 My code is as follows:
```python
api.statuses_lookup("Your ID list (max 100)", tweet_mode='extended', include_entities=True)
```
