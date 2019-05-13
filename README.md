# twitch-irc-bot
This is my twitch bot. There are many like it, but this is mine.

this builds to the docker container at: https://cloud.docker.com/repository/docker/bigjuevos/ez-twitch-bot/general

To work with me set some environment variables for the docker container:
T_CHAN - your channel name - all little letters 
T_NICK - your nick name - all little letters
T_PASS - you API key obtained from the instructions at https://twitchapps.com/tmi/
T_API_KEY - the appi keyfor your tweitch app so it can query the API for stats like uptime: https://dev.twitch.tv/docs/authentication/#registration

I keep mine running with a local nomad installation across my local server cluster. So, if a server bites it the bot stays up.
