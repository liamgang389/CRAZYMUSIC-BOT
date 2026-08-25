from CRAZYHUBBOT.core.bot import DAXX
from CRAZYHUBBOT.core.dir import dirr
from CRAZYHUBBOT.core.userbot import Userbot
from CRAZYHUBBOT.misc import dbb, heroku

from SafoneAPI import SafoneAPI
from .logging import LOGGER

dirr()
# git() removed: it hard-resets this deployment's files onto UPSTREAM_REPO
# on every boot, which was overwriting CRAZYHUBBOT with the upstream
# DAXXMUSIC codebase and causing the crash loop.
dbb()
heroku()

app = DAXX()
api = SafoneAPI()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
