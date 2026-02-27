<a className="gh-badge" href="https://datahub.io/collections/football"><img src="https://badgen.net/badge/icon/View%20on%20datahub.io/orange?icon=https://datahub.io/datahub-cube-badge-icon.svg&label&scale=1.25" alt="badge" /></a>

# Football datasets

This repository includes 5 major Europe leagues:

- English Premier League – https://datahub.io/core/english-premier-league
- Spanish La Liga – https://datahub.io/core/spanish-la-liga
- Italian Serie A – https://datahub.io/core/italian-serie-a
- German Bundesliga – https://datahub.io/core/german-bundesliga
- French Ligue 1 – https://datahub.io/core/french-ligue-1

Each league has data for the all the seasons. The data is updated on daily basis via Github-Actions.

## Data

The data is sourced from the `https://www.football-data.co.uk/` website, datasets range starts from 1993 up to current year.

## Preparation

You need Python version >=3.9:

- Install requirements using `pip install -r scripts/requirements.txt`
- Update datasets from source using `python scripts/process.py`
- Generate datapackage metadata using `python scripts/package.py`

## Preprocessing and Data Comprehension

Run the full local pipeline:

1. Refresh raw league datasets: `python scripts/process.py`
2. Generate EDA + preprocessing outputs: `python eda/data_comprehension.py`

Execution order:

1. EDA / data comprehension (global + by season)
2. Preprocessing (clean feature-ready CSV outputs)

Generated structure:

- `data/comprehension/overview.md`
- `data/comprehension/season_index.csv`
- `data/comprehension/plots/01_global_missingness_top15.png`
- `data/comprehension/plots/02_global_result_mix_by_league.png`
- `data/comprehension/plots/03_global_total_goals_distribution.png`
- `data/comprehension/plots/04_global_avg_goals_by_season_league.png`
- `data/comprehension/plots/05_global_home_win_rate_by_season_league.png`
- `data/comprehension/plots/06_global_home_shots_vs_goals.png`
- `data/comprehension/plots/07_global_correlation_heatmap.png`
- `data/comprehension/plots/08_global_total_goals_boxplot_by_league.png`
- `data/comprehension/plots/09_global_cards_by_league.png`
- `data/comprehension/plots/10_global_matches_by_month.png`
- `data/comprehension/plots/by_league/<league>/01_ftr_distribution.png`
- `data/comprehension/plots/by_league/<league>/02_avg_total_goals_by_season.png`
- `data/comprehension/plots/by_league/<league>/03_missingness_top12.png`
- `data/comprehension/plots/by_league/<league>/04_home_win_rate_by_season.png`
- `data/comprehension/plots/by_league/<league>/by_season/season-xxxx.png`
- `data/processed/all_leagues/matches_clean.csv`
- `data/processed/by_league/<league>/matches_clean.csv`
- `data/processed/by_league/<league>/by_season/season-xxxx.csv`

Main preprocessing transformations:

- Keep canonical columns from `datasets/*/season-*.csv`
- Parse `Date` to a proper datetime field (`match_date`)
- Standardize text fields (`home_team`, `away_team`, `referee`, result labels)
- Convert numeric match stats to numeric types
- Remove duplicate matches using league/season/date/teams keys
- Create derived features: `goal_diff`, `total_goals`, `home_win`, `draw`, `away_win`

Data comprehension outputs include:

- Global dataset profile (volume, leagues, date range, missingness)
- Professional plot suite (global + by league + by season)
- Seasonal index table: `data/comprehension/season_index.csv`

## Automation

Up-to-date (auto-updates every day) football dataset could be found on the datahub.io: https://datahub.io/core/football-datasets

## Packaging datasets

Each directory in `datasets/` directory is a data package. It has a common `schema.json` for all its resources. You need to run `python package.py` from root directory to generate `datapackage.json` for each data package.

## License

This Data Package is made available under the Public Domain Dedication and License v1.0 whose full text can be found at: http://www.opendatacommons.org/licenses/pddl/1.0/
