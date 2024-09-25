from __future__ import annotations

import difflib
import logging
import re

import requests

_logger = logging.getLogger(__name__)


def _removeExcessValue(text: str, value: str, strip: bool = True) -> str:
    """Remove excess value from text."""
    # Remove excess replace with values
    if value and text:
        text = re.sub(f"{value}+", value, text)
    if strip and text:
        text = text.strip(value or None)
    return text


def stripText(text: str, replace_with: str = '_', lower: bool = True, strip: bool = True, default: set = None,
              include: set = None, exclude: set = None) -> str:
    """
    Strip text by replacing substrings and remove excess values.

    Refer to `utils.text_manipulation.stripText` for details.
    """
    if default is None:
        default = set(" `~!@#$%^&*()-_=+|[{]};:',<.>/?\\\n\t" + '"')
    if include is None:
        include = set()
    if exclude is None:
        exclude = set()

    text = str(text)
    if lower:
        text = text.lower()

    substrings_to_replace = default.union(include) - exclude

    # Replace longer substrings first
    for char in sorted(substrings_to_replace, key=len, reverse=True):
        if char != replace_with:
            text = text.replace(char, replace_with)
        if not text:
            break

    # Remove excess replace with values
    return _removeExcessValue(text, replace_with, strip)


def sanitiseText(raw_text: str, replace_: set = None, remove_: set = None, sep: str = '_') -> str:
    """
    Sanitise text with a set of operations, simplify text for easier comparisons.

    Refer to `utils.text_manipulation.sanitiseText` for details.
    """
    fmt_text = str(raw_text)
    if replace_:
        fmt_text = stripText(fmt_text, replace_with=sep, default=replace_)
    if remove_:
        fmt_text = stripText(fmt_text, replace_with='', default=remove_)
    return stripText(fmt_text, replace_with=sep, default=set())  # Remove excess seps


def sanitiseTextCommon(raw_text: str) -> str:
    """
    Sanitise text with a set of common operations, simplify text for easier comparisons.

    Refer to `utils.text_manipulation.sanitiseTextCommon` for details.
    """
    if not raw_text:
        return raw_text or ''
    return sanitiseText(raw_text, set(' -|;'), set('\'`~!@#$%^&*()=+[{]}:,<.>/?\\'))


def patternReplaceWith(text: str, patterns: list[str | re.Pattern], replace_with: str = '_', strip: bool = True) -> str:
    """Replace matching substrings using patterns with replace value."""
    for pattern in patterns:
        text = re.sub(pattern, replace_with, text)

    # Remove excess replace with values
    return _removeExcessValue(text, replace_with, strip)


