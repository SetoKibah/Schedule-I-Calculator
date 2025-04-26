"""
Schedule I Calculator
Handles calculations related to market value and profit margins for drug mixes.
"""

from src.game_data import BASE_MARKET_VALUES, MIXERS, EFFECTS, MARIJUANA_STRAINS, EFFECT_REACTIONS


def get_effects_from_mixers(base_product, mixer_list):
    """
    Determine the effects that would be applied to a product based on the mixers used.
    This uses a more accurate approach based on the wiki's specific replacement rules.
    
    Args:
        base_product (str): The base product or marijuana strain
        mixer_list (list): List of mixer names used in order
    
    Returns:
        list: List of effect names that would be applied to the product
    """
    from src.game_data import EFFECT_REPLACEMENTS
    
    # Start with inherent effect if it's a marijuana strain
    effects = []
    if base_product in MARIJUANA_STRAINS:
        strain_effect = MARIJUANA_STRAINS[base_product]["effect"]
        effects.append(strain_effect)
    
    # Process mixers in order
    for mixer in mixer_list:
        if mixer not in MIXERS:
            continue
        
        # First check if this mixer would replace any existing effects
        replacement_occurred = False
        for i, effect in enumerate(effects):
            if (effect, mixer) in EFFECT_REPLACEMENTS:
                # Replace the existing effect with the new one
                new_effect = EFFECT_REPLACEMENTS[(effect, mixer)]
                effects[i] = new_effect
                replacement_occurred = True
                break
        
        # If no replacement occurred, add the mixer's default effect
        if not replacement_occurred:
            default_effect = MIXERS[mixer]["effect"]
            if default_effect not in effects and len(effects) < 8:
                effects.append(default_effect)
    
    # Limit to 8 effects (game maximum)
    return effects[:8]


def calculate_market_value(base_product, effects_list, mixer_list=None):
    """
    Calculate the market value of a product with given effects.
    Uses a game-accurate formula with appropriate rounding.
    
    Args:
        base_product (str): The base product type (Marijuana, Methamphetamine, Cocaine)
                           or a specific marijuana strain
        effects_list (list): List of effect names applied to the product
        mixer_list (list, optional): List of mixers used (for special case handling)
    
    Returns:
        int: The rounded market value per unit
    """
    # Determine base value based on product type
    if base_product in BASE_MARKET_VALUES:
        base_value = BASE_MARKET_VALUES[base_product]
    elif base_product in MARIJUANA_STRAINS:
        base_value = MARIJUANA_STRAINS[base_product]["bud_value"]
    else:
        raise ValueError(f"Unknown product: {base_product}")
    
    # Calculate total multiplier
    multiplier_total = sum(EFFECTS[effect]["multiplier"] for effect in effects_list if effect in EFFECTS)
    
    # Calculate total value using the game's formula
    total_value = base_value * (1 + multiplier_total)
    
    # Round according to the game's rules
    if total_value % 1 == 0.5:
        return int(total_value)
    else:
        return round(total_value)


def calculate_mixer_cost(mixer_list):
    """
    Calculate the total cost of mixers used in a recipe.
    
    Args:
        mixer_list (list): List of mixer names used in the recipe
    
    Returns:
        int: The total cost of all mixers
    """
    return sum(MIXERS[mixer]["cost"] for mixer in mixer_list if mixer in MIXERS)


def calculate_product_cost(base_product, mixer_list):
    """
    Calculate the total cost of producing a product (base + mixers).
    
    Args:
        base_product (str): The base product or marijuana strain
        mixer_list (list): List of mixer names used
    
    Returns:
        int: The total production cost per unit
    """
    from src.game_data import PRODUCTION_INFO
    
    # Calculate base cost based on product type
    if base_product in MARIJUANA_STRAINS:
        # For marijuana, we need to account for yield (multiple buds per seed)
        seed_cost = MARIJUANA_STRAINS[base_product]["seed_cost"]
        # Use the average of min and max yield for the calculation
        min_yield, max_yield = MARIJUANA_STRAINS[base_product]["yield_range"]
        avg_yield = (min_yield + max_yield) / 2
        # Base cost is seed cost divided by average yield (cost per bud)
        base_cost = seed_cost / avg_yield
    elif base_product in PRODUCTION_INFO:
        # For other drugs with production info, calculate cost per unit
        ingredients_cost = PRODUCTION_INFO[base_product]["ingredients_cost"]
        yield_amount = PRODUCTION_INFO[base_product]["yield"]
        base_cost = ingredients_cost / yield_amount
    else:
        # Fallback for any other product types
        base_cost = BASE_MARKET_VALUES.get(base_product, 0)
    
    # Add mixer costs
    mixer_cost = calculate_mixer_cost(mixer_list)
    
    # Return total cost (base cost per unit + mixer costs) - rounded to nearest whole number
    return round(base_cost + mixer_cost)


