import logging
from plexapi.server import PlexServer
from plexapi.exceptions import NotFound

logger = logging.getLogger(__name__)

class PlexClient:
    """A client for interacting with the Plex Media Server API"""

    def __init__(self, base_url: str, token: str):
        """
        Initializes the PlexClient

        Args:
            base_url: The base URL of the Plex server
            token: The Plex API token
        """
        self.base_url = base_url
        self.token = token
        self._server = None
        # These are the tags we manage. Any other tags on the episode will be left alone.
        self.managed_tags = ["MangaCanon", "Mixed", "Filler", "AnimeCanon"]

    def connect(self):
        """Establishes and tests the connection to the Plex server"""
        try:
            self._server = PlexServer(self.base_url, self.token)
            self._server.version
            logger.info(f"Successfully connected to Plex server: {self._server.friendlyName}")
        except Exception as e:
            logger.error(f"Failed to connect to Plex at {self.base_url}: {e}")
            raise

    def update_tags(self, show_title: str, episodes_to_tag: dict, library_name: str, dry_run: bool = False):
        """
        Updates labels for episodes of a specific show in Plex

        Args:
            show_title: The title of the show to update
            episodes_to_tag: A dictionary mapping (season, episode) to a status tag
            library_name: The name of the Plex library to search in
            dry_run: If True, only log the changes that would be made
        """
        if not self._server:
            logger.error("Not connected to Plex. Call connect() first")
            return

        try:
            show = self._server.library.section(library_name).get(show_title)
            logger.info(f"Found show '{show_title}' in Plex library '{library_name}'")
        except NotFound:
            logger.error(f"Show '{show_title}' not found in Plex library '{library_name}'")
            return

        logger.info(f"Fetching all episodes for '{show_title}' from Plex. This may take a moment...")
        all_plex_episodes = show.episodes()
        logger.info(f"Found {len(all_plex_episodes)} episodes in Plex for '{show_title}'")

        episode_map = {(ep.seasonNumber, ep.index): ep for ep in all_plex_episodes}

        updated_count = 0
        skipped_count = 0

        for (season_num, ep_num), status in episodes_to_tag.items():
            try:
                episode = episode_map.get((season_num, ep_num))
                
                if not episode:
                    logger.warning(f"Episode S{season_num:02d}E{ep_num:02d} for '{show_title}' not found in the pre-fetched list from Plex. Check your season order matches between Sonarr and Plex")
                    continue
                
                current_labels = [label.tag for label in episode.labels]

                if status in current_labels:
                    logger.debug(f"Episode S{season_num:02d}E{ep_num:02d} already has tag '{status}'. Skipping")
                    skipped_count += 1
                    continue

                tags_to_remove = [tag for tag in current_labels if tag in self.managed_tags]
                
                log_prefix = "[DRY RUN] " if dry_run else ""
                
                if tags_to_remove:
                    logger.info(f"{log_prefix}Removing old tags {tags_to_remove} from S{season_num:02d}E{ep_num:02d} ('{episode.title}')")
                    if not dry_run:
                        episode.removeLabel(tags_to_remove, locked=False)

                logger.info(f"{log_prefix}Adding tag '{status}' to S{season_num:02d}E{ep_num:02d} ('{episode.title}')")
                if not dry_run:
                    episode.addLabel(status, locked=False)
                
                updated_count += 1

            except Exception as e:
                logger.error(f"Failed to update tags for S{season_num:02d}E{ep_num:02d} of '{show_title}': {e}")
        
        logger.info(f"Processing complete for '{show_title}'")
        logger.info(f"  Episodes updated: {updated_count}")
        logger.info(f"  Episodes skipped (already tagged): {skipped_count}")