def populateLookupTables(env):
    """ Populate lookup tables with initial data. """
    # Genres Table
    genres = ['Action', 'Adventure', 'Comedy', 'Drama', 'Ecchi', 'Fan Service', 'Fantasy', 'Gore', 'Harem',
              'Historical', 'Horror', 'Isekai', 'Magic', 'Martial Arts', 'Mecha', 'Methodology', 'Mystery',
              'Psychological', 'Reincarnation', 'Romance', 'School', 'Sci-Fi', 'Shonen', 'Slice of Life',
              'Supernatural', 'Super Power', 'Suspense', 'Survival']
    for genre in genres:
        env.cur.execute("INSERT INTO genre (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (genre,))

    # Stream Services Table
    stream_services = [
        ('AnimeLab', 'https://www.animelab.com'),
        ('Crunchyroll', 'https://www.crunchyroll.com'),
        ('Funimation', 'https://www.funimation.com'),
        ('HiDive', 'https://www.hidive.com'),
        ('Netflix', 'https://www.netflix.com')
    ]

    for stream_service in stream_services:
        env.cur.execute(
            "INSERT INTO stream_service (name, domain_url) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING;",
            stream_service
        )


def addAnime(env, name: str, display_name: str) -> int:
    # Query whether the anime already exists
    env.cur.execute("""
        SELECT id FROM anime WHERE name = %s
        LIMIT 1;
    """, (name,))
    result = env.cur.fetchone()
    if result:  # Existing anime id
        return result[0]

    # Insert into the new anime table
    _logger.debug(f"Adding anime '{display_name}'")
    env.cur.execute("""
                    INSERT INTO anime (name, display_name)
                    VALUES (%s, %s)
                    RETURNING id;
                """, (name, display_name))

    new_anime_id = env.cur.fetchone()[0]
    return new_anime_id


def addService(env, anime_id: int, service: str):
    env.cur.execute("SELECT id FROM stream_service WHERE name = %s", (service,))
    service_record = env.cur.fetchone()

    if not service_record:
        _logger.warning(f"Service '{service}' not found in the stream_service table.")
        return

    service_id = service_record[0]
    # Insert into the join table (anime_stream_service)
    env.cur.execute(
        "INSERT INTO anime_stream_service (anime_id, stream_service_id) VALUES (%s, %s) "
        "ON CONFLICT (anime_id, stream_service_id) DO NOTHING;",
        (anime_id, service_id)
        )


def addGenre(env, anime_id: int, genre: str):
    if genre == "Sci Fi":
        genre = "Sci-Fi"

    # Find the corresponding genre ID in the genre table
    env.cur.execute("SELECT id FROM genre WHERE name = %s", (genre,))
    genre_record = env.cur.fetchone()

    if not genre_record:
        _logger.warning(f"Genre '{genre}' not found in the genre table.")
        return

    genre_id = genre_record[0]
    # Insert into the join table (anime_genre)
    env.cur.execute(
        "INSERT INTO anime_genre (anime_id, genre_id) VALUES (%s, %s) "
        "ON CONFLICT (anime_id, genre_id) DO NOTHING;",
        (anime_id, genre_id)
    )


def convertToLookupReferences(env, anime_id, service: str, genres_text: str):
    """ Convert texts to lookup table references. """
    # Convert service to reference and insert into anime_stream_service join table
    if service:
        addService(env, anime_id, service)

    # Convert genres to references and insert into anime_genre join table
    if genres_text:
        split_genres = genres_text.split(", ")

        # Insert references into the join table (anime_genre)
        for genre in split_genres:
            addGenre(env, anime_id, genre)


def queryJikanForAnime(name: str) -> list[dict]:
    """Call Jikan API to get all pages of anime results."""
    base_url = "https://api.jikan.moe/v4/anime"
    params = {
        'q': name.replace('_', ' '),
        'type': 'tv',
        'order_by': 'start_date',
        'page': 1  # Start from the first page
    }

    all_anime_data = []

    try:
        while True:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            json_data = response.json()

            # Add the current page's data
            all_anime_data.extend(json_data.get('data', []))

            # Check if there is another page
            pagination = json_data.get('pagination', {})
            if not pagination.get('has_next_page', False):
                break  # Exit loop if there are no more pages

            # Move to the next page
            params['page'] += 1

    except requests.exceptions.RequestException as e:
        _logger.error(f"Failed to retrieve data from Jikan API for '{name}': {e}")

    return all_anime_data


def filterOutUnrelated(anime_result: dict, name: str, threshold: float = 0.7) -> bool:
    """ Filter out anime results that are not similar enough to the given name. """
    # If the anime has not aired yet, filter it out
    if anime_result.get("status") == "Not yet aired":
        return False

    score = 0
    for title_info in anime_result.get("titles", []):
        title = title_info.get("title", "")
        # Strip and sanitise the title
        clean_title = stripText(title)

        clean_title = patternReplaceWith(clean_title, [r'(season|part)_[0-9]'])

        # Apply the built-in similarity function from difflib
        similarity = difflib.SequenceMatcher(None, name.lower(), clean_title.lower()).ratio()
        score = max(score, similarity)

    # Return True only if the best similarity score is above the threshold
    return score >= threshold


def addEpisode(env, anime_id: int, season_id: int, episode_count: int):
    _logger.debug(f"Adding {episode_count} episodes to new season '{season_id}'")
    for ep_num in range(1, episode_count + 1):
        # Insert episodes into the anime_episode table
        env.cur.execute("""
                        INSERT INTO episode (anime_id, season_id, number)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (season_id, number) DO NOTHING;
                    """, (anime_id, season_id, ep_num))


def addSeason(env, anime_id: int, display_name: str, season_result, season_number: int) -> int:
    # Extract season and episode data from the API response
    thumbnail_url = season_result['images']['jpg']['image_url']
    episode_count = season_result['episodes']
    ep_duration = int(season_result['duration'].replace(" min per ep", ""))
    genres = [x['name'] for x in (season_result['genres'] + season_result['themes'])]

    for genre in genres:
        addGenre(env, anime_id, genre)

    # Query whether the season already exists
    env.cur.execute("""SELECT id FROM season WHERE anime_id = %s AND number = %s;""", (anime_id, season_number))
    result = env.cur.fetchone()
    if result:  # Existing anime id
        return result[0]

    # Insert season into the season table
    _logger.debug(f"Adding season '{season_number}' for anime '{anime_id}'")
    env.cur.execute("""
                    INSERT INTO season (number, anime_id, myanimelist_url, thumbnail_url, mal_id, episode_count,
                    ep_duration, summary)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (season_number, anime_id, season_result['url'], thumbnail_url, season_result['mal_id'],
                      season_result['episodes'], ep_duration, season_result['synopsis']))

    season_id = env.cur.fetchone()[0]

    if episode_count == 0:
        _logger.warning(f"No episode data available for season {season_number} of {display_name}.")
        return season_id

    addEpisode(env, anime_id, season_id, episode_count)
    return season_id


def migrateAnimeData(env):
    """Migrate data from anime_old to anime table with transformations."""
    while True:
        # Fetch records from anime_old one at a time
        env.cur.execute("SELECT * FROM anime_old")
        anime = env.cur.fetchone()
        if anime is None:
            break  # Exit the loop if no more records

        anime_id, name, season, episode, times_watched, service, watch_date, genres = anime

        display_name = name
        name = sanitiseTextCommon(name)

        new_anime_id = addAnime(env, name, display_name)
        _logger.debug(f"Updating records related to anime {new_anime_id}-'{name}'")

        # Convert services and genres to references in lookup tables
        _logger.debug("Converting texts to lookup references.")
        convertToLookupReferences(env, new_anime_id, service, genres)

        _logger.debug("Querying Jikan API for anime.")
        all_anime_results = queryJikanForAnime(name)
        anime_results = [result for result in all_anime_results if filterOutUnrelated(result, name)]

        if not anime_results:
            raise Exception(f"No matching anime results found for '{display_name}' in MyAnimeList.")
        if len(anime_results) < season:
            _logger.warning(f"More recorded seasons than results for {display_name} in MyAnimeList.")
            continue  # Skip this anime if the number of seasons exceeds available results

        remaining_eps = episode
        for i in range(season):
            # Create the season and episode if not already existing
            season_id = addSeason(env, new_anime_id, display_name, anime_results[i], i + 1)

            for licensor in anime_results[i]['licensors']:
                licensor_name = licensor['name']
                if licensor_name:
                    addService(env, new_anime_id, licensor_name)

            season_episodes = anime_results[i]['episodes']

            watched_eps_this_season = min(season_episodes, remaining_eps)
            if watched_eps_this_season <= 0:
                continue  # Ran out of watched eps to created watch history

            # Add watch history
            for x in range(times_watched):
                env.cur.execute("""
                                    INSERT INTO watch_history (anime_id, season_id, date, eps_watched, completion_percentage)
                                    VALUES (%s, %s, %s, %s, %s);
                                """,
                                (new_anime_id, season_id, watch_date, watched_eps_this_season, round(watched_eps_this_season / season_episodes, 2)))
            remaining_eps -= watched_eps_this_season

        # Remove the processed record from anime_old
        env.cur.execute("DELETE FROM anime_old WHERE id = %s", (anime_id,))
        _logger.info(f"Anime {display_name} migrated and removed from anime_old.")

        _logger.info("Confirm anime has been migrated successfully.")

    # Commit the transaction after all records are processed
    env.conn.commit()


def populate(env):
    """ Data transformation from v1 to v2. """
    _logger.info("Populating the database lookup tables with initial data...")
    populateLookupTables(env)

    _logger.info("Starting data transformation for anime table...")
    migrateAnimeData(env)

    _logger.info("Data migrated successfully from anime_old to anime.")

    # Drop the old anime table
    env.cur.execute("DROP TABLE IF EXISTS anime_old")
    _logger.info("Old anime table dropped successfully.")
    _logger.info("Data population and transformations completed.")
