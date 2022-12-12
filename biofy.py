from secrets import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, TWITTER_API_KEY, TWITTER_API_SECRET
import tweepy
import time
import spotipy
import requests
import os
from bs4 import BeautifulSoup
from flask import session, request
from exceptions import MissingData
from spotify_constants import SpotifyKeys, SpotifyScopes, SpotifyAPIEndpoints


class Biofy:

    REDIRECT_URI = "https://example.com/callback/"
    EMPTY = ""

    def __init__(self):
        self.SPOTIFY_CLIENT_ID = SPOTIFY_CLIENT_ID
        self.SPOTIFY_CLIENT_SECRET = SPOTIFY_CLIENT_SECRET
        self.TWITTER_API_KEY = TWITTER_API_KEY
        self.TWITTER_API_SECRET = TWITTER_API_SECRET

        self.SPOTIFY_TOKEN = self.get_spotify_token()
        self.twitter_client = self.twitter_auth()
        self.default_bio = self.get_default_bio()

    def twitter_auth(self):
        try:
            auth = tweepy.OAuthHandler(
                self.TWITTER_API_KEY, self.TWITTER_API_SECRET)
            redirect_url = auth.get_authorization_url()
            print("Please click on this URL: " + redirect_url)
        except tweepy.TweepError:
            print("Error! Failed to get request token.")
            quit()

        print("Enter the verification code from the URL above.")
        verifier = input("Verify code: ")

        try:
            auth.get_access_token(verifier)
        except tweepy.TweepError:
            print("Error! Failed to get access token.")
            quit()

        twitter_access_token = auth.access_token
        twitter_access_token_secret = auth.access_token_secret

        auth.set_access_token(twitter_access_token,
                              twitter_access_token_secret)
        api = tweepy.API(auth)

        return api

    def get_spotify_token(self):
        spotify_user_id = input("Please enter your Spotify username: ")
        return spotipy.util.prompt_for_user_token(spotify_user_id,
                                                  SpotifyScopes.USER_READ_CURRENTLY_PLAYING.value,
                                                  client_id=self.SPOTIFY_CLIENT_ID,
                                                  client_secret=self.SPOTIFY_CLIENT_SECRET,
                                                  redirect_uri=Biofy.REDIRECT_URI)

    @staticmethod
    def get_artist_name(response_json):

        UNKNOWN_ARTIST_MSG = "Unknown Artist - '{}' attribute missing"
        if response_json and SpotifyKeys.ITEM.value in response_json.keys():
            items = response_json[SpotifyKeys.ITEM.value]
        else:
            raise MissingData(UNKNOWN_ARTIST_MSG.format(SpotifyKeys.ITEM.value))

        if items and SpotifyKeys.ARTISTS.value in items.keys():
            artists = items[SpotifyKeys.ARTISTS.value]
        else:
            raise MissingData(UNKNOWN_ARTIST_MSG.format(SpotifyKeys.ARTISTS.value))

        if artists and len(artists) > 0 and SpotifyKeys.NAME.value in artists[0]:
            return artists[0][SpotifyKeys.NAME.value]
        else:
            raise MissingData(UNKNOWN_ARTIST_MSG.format(SpotifyKeys.NAME.value))

    @staticmethod
    def get_track_name(response_json):
        UNKNOWN_TRACK_MSG = "Unknown Track Name - '{}' attribute missing"

        if response_json and SpotifyKeys.ITEM.value in response_json.keys():
            items = response_json[SpotifyKeys.ITEM.value]
        else:
            raise MissingData(UNKNOWN_TRACK_MSG.format(SpotifyKeys.ITEM.value))

        if items and SpotifyKeys.NAME.value in items.keys():
            return items[SpotifyKeys.NAME.value]
        else:
            raise MissingData(UNKNOWN_TRACK_MSG.format(SpotifyKeys.NAME.value))

    # get song user is currently listening to on Spotify

    def get_currently_playing_track(self):
        response = requests.get(
            SpotifyAPIEndpoints.CURRENTLY_PLAYING.value,
            headers={
                "Authorization": "Bearer {}".format(self.SPOTIFY_TOKEN)
            }
        )

        if not response or response.status_code != 200:
            self.update_twitter_bio(Biofy.EMPTY, Biofy.EMPTY)
            return

        response_json = response.json()
        if response_json and \
            SpotifyKeys.IS_PLAYING.value in response_json.keys() and \
                not response_json[SpotifyKeys.IS_PLAYING.value]:
            artist_name = Biofy.EMPTY
            track_name = Biofy.EMPTY
        else:
            try:
                artist_name = Biofy.get_artist_name(response_json)
                track_name = Biofy.get_track_name(response_json)
            except MissingData:
                artist_name = Biofy.EMPTY
                track_name = Biofy.EMPTY
        self.update_twitter_bio(artist_name, track_name)

    # update user's twitter bio with song currently playing on Spotify
    def update_twitter_bio(self, artist_name, track_name):
        if artist_name == Biofy.EMPTY and track_name == Biofy.EMPTY:
            self.twitter_client.update_profile(description=self.default_bio)
        else:
            emoji = Biofy.get_emoji(track_name)
            description = emoji + "Currently listening to " + \
                track_name + " by " + artist_name + emoji
            self.twitter_client.update_profile(description=description)

    # get user's bio before Biofy access
    def get_default_bio(self):
        screen_name = self.twitter_client.me().screen_name
        return self.twitter_client.get_user(screen_name).description

    # get emojis relative to currently playing song
    @staticmethod
    def get_emoji(track_name):
        if not track_name:
            raise MissingData("Cannot find emoji due to unknown track name")
        url = "https://emojifinder.com/{}".format(track_name.replace(" ", "+"))
        headers = {
            "User-Agent": "Emoji Finder",
        }
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")

        input_containers = soup.find_all("input")
        if len(input_containers) < 3:
            return "🎶"

        return " " + Biofy.EMPTY.join(input_containers[2].attrs["value"])

    def wait_for_song_change(self):
        while True:
            self.get_currently_playing_track()
            time.sleep(10)


if __name__ == "__main__":
    biofy = Biofy()
    biofy.wait_for_song_change()
