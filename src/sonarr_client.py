import logging
import sonarr
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import requests

logger = logging.getLogger(__name__)

class SonarrClient:
    """A client for interacting with the Sonarr API"""

    def __init__(self, base_url: str, api_key: str):
        """
        Initializes the SonarrClient

        Args:
            base_url: The base URL of the Sonarr instance
            api_key: The API key for Sonarr
        """
        self.base_url = base_url
        self.api_key = api_key
        self._api_client = None
        self.configuration = sonarr.Configuration(host=self.base_url)
        self.configuration.api_key["X-Api-Key"] = self.api_key

    def connect(self):
        """Establishes and tests the connection to the Sonarr API"""
        try:
            self._api_client = sonarr.ApiClient(self.configuration)
            sonarr.SystemApi(self._api_client).get_system_status()
            logger.info("Successfully connected to Sonarr")
        except Exception as e:
            logger.error(f"Failed to connect to Sonarr at {self.base_url}: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.exceptions.RequestException))
    def get_show_episodes(self, series_id: int) -> list:
        """
        Retrieves all episodes for a given Sonarr series ID

        Args:
            series_id: The Sonarr ID of the series

        Returns:
            A list of episode objects from the sonarr-py library
        """
        if not self._api_client:
            logger.error("Not connected to Sonarr. Call connect() first")
            return []
        
        try:
            logger.info(f"Fetching episodes for series ID: {series_id}")
            api_instance = sonarr.EpisodeApi(self._api_client)
            episodes = api_instance.list_episode(series_id=series_id)
            logger.info(f"Found {len(episodes)} episodes for series ID: {series_id}")
            return episodes
        except Exception as e:
            logger.error(f"Failed to get episodes for series ID {series_id}: {e}")
            return []