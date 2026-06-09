"""
Shared utilities for Eurovision Fantasy League simulation scripts.

This module provides common functions to avoid code duplication across:
- Data preprocessing and tier assignment
- Draft simulation logic
- Score calculation and aggregation
"""

import pandas as pd
import numpy as np


def assign_tiers(df, tier1_size=10, tier2_size=10):
    """
    Assign countries to tiers based on year ranking.
    
    Tier assignment strategy:
    - Tier 1: Direct qualifiers + top semi performers (up to tier1_size total)
    - Tier 2: Next tier2_size countries by semi score
    - Tier 3: All remaining countries
    
    Args:
        df: DataFrame with columns ['year', 'direct_qualifier_10', 'semi_total_points']
        tier1_size: Number of countries in Tier 1 per year (default 10)
        tier2_size: Number of countries in Tier 2 per year (default 10)
        
    Returns:
        DataFrame with 'tier' column added (1, 2, or 3)
    """
    df = df.copy()
    df['tier'] = 0  # Initialize
    
    for year in df['year'].unique():
        year_mask = df['year'] == year
        year_data = df[year_mask].copy()
        
        # Start with direct qualifiers in Tier 1
        direct_qual_mask = year_mask & (df['direct_qualifier_10'] == 1)
        df.loc[direct_qual_mask, 'tier'] = 1
        num_tier1 = direct_qual_mask.sum()
        
        # Get non-direct qualifiers sorted by semi score
        non_dq = year_data[year_data['direct_qualifier_10'] == 0].copy()
        non_dq = non_dq.sort_values('semi_total_points', ascending=False)
        
        # Fill Tier 1 to target size
        tier1_needed = max(0, tier1_size - num_tier1)
        if tier1_needed > 0 and len(non_dq) > 0:
            tier1_adds = non_dq.iloc[:tier1_needed]
            for idx in tier1_adds.index:
                df.loc[idx, 'tier'] = 1
        
        # Next tier2_size = Tier 2
        tier2_start = tier1_needed
        tier2_end = tier2_start + tier2_size
        if len(non_dq) > tier2_start:
            tier2_countries = non_dq.iloc[tier2_start:tier2_end]
            for idx in tier2_countries.index:
                df.loc[idx, 'tier'] = 2
        
        # Rest = Tier 3
        tier3_start = tier2_end
        if len(non_dq) > tier3_start:
            tier3_countries = non_dq.iloc[tier3_start:]
            for idx in tier3_countries.index:
                df.loc[idx, 'tier'] = 3
    
    return df


def pick_country(available_pool, strategy):
    """
    Pick best country from pool based on player strategy.
    
    Args:
        available_pool: DataFrame of available countries with 'tier' and 'semi_total_points'
        strategy: One of 'tier1', 'tier2', 'tier3'
        
    Returns:
        Series representing the picked country, or None if pool empty
    """
    if len(available_pool) == 0:
        return None
    
    # Determine preferred tier based on strategy
    if strategy == 'tier1':
        preferred_tier = 1
    elif strategy == 'tier2':
        preferred_tier = 2
    else:  # tier3
        preferred_tier = 3
    
    # Try to pick from preferred tier first (highest semi score)
    preferred = available_pool[available_pool['tier'] == preferred_tier]
    if len(preferred) > 0:
        return preferred.nlargest(1, 'semi_total_points', keep='first').iloc[0]
    
    # Fallback: pick highest semi score from any tier
    return available_pool.nlargest(1, 'semi_total_points', keep='first').iloc[0]


