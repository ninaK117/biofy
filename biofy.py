from secrets import *
import tweepy
import time
import spotipy
import requests
from bs4 import BeautifulSoup
from flask import session, request


class Biofy:
    def __init__(self):
        self.SPOTIFY_TOKEN = self.get_spotify_token()
        self.twitter_client = self.twitter_auth()
        self.default_bio = self.get_default_bio()

        self.artist_name = ''
        self.track_name = ''

    def twitter_auth(self):
        auth = tweepy.OAuthHandler(self.TWITTER_API_KEY, self.TWITTER_API_SECRET)
        try:
            redirect_url = auth.get_authorization_url()
            print("Go to this URL for verify code: " + redirect_url)
        except tweepy.TweepError:
            print('Error! Failed to get request token.')
            quit()

        print("enter the verify code from the URL above")
        verifier = input('Verify code: ')

        try:
            auth.get_access_token(verifier)
        except tweepy.TweepError:
            print('Error! Failed to get access token.')

        twitter_access_token = auth.access_token
        twitter_access_token_secret = auth.access_token_secret

        auth.set_access_token(twitter_access_token, twitter_access_token_secret)
        api = tweepy.API(auth)

        return api

    def get_spotify_token(self):

        redirect_uri = "https://example.com/callback/"
        scope = "user-read-currently-playing"
        spotify_user_id = input("Please enter your Spotify username: ")

        try:
            spotify_token = spotipy.util.prompt_for_user_token(spotify_user_id,
                                                               scope,
                                                               client_id=self.SPOTIFY_CLIENT_ID,
                                                               client_secret=self.SPOTIFY_CLIENT_SECRET,
                                                               redirect_uri=redirect_uri)
        except:
            os.remove(f".cache-{spotify_user_id}")
            spotify_token = spotipy.util.prompt_for_user_token(spotify_user_id,
                                                               scope,
                                                               client_id=self.SPOTIFY_CLIENT_ID,
                                                               client_secret=self.SPOTIFY_CLIENT_SECRET,
                                                               redirect_uri=redirect_uri)

        return spotify_token

    # get song user is currently listening to on Spotify
    def get_currently_playing_track(self):
        query = 'https://api.spotify.com/v1/me/player/currently-playing'
        response = requests.get(
            query,
            headers={
                'Authorization': 'Bearer {}'.format(self.SPOTIFY_TOKEN)
            }
        )

        if response.status_code == 200:
            response_json = response.json()
            if response_json["is_playing"]:  # make sure song is not paused
                self.artist_name = response_json["item"]["artists"][0]["name"]
                self.track_name = response_json["item"]["name"]

                self.update_twitter_bio(self.artist_name, self.track_name)
            else:
                self.update_twitter_bio('', '')
        else:
            self.update_twitter_bio('','')

    # update user's twitter bio with song currently playing on Spotify
    def update_twitter_bio(self, artist_name, track_name):
        if artist_name == '' and track_name == '':
            self.twitter_client.update_profile(description=self.default_bio)
        else:
            emoji = self.get_emoji()
            description = emoji + "Currently listening to " + track_name + " by " + artist_name + emoji
            self.twitter_client.update_profile(description=description)

    # get user's bio before Biofy access
    def get_default_bio(self):
        screen_name = self.twitter_client.me().screen_name
        return self.twitter_client.get_user(screen_name).description

    # get emojis relative to currently playing song
    def get_emoji(self):
        page = requests.get("https://emojifinder.com/{}".format(self.track_name.replace(' ', '+')))
        soup = BeautifulSoup(page.content, 'html.parser')

        if len(soup.find_all('input')) < 3:
            return '🎶'

        emoji = []
        for i in range(2, 3):
            emoji.append(soup.find_all('input')[i].attrs["value"])

        return " " + "".join(emoji)

    def wait_for_song_change(self):
        while True:
            self.get_currently_playing_track()
            time.sleep(10)


if __name__ == "__main__":
    biofy = Biofy()
    biofy.wait_for_song_change()


