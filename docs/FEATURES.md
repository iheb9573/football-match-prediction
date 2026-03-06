# Feature Engineering - Football Match Prediction

Comprehensive guide to all features used in the prediction model.

## Overview

The feature engineering system is organized into three layers:
1. **Base Features** (23 numeric + 3 categorical) - Existing Elo-based system
2. **Player Features** [NEW] (12 numeric) - Squad-level aggregations
3. **Advanced Features** [NEW] (5 numeric) - Interaction and derived features

**Total: 40 features (23+12+5) for modeling**

---

## Layer 1: Base Features (Existing)

### 1.1 Elo Rating System

**System Parameters:**
- `K_FACTOR = 20` - Learning rate for rating updates
- `HOME_ADVANTAGE = 60` - ELO points advantage for home team
- `INITIAL_RATING = 1500.0` - Starting ELO for new teams
- **Seasonal Reset:** ELO regresses 75% to 1500 at season start

**Process:**
```python
For each match chronologically:
  1. Get home_elo_pre, away_elo_pre from team state
  2. Calculate expected home win probability using Elo formula
  3. Compare vs actual result
  4. Update both teams' ELO ratings by K_FACTOR
  5. Store updated ELO in team state for next match
```

**Features Generated:**
- `home_elo_pre`: Home team's ELO before match (float, typically 1300-1700)
- `away_elo_pre`: Away team's ELO before match (float, typically 1300-1700)
- `elo_diff`: `home_elo_pre - away_elo_pre + HOME_ADVANTAGE` (float, -300 to +300)

**Interpretation:**
- Positive `elo_diff` → Home team favored (home advantage + strength)
- Negative `elo_diff` → Away team favored despite playing away
- Typical range: -150 to +150 (extreme ±300 for dominant vs weak teams)

**Validation:**
- ✓ No data leakage (ELO only uses past matches)
- ✓ Properly handles new teams (initialized at 1500)
- ✓ Respects season boundaries (reset at new season)

---

### 1.2 Rolling Statistics (5-Match Windows)

**Features Calculated:**

#### Season Performance (From season start)
- `home_matches_played_pre`: Count of matches played so far in season (int, 0-38)
- `home_points_per_game_pre`: Total season points / matches played (float, 0-3)
- `home_goal_diff_per_game_pre`: (Goals for - Goals against) / matches (float, -3 to +3)

#### Recent Form (Last 5 Matches)
- `home_recent_points_avg_pre`: Mean points in last min(5, matches) (float, 0-3)
- `home_recent_goal_diff_avg_pre`: Mean goal diff in last 5 matches (float, -3 to +3)

**Interpretation:**
- High PPG + high recent points → Form is consistent with season
- Recent form > season PPG → Team improving (positive momentum)
- Recent form < season PPG → Team declining (concerning trend)

**Calculation Example:**
```
Team with 10 season matches: 4W 2D 4L = 14 points → PPG = 1.4
Last 5: W W D L W = 7 points → Recent avg = 1.4 (consistent)
```

**Handling Missing Data:**
- For early season matches (< 5 games), use available matches only
- For season start (< 1 match), use 0 as placeholder
- Imputation fills remaining NaN with league/global median

---

### 1.3 Temporal Features

- `month`: Match month (int, 1-12)
  - Captures seasonal variation in form, weather, player fitness
  - December/January typically lower quality (holiday congestion)

- `weekday`: Day of week (int, 0=Mon...6=Sun)
  - Midweek matches often different recovery vs weekend
  - Some teams stronger on Thursday (European competition days)

**Encoding:** One-hot encoded in preprocessing

---

### 1.4 Team Identifiers (Categorical)

- `league_code`: League identifier (5 values: EPL, LaLiga, SerieA, Bundesliga, Ligue1)
- `home_team`: Team name (40-50 unique values per league)
- `away_team`: Team name (same universe as home_team)

**Purpose:**
- Captures league-specific quality differences
- Encodes team-specific strength beyond aggregate stats
- One-hot encoded in preprocessing (creates 90+ binary features)

**Note:** These are raw team identifiers and market value; team ranking is learned by the model

---

### 1.5 Derived Base Features

- `ppg_diff`: `home_ppg - away_ppg` (float, -3 to +3)
- `goal_diff_pg_diff`: `home_goal_diff_pg - away_goal_diff_pg` (float, -6 to +6)
- `recent_points_diff`: `home_recent_points_avg - away_recent_points_avg` (float, -3 to +3)
- `recent_goal_diff_diff`: `home_recent_goal_diff_avg - away_recent_goal_diff_avg` (float, -6 to +6)
- `rest_days_diff`: `home_rest_days - away_rest_days` (float, -30 to +30)

**Purpose:** Pre-compute differences to aid model learning

---

## Layer 2: Player Features [NEW]

### 2.1 Squad Age Metrics

**Data Source:** `player_profiles.csv`
- Loaded for each team from official roster data
- Snapshot taken 1 day before match (no data leakage)

