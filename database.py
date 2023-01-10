import sqlite3
import requests


class Database_Manager:
    def __init__(self, db_file, webapi_key) -> None:
        self.webapi_key = webapi_key
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.create_table()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

    def get_user_games(self, steamid):
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={self.webapi_key}&steamid={steamid}&include_appinfo=1&include_played_free_games=1&format=json"
        response = requests.get(url)
        match response.status_code:
            case 200:
                ...
            case 401:
                raise AttributeError("Invalid webapi key")
            case 503:
                raise ConnectionError("Steam api is down")
            case _:
                raise Exception("Unknown error while accessing steam api")
        json = response.json()
        return json

    def create_table(self):
        # this isn't nessesary, but just in case the tables don't exist
        self.cursor.executescript(
            """
            BEGIN TRANSACTION;

            CREATE TABLE IF NOT EXISTS users (
                steamid TEXT UNIQUE PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS games (
                appid INT UNIQUE PRIMARY KEY,
                game_name TEXT
            );

            CREATE TABLE IF NOT EXISTS owned_games (
                steamid TEXT NOT NULL,
                appid INT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (steamid) REFERENCES users (steamid),
                FOREIGN KEY (appid) REFERENCES games (appid)
            );

            CREATE TABLE IF NOT EXISTS tracked_playtime (
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                steamid TEXT,
                appid INT,
                playtime INT,
                FOREIGN KEY (steamid) REFERENCES users(steamid),
                FOREIGN KEY (appid) REFERENCES games(appid)
            );

            COMMIT;
            """
        )

    def add_owned_game(self, steamid, appid):
        if (
            self.cursor.execute(
                "SELECT * FROM owned_games WHERE steamid = ? AND appid = ?",
                (steamid, appid)
            ).fetchone()
            is None
        ):
            self.cursor.execute(
                """
                INSERT INTO owned_games(steamid, appid)
                VALUES (?, ?);
                """,
                (steamid, appid)
            )

    def add_game(self, appid, game_name):
        self.cursor.execute(
            """
            INSERT INTO games
            VALUES (?, ?);
            """,
            (appid, game_name)
        )

    def append_games(self, steamid, games=None):
        if games is None:
            try:
                games = self.get_user_games(steamid)
            except Exception as e:
                return e
        for game in games["response"]["games"]:
            appid = game["appid"]
            if (
                self.cursor.execute(
                    "SELECT * FROM games WHERE appid = ?", (appid,)
                ).fetchone()
                is None
            ):
                self.add_game(appid, game["name"])
            self.add_owned_game(steamid, appid)
            self.cursor.execute(
                """
                INSERT INTO tracked_playtime(steamid, appid, playtime)
                VALUES (
                    ?,
                    ?,
                    ?
                    );
                """,
                (steamid, appid, game["playtime_forever"])
            )

    def add_user(self, steamid):
        try:
            games = self.get_user_games(steamid)
        except Exception as e:
            return e
        self.cursor.execute(
            """
            INSERT INTO users
            VALUES (
                ?
                );
            """,
            (steamid,)
        )
        self.append_games(steamid, games)

    def get_users(self):
        result = self.cursor.execute("SELECT steamid FROM users").fetchall()
        return result


if __name__ == "__main__":
    with open("steam_webapi_key.txt", "r") as f:
        webapi_key = f.read()
    with Database_Manager("database.sqlite", webapi_key) as db:
        for user in db.get_users():
            user = user[0]
            db.append_games(user)
