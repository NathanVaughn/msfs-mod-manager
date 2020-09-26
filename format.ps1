isort src --multi-line=3 --trailing-comma --force-grid-wrap=0 --use-parentheses --line-width=88
autoflake -r -i --remove-all-unused-imports --remove-unused-variables src
black src