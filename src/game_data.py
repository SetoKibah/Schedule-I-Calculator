"""
Schedule I Game Data
Contains constants and data structures for the Schedule I drug mixing profit calculator.
"""

# Base market values for each product type
BASE_MARKET_VALUES = {
    "Marijuana": 38,
    "Methamphetamine": 70,
    "Cocaine": 150
}

# Marijuana strains with their inherent effects, costs, and yields
MARIJUANA_STRAINS = {
    "OG Kush": {"effect": "Calming", "seed_cost": 30, "bud_value": 38, "yield_range": (11, 13)},
    "Sour Diesel": {"effect": "Refreshing", "seed_cost": 35, "bud_value": 40, "yield_range": (11, 13)},
    "Green Crack": {"effect": "Energizing", "seed_cost": 40, "bud_value": 43, "yield_range": (11, 13)},
    "Granddaddy Purple": {"effect": "Sedating", "seed_cost": 45, "bud_value": 44, "yield_range": (11, 13)}
}

# Mixers with their effects, costs, and unlock ranks
MIXERS = {
    "Cuke": {"effect": "Energizing", "cost": 2, "unlock": "Immediately"},
    "Banana": {"effect": "Gingeritis", "cost": 2, "unlock": "Immediately"},
    "Paracetamol": {"effect": "Sneaky", "cost": 3, "unlock": "Immediately"},
    "Donut": {"effect": "Calorie-Dense", "cost": 3, "unlock": "Immediately"},
    "Viagra": {"effect": "Tropic Thunder", "cost": 4, "unlock": "Hoodlum II"},
    "Flu medicine": {"effect": "Sedating", "cost": 5, "unlock": "Hoodlum IV"},
    "Mouth wash": {"effect": "Balding", "cost": 4, "unlock": "Hoodlum III"},
    "Gasoline": {"effect": "Toxic", "cost": 5, "unlock": "Hoodlum V"},
    "Motor oil": {"effect": "Slippery", "cost": 6, "unlock": "Peddler II"},
    "Mega bean": {"effect": "Foggy", "cost": 7, "unlock": "Peddler II"},
    "Chili": {"effect": "Spicy", "cost": 7, "unlock": "Peddler IV"},
    "Battery": {"effect": "Bright-Eyed", "cost": 8, "unlock": "Peddler V"},
    "Energy drink": {"effect": "Athletic", "cost": 6, "unlock": "Peddler I"},
    "Iodine": {"effect": "Jennerising", "cost": 8, "unlock": "Hustler I"},
    "Addy": {"effect": "Thought-Provoking", "cost": 9, "unlock": "Hustler II"},
    "Horse semen": {"effect": "Long Faced", "cost": 9, "unlock": "Hustler III"}
}

