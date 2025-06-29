import logging
import plexapi
from plexapi.server import PlexServer
from plexapi.exceptions import NotFound

logger = logging.getLogger(__name__)

plexapi.BASE_HEADERS.update({
    "X-Plex-Product": "Plex Filler Tagger",
    "X-Plex-Device-Name": "Plex Filler Tagger",
    "X-Plex-Client-Identifier": "cbrherms-plex-filler-tagger"
})


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

    def disconnect(self):
        """Closes the connection to the Plex server"""
        if self._server and self._server._session:
            try:
                self._server._session.close()
                logger.info("Successfully disconnected from Plex")
            except Exception as e:
                logger.error(f"Failed to disconnect from Plex: {e}")

    def update_tags(self, show_title: str, episodes_to_tag: dict, library_name: str, ep_key_to_abs_num: dict, dry_run: bool = False):
        """
        Updates labels for episodes of a specific show in Plex

        Args:
            show_title: The title of the show to update
            episodes_to_tag: A dictionary mapping (season, episode) to a status tag
            library_name: The name of the Plex library to search in
            ep_key_to_abs_num: A dictionary mapping (season, episode) to an absolute episode number
            dry_run: If True, only log the changes that would be made
        """
        if not self._server:
            logger.error("Not connected to Plex. Call connect() first")
            return

        try:
            results = self._server.library.section(library_name).search(title=show_title, libtype='show')
            
            if not results:
                logger.error(f"Show '{show_title}' not found in Plex library '{library_name}'")
                return

            show = next((s for s in results if s.title.lower() == show_title.lower()), None)
            
            if not show:
                possible_matches = [s.title for s in results]
                logger.error(f"Could not find an exact match for '{show_title}' in Plex library '{library_name}'.")
                logger.warning(f"Possible fuzzy matches were: {possible_matches}. Please check the 'plex_name' in your config.")
                return

            logger.info(f"Found exact match for show '{show.title}' in Plex library '{library_name}'")
        except NotFound:
            logger.error(f"Library '{library_name}' not found on the Plex server.")
            return

        logger.info(f"Fetching all episodes for '{show_title}' from Plex. This may take a moment...")
        all_plex_episodes = show.episodes()
        logger.info(f"Found {len(all_plex_episodes)} episodes in Plex for '{show_title}'")

        episode_map = {(ep.seasonNumber, ep.index): ep for ep in all_plex_episodes}

        tag_counts = {tag: 0 for tag in self.managed_tags}
        skipped_count = 0

        for (season_num, ep_num), status in episodes_to_tag.items():
            try:
                episode = episode_map.get((season_num, ep_num))
                
                if not episode:
                    logger.warning(f"Episode S{season_num:02d}E{ep_num:02d} for '{show_title}' not found in the pre-fetched list from Plex. Check your season order matches between Sonarr and Plex")
                    continue
                
                current_labels = [label.tag for label in episode.labels]
                existing_managed_tags = [tag for tag in current_labels if tag in self.managed_tags]

                if status in existing_managed_tags and len(existing_managed_tags) == 1:
                    logger.debug(f"Episode S{season_num:02d}E{ep_num:02d} already has correct tag '{status}'. Skipping")
                    skipped_count += 1
                    continue

                log_prefix = "[DRY RUN] " if dry_run else ""
                abs_num_str = f"(Absolute Ep: {ep_key_to_abs_num.get((season_num, ep_num), 'N/A')})"
                
                if existing_managed_tags:
                    logger.info(f"{log_prefix}Removing old/incorrect tags {existing_managed_tags} from S{season_num:02d}E{ep_num:02d} {abs_num_str} ('{episode.title}')")
                    if not dry_run:
                        episode.removeLabel(existing_managed_tags, locked=False)

                logger.info(f"{log_prefix}Adding tag '{status}' to S{season_num:02d}E{ep_num:02d} {abs_num_str} ('{episode.title}')")
                if not dry_run:
                    episode.addLabel(status, locked=False)
                
                if status in tag_counts:
                    tag_counts[status] += 1

            except Exception as e:
                logger.error(f"Failed to update tags for S{season_num:02d}E{ep_num:02d} of '{show_title}': {e}")
        
        total_updated = sum(tag_counts.values())
        logger.info(f"Processing complete for '{show_title}'")
        logger.info(f"  Episodes updated: {total_updated}")
        logger.info(f"  Episodes skipped (already tagged): {skipped_count}")
        if total_updated > 0:
            logger.info("  Tag summary for updated episodes:")
            for tag, count in tag_counts.items():
                if count > 0:
                    logger.info(f"    {tag}: {count}")