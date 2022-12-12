from enum import Enum

class SpotifyKeys(Enum):
    ITEM = "item"
    IS_PLAYING = "is_playing"
    NAME = "name"
    ARTISTS = "artists"

class SpotifyScopes(Enum):
    USER_READ_PLAYBACK_STATE = "user-read-playback-state"
    USER_MODIFY_PLAYBACK_STATE = "user-modify-playback-state"
    USER_READ_CURRENTLY_PLAYING = "user-read-currently-playing"

class SpotifyAPIEndpoints(Enum):
    CURRENTLY_PLAYING = "https://api.spotify.com/v1/me/player/currently-playing"