def simulate_year(year_data, players, player_order, token_values, tier_to_token, 
                  penalty_mode='full'):
    """
    Simulate one year of the fantasy league.
    
    Args:
        year_data: DataFrame for one year with all country data
        players: Dict mapping player ID to {'strategy': 'tier1/tier2/tier3'}
        player_order: List of player IDs in draft order (e.g., ['A', 'B', 'C', ...])
        token_values: Dict like {'Bronze': {'bonus': 5, 'penalty': 2}, ...}
        tier_to_token: Dict mapping tier number to token type (e.g., {1: 'Bronze', 2: 'Silver', 3: 'Gold'})
        penalty_mode: One of:
            - 'full': Apply penalties when tokens placed on owned countries (default)
            - 'none': No penalties applied
            - 'winner_only': Penalties only if placed on champion
            
    Returns:
        Dict with keys:
            - 'year': int
            - 'champion': str (country name)
            - 'champion_owner': str (player ID) or None
            - 'player_base_scores': dict {player: score}
            - 'player_token_scores': dict {player: score} (net: bonuses - penalties)
            - 'player_token_bonuses': dict {player: score}
            - 'player_token_penalties': dict {player: score}
            - 'player_total_scores': dict {player: score}
            - 'player_tokens': dict {player: {token_type: count}}
            - 'player_final_roster': dict {player: [country_rows]}
    """
    # Separate by semi-final
    semi1 = year_data[year_data['semi_final'].astype(str) == '1'].copy()
    semi2 = year_data[year_data['semi_final'].astype(str) == '2'].copy()
    
    if len(semi1) < len(player_order) or len(semi2) < len(player_order):
        return None  # Not enough countries to draft
    
    # Initialize player data
    player_countries = {p: [] for p in player_order}
    player_tokens = {p: {tt: 0 for tt in token_values.keys()} for p in player_order}
    drafted_countries = []
    
    # DRAFT 1: Before Semi-Final 1 (2 picks each, snake order)
    draft1_order = player_order + player_order[::-1]
    draft1_pool = semi1.copy()
    
    for player in draft1_order:
        available = draft1_pool[~draft1_pool['country'].isin(drafted_countries)]
        pick = pick_country(available, players[player]['strategy'])
        if pick is not None:
            player_countries[player].append(pick)
            drafted_countries.append(pick['country'])
    
    # SEMI-FINAL 1: Mint tokens for qualifiers
    for player in player_order:
        for country_row in player_countries[player]:
            semi_val = country_row['semi_final']
            if semi_val == 1 or semi_val == '1':
                if country_row['qualified_10'] == 1 or country_row['direct_qualifier_10'] == 1:
                    token_type = tier_to_token[country_row['tier']]
                    player_tokens[player][token_type] += 1
    
    # DRAFT 2: Before Semi-Final 2 (2 more picks each, snake order reversed)
    draft2_order = player_order[::-1] + player_order
    draft2_pool = semi2.copy()
    
    for player in draft2_order:
        available = draft2_pool[~draft2_pool['country'].isin(drafted_countries)]
        pick = pick_country(available, players[player]['strategy'])
        if pick is not None:
            player_countries[player].append(pick)
            drafted_countries.append(pick['country'])
    
    # SEMI-FINAL 2: Mint tokens for qualifiers
    for player in player_order:
        for country_row in player_countries[player]:
            semi_val = country_row['semi_final']
            if semi_val == 2 or semi_val == '2':
                if country_row['qualified_10'] == 1 or country_row['direct_qualifier_10'] == 1:
                    token_type = tier_to_token[country_row['tier']]
                    player_tokens[player][token_type] += 1
    
    # POST-SEMI CLEANUP: Count qualifiers per player
    player_qualifiers = {}
    for player in player_order:
        qualifiers = [c for c in player_countries[player] 
                     if c['qualified_10'] == 1 or c['direct_qualifier_10'] == 1]
        player_qualifiers[player] = qualifiers
    
    # RESCUE DRAFT: Players with <3 qualifiers draft from unowned qualifiers
    all_qualifiers = year_data[
        (year_data['qualified_10'] == 1) | (year_data['direct_qualifier_10'] == 1)
    ].copy()
    
    for player in player_order:
        while len(player_qualifiers[player]) < 3:
            available_rescue = all_qualifiers[~all_qualifiers['country'].isin(drafted_countries)]
            if len(available_rescue) == 0:
                break
            rescue_pick = available_rescue.nlargest(1, 'semi_total_points', keep='first').iloc[0]
            player_countries[player].append(rescue_pick)
            player_qualifiers[player].append(rescue_pick)
            drafted_countries.append(rescue_pick['country'])
    
    # FINAL ROSTER LOCK: Select best 3 qualifiers
    player_final_roster = {}
    for player in player_order:
        if len(player_qualifiers[player]) >= 3:
            sorted_qual = sorted(player_qualifiers[player], 
                               key=lambda x: x['final_total_points'], reverse=True)
            player_final_roster[player] = sorted_qual[:3]
        else:
            player_final_roster[player] = player_qualifiers[player]
    
    # Calculate base score (sum of 3 locked countries)
    player_base_scores = {}
    for player in player_order:
        player_base_scores[player] = sum(c['final_total_points'] for c in player_final_roster[player])
    
    # Find the champion
    champion_row = year_data[year_data['is_champion'] == 1].iloc[0]
    champion_country = champion_row['country']
    champion_owner = None
    
    for player in player_order:
        roster_countries = [c['country'] for c in player_final_roster[player]]
        if champion_country in roster_countries:
            champion_owner = player
            break
    
    # TOKEN PLACEMENT: Players predict the champion from top 3 finishers
    all_qualifiers_list = year_data[
        (year_data['qualified_10'] == 1) | (year_data['direct_qualifier_10'] == 1)
    ].copy()
    top_3_finishers = all_qualifiers_list.nlargest(3, 'final_total_points')['country'].tolist()
    
    player_token_placements = {p: [] for p in player_order}
    
    for player in player_order:
        tokens_to_place = []
        for token_type, count in player_tokens[player].items():
            tokens_to_place.extend([token_type] * count)
        
        if len(tokens_to_place) > 0:
            for token in tokens_to_place:
                predicted_champion = np.random.choice(top_3_finishers)
                player_token_placements[player].append((token, predicted_champion))
    
    # FINAL SCORING: Calculate token bonuses/penalties based on penalty_mode
    player_token_scores = {p: 0 for p in player_order}
    player_token_bonuses = {p: 0 for p in player_order}
    player_token_penalties = {p: 0 for p in player_order}
    
    if penalty_mode == 'none':
        # No penalties: only bonuses for correct predictions
        for player in player_order:
            for token_type, placed_country in player_token_placements[player]:
                if placed_country == champion_country:
                    bonus = token_values[token_type]['bonus']
                    player_token_scores[player] += bonus
                    player_token_bonuses[player] += bonus
    
    elif penalty_mode == 'winner_only':
        # Old rules: penalties only when token placed on champion
        for player in player_order:
            for token_type, placed_country in player_token_placements[player]:
                if placed_country == champion_country:
                    bonus = token_values[token_type]['bonus']
                    player_token_scores[player] += bonus
                    player_token_bonuses[player] += bonus
                    
                    # Apply penalty to champion owner if different player
                    if champion_owner is not None and champion_owner != player:
                        penalty = token_values[token_type]['penalty']
                        player_token_scores[champion_owner] -= penalty
                        player_token_penalties[champion_owner] += penalty
    
    else:  # 'full' mode (default)
        # New rules: penalties when token ACTIVATES and is placed on owned country
        # (Original implementation: penalty only on activated tokens)
        for player in player_order:
            for token_type, placed_country in player_token_placements[player]:
                # Check if token activates (correct prediction)
                if placed_country == champion_country:
                    # Award bonus
                    bonus = token_values[token_type]['bonus']
                    player_token_scores[player] += bonus
                    player_token_bonuses[player] += bonus
                    
                    # Apply penalty to champion owner if different player
                    if champion_owner is not None and champion_owner != player:
                        penalty = token_values[token_type]['penalty']
                        player_token_scores[champion_owner] -= penalty
                        player_token_penalties[champion_owner] += penalty
    
    # Total scores
    player_total_scores = {}
    for player in player_order:
        player_total_scores[player] = player_base_scores[player] + player_token_scores[player]
    
    return {
        'year': int(year_data['year'].iloc[0]),
        'champion': champion_country,
        'champion_owner': champion_owner,
        'player_base_scores': player_base_scores,
        'player_token_scores': player_token_scores,
        'player_token_bonuses': player_token_bonuses,
        'player_token_penalties': player_token_penalties,
        'player_total_scores': player_total_scores,
        'player_tokens': player_tokens,
        'player_final_roster': player_final_roster
    }