# Effects with their market value multipliers and addictiveness
EFFECTS = {
    "Calming": {"multiplier": 0.10, "addictiveness": 0.00, "tier": 1},
    "Paranoia": {"multiplier": 0.12, "addictiveness": 0.12, "tier": 1},
    "Euphoric": {"multiplier": 0.14, "addictiveness": 0.29, "tier": 1},
    "Munchies": {"multiplier": 0.16, "addictiveness": 0.19, "tier": 1},
    "Laxative": {"multiplier": 0.18, "addictiveness": 0.15, "tier": 1},
    "Focused": {"multiplier": 0.20, "addictiveness": 0.31, "tier": 1},
    "Energizing": {"multiplier": 0.22, "addictiveness": 0.34, "tier": 2},
    "Foggy": {"multiplier": 0.24, "addictiveness": 0.27, "tier": 2},
    "Sedating": {"multiplier": 0.26, "addictiveness": 0.30, "tier": 2},
    "Calorie-Dense": {"multiplier": 0.28, "addictiveness": 0.27, "tier": 2},
    "Balding": {"multiplier": 0.30, "addictiveness": 0.31, "tier": 2},
    "Thought-Provoking": {"multiplier": 0.32, "addictiveness": 0.37, "tier": 2},
    "Slippery": {"multiplier": 0.34, "addictiveness": 0.31, "tier": 3},
    "Toxic": {"multiplier": 0.00, "addictiveness": 0.38, "tier": 3},
    "Spicy": {"multiplier": 0.36, "addictiveness": 0.33, "tier": 3},
    "Gingeritis": {"multiplier": 0.38, "addictiveness": 0.44, "tier": 3},
    "Sneaky": {"multiplier": 0.40, "addictiveness": 0.48, "tier": 3},
    "Disorienting": {"multiplier": 0.42, "addictiveness": 0.46, "tier": 3},
    "Athletic": {"multiplier": 0.44, "addictiveness": 0.49, "tier": 3},
    "Tropic Thunder": {"multiplier": 0.46, "addictiveness": 1.00, "tier": 4},
    "Glowing": {"multiplier": 0.48, "addictiveness": 0.78, "tier": 4},
    "Electrifying": {"multiplier": 0.50, "addictiveness": 0.80, "tier": 4},
    "Long Faced": {"multiplier": 0.52, "addictiveness": 1.00, "tier": 4},
    "Anti-gravity": {"multiplier": 0.54, "addictiveness": 0.86, "tier": 4},
    "Cyclopean": {"multiplier": 0.56, "addictiveness": 0.88, "tier": 4},
    "Zombifying": {"multiplier": 0.58, "addictiveness": 0.99, "tier": 4},
    "Shrinking": {"multiplier": 0.60, "addictiveness": 0.91, "tier": 5},
    "Bright-Eyed": {"multiplier": 0.62, "addictiveness": 0.93, "tier": 5},
    "Explosive": {"multiplier": 0.42, "addictiveness": 0.55, "tier": 3},
    "Jennerising": {"multiplier": 0.46, "addictiveness": 0.74, "tier": 4},
    "Schizophrenic": {"multiplier": 0.48, "addictiveness": 0.80, "tier": 4},
    "Seizure-Inducing": {"multiplier": 0.52, "addictiveness": 0.90, "tier": 4},
    "Refreshing": {"multiplier": 0.10, "addictiveness": 0.10, "tier": 1},
    "Smelly": {"multiplier": 0.30, "addictiveness": 0.35, "tier": 2}
}

# Effect reactions - what happens when mixers interact with existing effects
EFFECT_REACTIONS = {
    "Electrifying": {
        "Athletic": "Sneaky",
        "Euphoric": "Spicy"
    },
    "Disorienting": {
        "Paranoia": "Zombifying"
    }
}

# Effect interaction rules
EFFECT_INTERACTION_RULES = [
    ["Smelly", "Banana", "Anti-gravity", "Smelly"],
    ["Munchies", "Paracetamol", "Anti-gravity", "Munchies"],
    ["Calming", "Mouth wash", "Anti-gravity", "Calming"],
    ["Refreshing", "Cuke", "Energizing", None],
    ["Refreshing", "Horse semen", "Long Faced", None],
    ["Refreshing", "Chili", "Shrinking", None],
    ["Refreshing", "Addy", "Glowing", None],
    ["Calming", "Cuke", "Energizing", None],
    ["Calming", "Banana", "Sneaky", "Calming"],
    ["Calming", "Mouth wash", "Cyclopean", "Calming"],
    ["Calming", "Energy drink", "Athletic", None],
    ["Calming", "Addy", "Thought-Provoking", None],
    ["Energizing", "Motor oil", "Slippery", None],
    ["Energizing", "Battery", "Bright-Eyed", None],
    ["Energizing", "Addy", "Thought-Provoking", None],
    ["Energizing", "Horse semen", "Long Faced", None],
    ["Sedating", "Energy drink", "Bright-Eyed", "Sedating"],
    ["Sedating", "Flu medicine", "Bright-Eyed", None],
    ["Sedating", "Chili", "Spicy", None],
    ["Paranoia", "Banana", "Zombifying", "Paranoia"],
    ["Paranoia", "Cuke", "Shrinking", None],
    ["Paranoia", "Mega bean", "Jennerising", None],
    ["Paranoia", "Iodine", "Foggy", None],
    ["Paranoia", "Paracetamol", "Sneaky", None],
    [None, "Battery", "Euphoric", None],
    ["Zombifying", "Battery", "Electrifying", None],
    [None, "Mouth wash", "Explosive", None],
    ["Munchies", "Motor oil", "Energizing", None],
    ["Calorie-Dense", "Donut", "Explosive", None],
    ["Athletic", "Energy drink", "Glowing", None]
]

