# Plex Filler Tagger

## Overview
The `plex-filler-tagger` is a Python application designed to manage episode tags in Plex based on their status from AnimeFillerList.com. It fetches episode statuses (Manga Canon, Filler, etc.), correlates them with your library via Sonarr, and applies them as tags in Plex. This facilitates the creation of smart collections and overlays in tools like Kometa.

## Features
- Connects to Plex and Sonarr APIs to retrieve and manage episode information.
- Parses episode statuses directly from AnimeFillerList.com.
- Supports multiple anime shows via a YAML configuration file.
- Applies status as tags to episodes in Plex (e.g., `MangaCanon`, `Filler`).
- **Dry Run Mode**: When setting the `DRY_RUN` environment variable to `true`, logs the changes it *would* make without modifying your Plex library.
- **Debug Mode**: Enable verbose logging for troubleshooting by setting `DEBUG=true` environment variable.

## Installation

The recommended way to run this application is with Docker or Docker Compose. A manual Python installation is also available for development or special use cases.

### Method 1: Docker Compose (Recommended)

This is the easiest way to manage the container.

1.  **Create a `docker-compose.yaml` file:**
    Copy the provided `docker-compose.yaml.example` to `docker-compose.yaml` and edit it with your details.

2.  **Create your `config.yaml`:**
    Create a `config.yaml` file in the same directory (or your preferred config location) and populate it with your show information. See the **Configuration** section below.

3.  **Update the volume path:**
    In your `docker-compose.yaml`, change `/path/to/your/config/config.yaml` to the actual path of your `config.yaml` file.

4.  **Run the container:**
    ```bash
    docker-compose up -d
    ```

### Method 2: Docker Run

1.  **Prepare your `config.yaml` file:**
    Create a `config.yaml` file on your host machine and populate it with your show information. See the **Configuration** section below.

2.  **Run the Docker Container:**
    Use the following command, replacing the environment variables and volume path with your own details.

    ```bash
    docker run --rm -it \
      --name plex-filler-tagger \
      -e PLEX_URL="http://your_plex_server_url:32400" \
      -e API_KEY_PLEX="your_plex_api_key" \
      -e SONARR_URL="http://your_sonarr_server_url:8989" \
      -e API_KEY_SONARR="your_sonarr_api_key" \
      -v /path/to/your/config.yaml:/config/config.yaml \
      ghcr.io/cbrherms/plex-filler-tagger:1.1.0
    ```
    *Make sure to replace `/path/to/your/config.yaml` with the absolute path to your configuration file.*

### Method 3: Manual Installation

This method is for running the script directly on your machine.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/cbrherms/plex-filler-tagger.git
    cd plex-filler-tagger
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the application:**
    *   Copy the example configuration files:
        ```bash
        cp config.yaml.example config.yaml
        cp .env.example .env
        ```
    *   Edit `config.yaml` and `.env` with your server details, API keys, and show information. The script will load credentials from the `.env` file automatically.

5.  **Run the script:**
    ```bash
    python -m src
    ```
    *To use a non-default config path, set the `CONFIG_PATH` environment variable: `CONFIG_PATH=my.yaml python -m src`*


## Configuration

### `config.yaml`
This file defines which shows the script should process. When using Docker, you must set the `CONFIG_PATH` environment variable to point to the location of this file inside the container (e.g., `/config/config.yaml`).

-   `plex_library_name`: The name of your Anime library in Plex (e.g., "Anime", "Anime Shows", etc).
-   `plex_shows`: A list of shows to process.
    -   `plex_name`: The name of the show as it appears in your Plex library.
    -   `sonarr_id`: The ID of the show in Sonarr. To find this, go to the series page in Sonarr and open your browser's developer tools (usually F12). Go to the "Network" tab, refresh the page, and look for an API call like `details?seriesId=15`. The number is the ID.
    -   `animefillerlist_slug`: The show's URL slug from AnimeFillerList.com (e.g., for `https://www.animefillerlist.com/shows/one-piece`, the slug is `one-piece`).

**Example `config.yaml`:**
```yaml
plex_library_name: "Anime"

plex_shows:
  - plex_name: "One Piece"
    sonarr_id: 15
    animefillerlist_slug: "one-piece"
  - plex_name: "Naruto Shippuden"
    sonarr_id: 13
    animefillerlist_slug: "naruto-shippuden"
```

### Environment Variables
These are used to configure the application, especially for Docker. For manual installation, you can place these in a `.env` file.

| Variable | Description | Default |
|---|---|---|
| `PLEX_URL` | Your Plex server URL | (none) |
| `API_KEY_PLEX` | Your Plex API token | (none) |
| `SONARR_URL` | Your Sonarr instance URL | (none) |
| `API_KEY_SONARR` | Your Sonarr API key | (none) |
| `CONFIG_PATH` | Manually override the default config file location | (none) |
| `DRY_RUN` | Set to `true` to prevent changes to Plex | `false` |
| `DEBUG` | Set to `true` to enable verbose debug logging | `false` |
| `TZ` | Set the timezone for logging | `Etc/UTC` |


## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.