def evaluate_configuration(df, players, player_order, token_values, tier_to_token, penalty_mode='full'):
    """
    Evaluate a single configuration by running simulation across all years.
    
    This is the core evaluation function used by all optimization scripts.
    It runs the simulation for each year with the given configuration and
    aggregates the results to compute balance metrics.
    
    Args:
        df: DataFrame with preprocessed data and tier assignments
        players: Dict mapping player IDs to strategy info
        player_order: List of player IDs in draft order
        token_values: Dict with token bonuses and penalties
        tier_to_token: Dict mapping tier numbers to token types
        penalty_mode: 'none', 'winner_only', or 'full'
        
    Returns:
        Dict with:
            - 'avg_scores': List of average scores per player
            - 'std_dev': Standard deviation of average scores
            - 'range': Difference between max and min average scores
            - 'results': List of individual year results (for detailed analysis)
    """
    from collections import defaultdict
    
    years = sorted(df['year'].unique())
    results = []
    
    for year in years:
        year_data = df[df['year'] == year]
        result = simulate_year(
            year_data=year_data,
            players=players,
            player_order=player_order,
            token_values=token_values,
            tier_to_token=tier_to_token,
            penalty_mode=penalty_mode
        )
        if result is not None:
            results.append(result)
    
    # Aggregate scores across all years
    all_scores = defaultdict(list)
    for result in results:
        for player in player_order:
            all_scores[player].append(result['player_total_scores'][player])
    
    # Calculate balance metrics
    avg_scores = [np.mean(all_scores[p]) for p in player_order]
    std_dev = np.std(avg_scores)
    score_range = max(avg_scores) - min(avg_scores)
    
    return {
        'avg_scores': avg_scores,
        'std_dev': std_dev,
        'range': score_range,
        'results': results
    }