**Features:**
- `home_squad_avg_age_pre`: Mean player age in home squad (float, 22-32)
- `away_squad_avg_age_pre`: Mean player age in away squad (float, 22-32)

**Interpretation:**
- Young squads (avg 23-24): High energy, lower experience
- Mature squads (avg 28-30): Experience, potential fatigue
- Youth 1-2 years advantage in late-season matches (fitness)

**Handling Missing Data:**
- If player_profiles missing for historical seasons:
  - Impute with league-season median
  - Create 'age_data_available' flag for SHAP analysis

---

### 2.2 Squad Market Value

**Data Source:** `ml_team_features.csv`
- Transfer market valuations (in millions EUR)
- Updated seasonally/quarterly

**Features:**
- `home_squad_market_value_pre`: Total squad value, home (float, 100M-500M)
- `away_squad_market_value_pre`: Total squad value, away (float, 100M-500M)

**Interpretation:**
- Market value strongly correlated with team quality
- Rich squads → Better recruitment → Stronger teams
- Typically: Top 6 teams 300M+, mid-table 100-200M, relegation 50M

**Notes:**
- These are pre-match snapshots (not real-time during match)
- No look-ahead bias (market values from before match-date)

---

### 2.3 Squad Composition

**Data Source:** Player position classifications in `player_profiles.csv`

**Features:**
- `home_num_defenders`: Count of players with CB/LB/RB/LWB/RWB position (int, 8-12)
- `home_num_midfielders`: Count of CM/CDM/CAM/LM/RM (int, 6-10)
- `home_num_forwards`: Count of ST/CF/LW/RW (int, 2-5)
- `home_num_goalkeepers`: Count of GK (int, 1-3)
- *(Same 4 features for away_* variables)

**Interpretation:**
- Defensive-heavy squad (12 DEF, 7 MID, 3 FOR): Emphasis on solidity
- Offensive-heavy squad (9 DEF, 8 MID, 4 FOR): Creative, attacking approach
- Affects team playing style and injury impact

**Ratios Derived:**
- `home_def_mid_ratio`: Defenders / Midfielders (float, 1.0-1.8)
- `home_mid_fwd_ratio`: Midfielders / Forwards (float, 1.5-3.5)

High defender ratio → Defensive stability but less attacking threat

---

### 2.4 Injury Impact

**Data Source:** `injury_history.csv`
- Tracks suspended/injured players per team per date
- Snapshot taken 1 day before match

**Features:**
- `home_injury_count_pre`: Number of key players out (int, 0-5)
- `home_injury_rate`: Injured % of squad (float, 0-20%)
- *(Same 2 features for away_*)

**Impact on Predictions:**
- 1 injured player (1-2%): Minimal impact on strong teams
- 3+ injured players (5-10%): Significant performance hit
- Especially critical if injuries to defenders or star players

**Handling Missing Data:**
- Historical injury data sparse (many seasons unavailable)
- For seasons without injury_history:
  - Impute with 0 injuries (assume healthy unless documented)
  - Create 'injury_data_available' flag

---

## Layer 3: Advanced Features [NEW]

### 3.1 Interaction Features

**Computing Strategy:**
1. Calculate base + player features for both teams
2. Create multiplicative/additive combinations
3. Engineer cross-team interactions

#### Feature 1: Form Interaction
```python
home_form_vs_away_form = home_recent_points_avg * away_recent_points_avg
```
- Range: 0 - 9 (0 = one team in terrible form, 9 = both excellent)
- Captures quality of potential match (Mismatch vs Close contest)
- Low value (0-1) → Likely one-sided match
- High value (4-9) → Likely competitive match

#### Feature 2: ELO × Form Product
```python
elo_advantage_with_form = elo_diff * home_recent_points_avg
```
- Amplifies ELO advantage when home team in good form
- Dampens ELO advantage when home team struggling
- Accounts for momentum alongside structural strength

#### Feature 3: Rest Disparity
```python
rest_disparity = abs(home_rest_days - away_rest_days)
```
- Quantifies rest advantage (0 = equal, 1-10 = disparity)
- High disparity favors rested team
- Relevant for midweek matches vs weekend recovery

#### Feature 4: Injury Impact Difference
```python
injury_impact = home_injury_rate - away_injury_rate
```
- Positive → Home team less impacted by injuries
- Negative → Away team has healthier squad
- Amplifies injury importance in predictions

---

### 3.2 Advanced Temporal Features

#### Feature 1: Match Quarter
```python
match_quarter = assign_quarter_of_season(match_date, season_start)
# Quarter 1: Aug-Oct (early, teams settling)
# Quarter 2: Nov-Jan (mid-season, settled form)
# Quarter 3: Feb-Apr (title race, promotion battle)
# Quarter 4: Apr-May (final stretch, high stakes)
```

**Interpretation:**
- Q1: New lineups, adjusting tactics (more unpredictable)
- Q2: Established form (most predictable)
- Q3: Increased stakes → More intensity, fewer surprises
- Q4: Final matches → Critical outcomes, less experimentation