def calculate_profit(base_product, mixer_list):
    """
    Calculate the profit for a mix.
    
    Args:
        base_product (str): The base product or marijuana strain
        mixer_list (list): List of mixer names used
    
    Returns:
        tuple: (market_value, total_cost, profit, profit_margin_percentage, effects_list, addictiveness)
    """
    from src.game_data import ADDICTIVENESS
    
    # Derive effects from mixers and base product
    effects_list = get_effects_from_mixers(base_product, mixer_list)
    
    market_value = calculate_market_value(base_product, effects_list, mixer_list)
    total_cost = calculate_product_cost(base_product, mixer_list)
    profit = market_value - total_cost
    
    # Calculate profit margin percentage
    if total_cost > 0:
        profit_margin = (profit / total_cost) * 100
    else:
        profit_margin = 0
    
    # Calculate addictiveness based on effects and base product
    base_addictiveness = 0
    if base_product in ADDICTIVENESS:
        base_addictiveness = ADDICTIVENESS[base_product]
    
    # Sum the addictiveness from all effects
    effect_addictiveness = sum(EFFECTS[effect]["addictiveness"] for effect in effects_list if effect in EFFECTS)
    
    # In the game, addictiveness is capped at 100%
    total_addictiveness = min(base_addictiveness + effect_addictiveness, 1.0)
    
    return market_value, total_cost, profit, profit_margin, effects_list, total_addictiveness


def compare_mixes(mix_list):
    """
    Compare multiple mixes to find the most profitable ones.
    
    Args:
        mix_list (list): List of mix dictionaries with 'name', 'base_product', and 'mixers' keys
    
    Returns:
        list: Sorted list of mixes with calculated profit metrics
    """
    results = []
    
    for mix in mix_list:
        market_value, total_cost, profit, profit_margin, effects, addictiveness = calculate_profit(
            mix['base_product'], mix['mixers']
        )
        
        results.append({
            'name': mix['name'],
            'base_product': mix['base_product'],
            'effects': effects,
            'mixers': mix['mixers'],
            'market_value': market_value,
            'total_cost': total_cost,
            'profit': profit,
            'profit_margin': profit_margin,
            'num_mixes': len(mix['mixers']),
            'addictiveness': addictiveness
        })
    
    # Sort by profit margin (descending)
    return sorted(results, key=lambda x: x['profit_margin'], reverse=True)


