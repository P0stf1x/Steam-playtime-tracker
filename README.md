# Steam playtime tracker
This app will track how much you play your steam games. It will also store when you bought a new game.

Inspired by official Steam Replay 2022. But unlike Steam Replay, it stores (And eventually will show) playtime in minutes, and not in an abstract percentage of your total playtime. 

Currently, there's no UI, but running database.py will save playtime for every game and all newly bought games for every steamid in users table. If you want it to store your playtime, you'd have to replace my steamid with yours

# Usage

1. Add your steamid to users table in database.sqlite (You can get your using steamdb or any other tool: https://steamdb.info/calculator/)
2. Insert your steam web api key into steam_webapi_key.txt (You can get one here: https://steamcommunity.com/dev/apikey)
3. Install Python 3.10+ with requirements
4. Run ```database.py```
