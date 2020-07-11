DESCRIPTION = "Justlooks api"
ENVIRONMENT = "dev"

config = {
    "module_name": __name__,
    "description": DESCRIPTION,
    "environment": ENVIRONMENT,
    "default_log_level": 20,
    "host": "localhost",
    "port": 5000,
    "debug": True,
    "postgrest_host": "http://0.0.0.0:3000",
}