#### Feature 2: Days Since Last Match
```python
days_since_match = match_date - last_match_date
# Typical: 3 days (weekend to midweek or vice versa)
# Long: 7+ days (international break, winter break)
# Short: 1-2 days (rare, fixture congestion)
```

**Impact:**
- 3 days (normal): Standard recovery
- 1-2 days (short): Fatigue effect (road teams more affected)
- 7+ days (long): Cold effect (loss of momentum)

---

### 3.3 Polynomial Features (Optional)

Can be enabled in `config/features.yaml` for non-linear effects:

- `elo_diff_squared`: `elo_diff ** 2`
  - Capture extreme ELO mismatches (elite vs relegation)
  - Low impact for typical cases

- `ppg_diff_squared`: `ppg_diff ** 2`
  - Amplify large form differences

**Note:** Disabled by default (can increase overfitting). Enable only if validation improves.

---

## Feature Statistics & Distributions

### Base Features (Current Project Data)

| Feature | Type | Min | Median | Max | Std Dev |
|---------|------|-----|--------|-----|---------|
| elo_diff | numeric | -300 | 20 | 300 | 85 |
| ppg_diff | numeric | -3 | 0.3 | 3 | 0.8 |
| rest_days_diff | numeric | -30 | 0 | 30 | 4 |
| month | categorical | 1 | 8 | 12 | 3.3 |
| league_code | categorical | — | — | — | — |

### Player Features (Expected Ranges)

| Feature | Type | Min | Typical | Max |
|---------|------|-----|---------|-----|
| squad_avg_age | numeric | 23 | 27 | 32 |
| market_value (M) | numeric | 50 | 250 | 500 |
| num_defenders | int | 8 | 10 | 12 |
| injury_rate (%) | numeric | 0 | 2 | 15 |

### Advanced Features (Expected Ranges)

| Feature | Type | Min | Typical | Max |
|---------|------|-----|---------|-----|
| form_interaction | numeric | 0 | 1.5 | 9 |
| rest_disparity | int | 0 | 0 | 10 |
| match_quarter | int | 1 | 2 | 4 |

---

## Data Quality & Validation

### Pre-Match Integrity (No Leakage)
✓ All base features computed BEFORE match result known
✓ All player features from previous day snapshots
✓ ELO updated only after match result
✓ Future injury data not used

### Missing Data Handling
- Hierarchical imputation: (league, season) → league → global median
- Missing historical player data: Impute with league median, flag with 'available' column
- Zero-inflation for rare features (injuries, rest disparity)

### Outlier Treatment
- Extreme ELO diff (> 200): Valid for dominant vs weak teams
- Extreme rest disparity (> 14 days): International breaks, valid
- Market value outliers: Real (Manchester City 400M+), kept
- **Policy:** Non-destructive outlier flagging, not removal

### Categorical Encoding
- League: 5 categories → 5 binary features
- Teams: 100-150 categories → One-hot, handle_unknown='ignore'
- Month/Weekday: Already numeric (0-indexed)

---

## Feature Importance (Expected)

Based on historical analysis:

**Top 5 Most Important Features:**
1. elo_diff (10-12% contribution)
2. home_team (7-9% contribution)
3. home_recent_points_avg (5-7% contribution)
4. away_team (5-7% contribution)
5. league_code (4-6% contribution)

**Player Features Expected Impact:**
- squad_market_value: +2-3% importance
- squad_avg_age: +1-2% importance
- injury_rate: +0.5-1% importance

**Advanced Features Expected Impact:**
- form_interaction: +1-2% importance
- elo_form_product: +0.5-1% importance
- match_quarter: +0.5-1% importance

---

## Feature Engineering Best Practices

### DO ✓
- ✓ Compute all features based on data available BEFORE match
- ✓ Handle missing data systematically (no ad-hoc fill)
- ✓ Document feature creation logic
- ✓ Validate no temporal leakage
- ✓ Use domain knowledge (Elo system, rolling windows)
- ✓ Test feature importance on validation set

### DON'T ✗
- ✗ Use match result (goals) to create pre-match features
- ✗ Use post-match injury updates
- ✗ Look-ahead bias in any future-dated fields
- ✗ Remove outliers without investigation
- ✗ Create features that only work for certain leagues
- ✗ Forget to handle categorical encoding

---

## Summary: Feature Engineering Strategy

**Phase 1 (Current):** Base features (Elo + rolling stats) = **23 numeric + 3 categorical**
**Phase 2:** Add player features (squad aggregations) = **+12 numeric**
**Phase 3:** Add advanced features (interactions, temporal) = **+5 numeric**

**Total Engineered Features: 40**

Expected accuracy improvement:
- Phase 1 → Phase 2: +2-3% (player data is predictive)
- Phase 2 → Phase 3: +1-2% (interactions capture synergies)

**Final Feature Set:** Balanced mix of structural features (Elo, composition) and performance-based features (form, recent results, injuries)