def find_top_profit_recipes(base_product, max_depth=8, top_n=5, max_mixers=None):
    """
    Find the top N highest profit margin recipes for a specific base product
    using a greedy approach combined with some pruning.
    
    Args:
        base_product (str): The base product type or marijuana strain
        max_depth (int): Maximum number of mixers to try
        top_n (int): Number of top recipes to return
        max_mixers (int, optional): Maximum number of mixers allowed in a recipe.
                                   If None, no limit is applied.
    
    Returns:
        list: Top N recipes sorted by profit margin (highest first)
    """
    # If max_mixers is provided, limit max_depth accordingly
    if max_mixers is not None:
        max_depth = min(max_depth, max_mixers)
    
    # All possible mixer combinations would be 2^16, which is too many to test
    # We'll use a greedy approach with some exploration
    
    # Start with no mixers
    mixer_combinations = [[]]
    
    # Generate all possible combinations of 1 mixer
    for mixer in MIXERS:
        mixer_combinations.append([mixer])
    
    # For deeper combinations, only keep the best ones at each step to avoid combinatorial explosion
    best_combinations = []
    
    # Keep track of effect signatures we've already seen to avoid duplicates
    seen_effect_signatures = set()
    
    # Evaluate all current combinations and keep top ones
    for mixers in mixer_combinations:
        market_value, total_cost, profit, margin, effects, addictiveness = calculate_profit(base_product, mixers)
        
        # Create a signature for this effect combination to filter out duplicates
        # Sort effects to make signature order-independent
        effect_signature = tuple(sorted(effects))
        
        # Only add if we haven't seen this effect combination before
        if effect_signature not in seen_effect_signatures:
            seen_effect_signatures.add(effect_signature)
            
            best_combinations.append({
                'mixers': mixers,
                'market_value': market_value,
                'total_cost': total_cost,
                'profit': profit,
                'profit_margin': margin,
                'effects': effects,
                'effect_signature': effect_signature,
                'addictiveness': addictiveness
            })
    
    # Sort by profit margin
    best_combinations = sorted(best_combinations, key=lambda x: x['profit_margin'], reverse=True)
    
    # Prune to top N*5 to allow for exploration (keep more than just top N)
    pruned_combinations = best_combinations[:top_n*5]
    
    # Explore deeper combinations, up to max_depth
    for depth in range(2, max_depth + 1):
        new_combinations = []
        
        # For each combination in our pruned list
        for combo in pruned_combinations:
            current_mixers = combo['mixers']
            
            # Skip if we've already hit max_mixers limit
            if max_mixers is not None and len(current_mixers) >= max_mixers:
                continue
                
            # Try adding each possible mixer that's not already in the combination
            for mixer in MIXERS:
                if mixer not in current_mixers:  # Avoid duplicates
                    new_mixers = current_mixers + [mixer]
                    market_value, total_cost, profit, margin, effects, addictiveness = calculate_profit(base_product, new_mixers)
                    
                    # Create signature for deduplication
                    effect_signature = tuple(sorted(effects))
                    
                    # Only add if we haven't seen this effect combination before
                    if effect_signature not in seen_effect_signatures:
                        seen_effect_signatures.add(effect_signature)
                        
                        new_combinations.append({
                            'mixers': new_mixers,
                            'market_value': market_value,
                            'total_cost': total_cost,
                            'profit': profit,
                            'profit_margin': margin,
                            'effects': effects,
                            'effect_signature': effect_signature,
                            'addictiveness': addictiveness
                        })
        
        # Add these to our best combinations
        best_combinations.extend(new_combinations)
        
        # Sort by profit margin
        best_combinations = sorted(best_combinations, key=lambda x: x['profit_margin'], reverse=True)
        
        # Prune again to avoid explosion
        pruned_combinations = best_combinations[:top_n*5]
    
    # Get results with variety - use effect signature as a key for grouping
    # Group recipes by their market value to further ensure variety
    value_groups = {}
    for combo in best_combinations:
        # Use market value as key to group similar recipes
        key = combo['market_value']
        if key not in value_groups:
            value_groups[key] = []
        value_groups[key].append(combo)
    
    # Take the best recipe from each market value group
    diverse_results = []
    for key in sorted(value_groups.keys(), reverse=True):
        # Sort recipes within each group by profit margin
        group = sorted(value_groups[key], key=lambda x: x['profit_margin'], reverse=True)
        # Take the best from each group
        if group:
            diverse_results.append(group[0])
            if len(diverse_results) >= top_n:
                break
    
    # If we still need more recipes to reach top_n, add more from best_combinations
    if len(diverse_results) < top_n:
        # Add recipes we haven't added yet
        for combo in best_combinations:
            if combo not in diverse_results:
                diverse_results.append(combo)
                if len(diverse_results) >= top_n:
                    break
    
    # Remove the signature field before returning
    for result in diverse_results:
        if 'effect_signature' in result:
            del result['effect_signature']
    
    # Final sort by profit margin
    return sorted(diverse_results, key=lambda x: x['profit_margin'], reverse=True)[:top_n]


def find_all_top_recipes(top_n=5, max_mixers=None):
    """
    Find the top profit margin recipes for all base products.
    
    Args:
        top_n (int): Number of top recipes to return per base product
        max_mixers (int, optional): Maximum number of mixers allowed in a recipe.
                                   If None, no limit is applied.
    
    Returns:
        dict: Dictionary with base products as keys and lists of top recipes as values
    """
    results = {}
    
    # Process normal drug types
    for product in BASE_MARKET_VALUES:
        results[product] = find_top_profit_recipes(product, top_n=top_n, max_mixers=max_mixers)
    
    # Process marijuana strains
    for strain in MARIJUANA_STRAINS:
        results[strain] = find_top_profit_recipes(strain, top_n=top_n, max_mixers=max_mixers)
    
    return results