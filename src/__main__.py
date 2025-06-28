import os
import logging
from dotenv import load_dotenv
from .config import Config
from .plex_client import PlexClient
from .sonarr_client import SonarrClient
from .parser import get_episode_status

def main():
    load_dotenv()

    is_debug = os.getenv('DEBUG', 'false').lower() in ('true', '1', 't')
    log_level = logging.DEBUG if is_debug else logging.INFO
    
    if is_debug:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    else:
        log_format = '%(asctime)s - %(message)s'
        
    logging.basicConfig(level=log_level, format=log_format, force=True)

    if is_debug:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("plexapi").setLevel(logging.INFO)

    config_path_env = os.getenv('CONFIG_PATH')
    if config_path_env:
        config_path = config_path_env
    else:
        is_docker = os.getenv('IS_DOCKER', 'false').lower() in ('true', '1', 't')
        config_path = '/config/config.yaml' if is_docker else 'config.yaml'

    dry_run = os.getenv('DRY_RUN', 'false').lower() in ('true', '1', 't')
    
    config = Config(config_path)
    try:
        config.load()
        logging.info(f"Successfully loaded configuration from {config_path}")
    except FileNotFoundError:
        logging.error(f"Configuration file not found at '{config_path}'.")
        logging.error("Please ensure the file exists or specify a different location using the 'CONFIG_PATH' environment variable.")
        return
    except ValueError as e:
        logging.error(f"Error loading configuration: {e}")
        return

    plex_client = PlexClient(
        base_url=os.getenv('PLEX_URL'),
        token=os.getenv('API_KEY_PLEX')
    )
    sonarr_client = SonarrClient(
        base_url=os.getenv('SONARR_URL'),
        api_key=os.getenv('API_KEY_SONARR')
    )

    plex_client.connect()
    sonarr_client.connect()

    for show in config.shows:
        plex_name = show['plex_name']
        sonarr_id = show['sonarr_id']
        anime_filler_list_slug = show['animefillerlist_slug']
        
        logging.info(f"Processing show: {plex_name}")

        anime_filler_list_url = f"https://www.animefillerlist.com/shows/{anime_filler_list_slug}"

        all_episode_statuses = get_episode_status(anime_filler_list_url)
        if not all_episode_statuses:
            logging.warning(f"No episode statuses found for {plex_name}, skipping")
            continue
        
        episode_to_status_map = {}
        for status, episodes in all_episode_statuses.items():
            for episode_number in episodes:
                episode_to_status_map[episode_number] = status
        
        logging.info(f"Found {len(episode_to_status_map)} statuses for {plex_name} from AnimeFillerList")

        sonarr_episodes = sonarr_client.get_show_episodes(sonarr_id)
        if not sonarr_episodes:
            logging.warning(f"No episodes found in Sonarr for {plex_name} (ID: {sonarr_id}), skipping")
            continue

        episodes_to_tag = {}
        for ep in sonarr_episodes:
            abs_ep_num = getattr(ep, 'absolute_episode_number', None)
            logging.debug(f"Processing Sonarr episode: abs_ep_num={abs_ep_num}, title={getattr(ep, 'title', 'N/A')}")
            if abs_ep_num and abs_ep_num in episode_to_status_map:
                status = episode_to_status_map[abs_ep_num]
                season_num = getattr(ep, 'season_number', None)
                ep_num = getattr(ep, 'episode_number', None)
                if season_num is not None and ep_num is not None:
                    episodes_to_tag[(season_num, ep_num)] = status
        
        logging.info(f"Prepared {len(episodes_to_tag)} tags for '{plex_name}'")

        plex_client.update_tags(plex_name, episodes_to_tag, config.plex_library_name, dry_run=dry_run)

if __name__ == '__main__':
    main()