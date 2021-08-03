poetry run isort .
poetry run autoflake -r -i --remove-all-unused-imports .
poetry run black .