# Effect replacement rules
EFFECT_REPLACEMENTS = {
    ("Smelly", "Banana"): "Anti-gravity",
    ("Munchies", "Paracetamol"): "Anti-gravity",
    ("Calming", "Mouth wash"): "Anti-gravity",
    ("Calming", "Banana"): "Sneaky",
    ("Paranoia", "Banana"): "Zombifying",
    ("Paranoia", "Cuke"): "Shrinking",
    ("Paranoia", "Paracetamol"): "Sneaky",
    ("Paranoia", "Flu Medicine"): "Shrinking",
    ("Paranoia", "Mega Bean"): "Jennerising",
    ("Paranoia", "Iodine"): "Foggy",
    ("Refreshing", "Banana"): "Long Faced",
    ("Refreshing", "Flu Medicine"): "Long Faced",
    ("Refreshing", "Addy"): "Glowing",
    ("Refreshing", "Horse Semen"): "Gingeritis",
    ("Energizing", "Paracetamol"): "Paranoia",
    ("Energizing", "Banana"): "Thought-Provoking",
    ("Calming", "Paracetamol"): "Slippery"
}

# Addictiveness data for each product
ADDICTIVENESS = {
    "OG Kush": 0.0,
    "Sour Diesel": 0.10,
    "Green Crack": 0.34,
    "Granddaddy Purple": 0.0,
    "Methamphetamine": 0.60,
    "Cocaine": 0.40
}

# Production information for Methamphetamine and Cocaine
PRODUCTION_INFO = {
    "Methamphetamine": {
        "ingredients_cost": 140,
        "yield": 10,
        "unit_value": 70
    },
    "Cocaine": {
        "ingredients_cost": 245,
        "yield": 10,
        "unit_value": 150
    }
}

# Example recipes
RECIPES = {
    "Granddaddy Assblaster": {
        "base": ["Methamphetamine", "Cocaine"],
        "mixers": ["Horse semen", "Addy", "Gasoline", "Paracetamol", "Banana", 
                   "Horse semen", "Iodine", "Cuke", "Gasoline", "Horse semen", 
                   "Battery", "Energy drink", "Mega bean", "Mouth wash"],
        "effects": ["Shrinking", "Zombifying", "Cyclopean", "Anti-gravity", 
                    "Long Faced", "Electrifying", "Glowing", "Tropic Thunder"],
        "multiplier_total": 4.24
    },
    "Mega Diamond": {
        "base": ["Sour Diesel"],
        "mixers": ["Horse semen", "Iodine", "Addy", "Gasoline", "Paracetamol", 
                   "Banana", "Horse semen", "Iodine", "Cuke", "Gasoline", 
                   "Horse semen", "Battery", "Energy drink", "Mega bean", "Mouth wash"],
        "effects": ["Shrinking", "Zombifying", "Cyclopean", "Anti-gravity", 
                    "Long Faced", "Electrifying", "Glowing", "Tropic Thunder"],
        "multiplier_total": 4.24
    },
    "Efficient Mix": {
        "base": ["Methamphetamine"],
        "mixers": ["Banana", "Cuke", "Paracetamol", "Gasoline", "Cuke", 
                   "Battery", "Horse semen", "Mega bean"],
        "effects": ["Electrifying", "Glowing", "Tropic Thunder", "Zombifying", 
                    "Cyclopean", "Bright-Eyed", "Long Faced", "Foggy"],
        "profit": 302
    }
}
