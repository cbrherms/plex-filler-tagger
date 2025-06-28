class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.shows = []
        self.plex_library_name = "Anime" # Default value

    def load(self):
        import yaml

        with open(self.config_file, 'r') as file:
            config_data = yaml.safe_load(file)
            
            self.plex_library_name = config_data.get('plex_library_name', self.plex_library_name)

            shows_data = config_data.get('plex_shows', [])
            self.validate(shows_data)
            self.shows = shows_data

    def validate(self, shows_data):
        required_fields = ['plex_name', 'sonarr_id', 'animefillerlist_slug']

        for show in shows_data:
            for field in required_fields:
                if field not in show:
                    raise ValueError(f'Missing required field: {field} in show configuration')