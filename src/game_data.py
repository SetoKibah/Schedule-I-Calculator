"""
Schedule I Game Data
Contains constants and data structures for the Schedule I drug mixing profit calculator.
"""

# Base market values for each product type
BASE_MARKET_VALUES = {
    "Marijuana": 38,  # Updated to match OG Kush value
    "Methamphetamine": 70,  # Per crystal value
    "Cocaine": 150  # Per gram value
}

# Marijuana strains with their inherent effects, costs, and yields
MARIJUANA_STRAINS = {
    "OG Kush": {"effect": "Calming", "seed_cost": 30, "bud_value": 38, "yield_range": (11, 13)},
    "Sour Diesel": {"effect": "Refreshing", "seed_cost": 35, "bud_value": 40, "yield_range": (11, 13)},  # Corrected to Refreshing
    "Green Crack": {"effect": "Energizing", "seed_cost": 40, "bud_value": 43, "yield_range": (11, 13)},
    "Granddaddy Purple": {"effect": "Sedating", "seed_cost": 45, "bud_value": 44, "yield_range": (11, 13)}  # Corrected to Sedating
}

# Mixers with their effects, costs, and unlock ranks from the wiki
MIXERS = {
    "Cuke": {"effect": "Energizing", "cost": 2, "unlock": "Immediately"},
    "Banana": {"effect": "Gingeritis", "cost": 2, "unlock": "Immediately"},  # Updated from $3 to $2
    "Paracetamol": {"effect": "Sneaky", "cost": 3, "unlock": "Immediately"},  # Updated from $4 to $3
    "Donut": {"effect": "Calorie-Dense", "cost": 3, "unlock": "Immediately"},  # Updated from $4 to $3
    "Viagra": {"effect": "Tropic Thunder", "cost": 4, "unlock": "Hoodlum II"},  # Listed as Viagor in wiki
    "Flu medicine": {"effect": "Sedating", "cost": 5, "unlock": "Hoodlum IV"},  # Updated from Street Rat I to Hoodlum IV
    "Mouth wash": {"effect": "Balding", "cost": 4, "unlock": "Hoodlum III"},  # Updated effect and cost
    "Gasoline": {"effect": "Toxic", "cost": 5, "unlock": "Hoodlum V"},  # Updated from $6 to $5 and changed unlock
    "Motor oil": {"effect": "Slippery", "cost": 6, "unlock": "Peddler II"},  # Updated unlock
    "Mega bean": {"effect": "Foggy", "cost": 7, "unlock": "Peddler II"},  # Updated from $4 to $7
    "Chili": {"effect": "Spicy", "cost": 7, "unlock": "Peddler IV"},  # Updated from $5 to $7
    "Battery": {"effect": "Bright-Eyed", "cost": 8, "unlock": "Peddler V"},  # Updated from $12 to $8 and changed effect
    "Energy drink": {"effect": "Athletic", "cost": 6, "unlock": "Peddler I"},  # Updated unlock
    "Iodine": {"effect": "Jennerising", "cost": 8, "unlock": "Hustler I"},  # Updated from $7 to $8
    "Addy": {"effect": "Thought-Provoking", "cost": 9, "unlock": "Hustler II"},  # Updated from $8 to $9
    "Horse semen": {"effect": "Long Faced", "cost": 9, "unlock": "Hustler III"}  # Updated from $10 to $9
}

# Effects with their market value multipliers and addictiveness from the wiki
EFFECTS = {
    # Base effects
    "Calming": {"multiplier": 0.10, "addictiveness": 0.00, "tier": 1},
    "Paranoia": {"multiplier": 0.12, "addictiveness": 0.12, "tier": 1},
    "Euphoric": {"multiplier": 0.14, "addictiveness": 0.29, "tier": 1},
    "Munchies": {"multiplier": 0.16, "addictiveness": 0.19, "tier": 1},
    "Laxative": {"multiplier": 0.18, "addictiveness": 0.15, "tier": 1},
    "Focused": {"multiplier": 0.20, "addictiveness": 0.31, "tier": 1},
    
    # Tier 2 effects
    "Energizing": {"multiplier": 0.22, "addictiveness": 0.34, "tier": 2},
    "Foggy": {"multiplier": 0.24, "addictiveness": 0.27, "tier": 2},
    "Sedating": {"multiplier": 0.26, "addictiveness": 0.30, "tier": 2},
    "Calorie-Dense": {"multiplier": 0.28, "addictiveness": 0.27, "tier": 2},
    "Balding": {"multiplier": 0.30, "addictiveness": 0.31, "tier": 2},
    "Thought-Provoking": {"multiplier": 0.32, "addictiveness": 0.37, "tier": 2},
    
    # Tier 3 effects
    "Slippery": {"multiplier": 0.34, "addictiveness": 0.31, "tier": 3},
    "Toxic": {"multiplier": 0.00, "addictiveness": 0.38, "tier": 3},  # No value increase
    "Spicy": {"multiplier": 0.36, "addictiveness": 0.33, "tier": 3},
    "Gingeritis": {"multiplier": 0.38, "addictiveness": 0.44, "tier": 3},
    "Sneaky": {"multiplier": 0.40, "addictiveness": 0.48, "tier": 3},
    "Disorienting": {"multiplier": 0.42, "addictiveness": 0.46, "tier": 3},
    "Athletic": {"multiplier": 0.44, "addictiveness": 0.49, "tier": 3},
    
    # Tier 4 effects
    "Tropic Thunder": {"multiplier": 0.46, "addictiveness": 1.00, "tier": 4},  # Updated from wiki
    "Glowing": {"multiplier": 0.48, "addictiveness": 0.78, "tier": 4},
    "Electrifying": {"multiplier": 0.50, "addictiveness": 0.80, "tier": 4},
    "Long Faced": {"multiplier": 0.52, "addictiveness": 1.00, "tier": 4},  # Updated from wiki
    "Anti-gravity": {"multiplier": 0.54, "addictiveness": 0.86, "tier": 4},
    "Cyclopean": {"multiplier": 0.56, "addictiveness": 0.88, "tier": 4},
    "Zombifying": {"multiplier": 0.58, "addictiveness": 0.99, "tier": 4},
    
    # Tier 5 effects (most valuable)
    "Shrinking": {"multiplier": 0.60, "addictiveness": 0.91, "tier": 5},
    "Bright-Eyed": {"multiplier": 0.62, "addictiveness": 0.93, "tier": 5},
    
    # Additional effects from wiki
    "Explosive": {"multiplier": 0.42, "addictiveness": 0.55, "tier": 3},
    "Jennerising": {"multiplier": 0.46, "addictiveness": 0.74, "tier": 4},
    "Schizophrenic": {"multiplier": 0.48, "addictiveness": 0.80, "tier": 4},
    "Seizure-Inducing": {"multiplier": 0.52, "addictiveness": 0.90, "tier": 4},
    "Refreshing": {"multiplier": 0.10, "addictiveness": 0.10, "tier": 1},  # Sour Diesel's base effect
    "Smelly": {"multiplier": 0.30, "addictiveness": 0.35, "tier": 2}  # Additional effect
}

# Effect reactions - what happens when mixers interact with existing effects
# Format: {mixer_effect: {existing_effect: new_effect}}
EFFECT_REACTIONS = {
    "Electrifying": {
        "Athletic": "Sneaky",
        "Euphoric": "Spicy",
        # Add more reactions as needed
    },
    "Disorienting": {
        "Paranoia": "Zombifying",
        # Add more reactions as needed
    },
    # Add more mixer effects and their reactions
}

# Updated with more comprehensive and accurate effect interactions from the wiki
# Format: [required_effect, mixer, new_effect, effect_to_replace (optional)]
EFFECT_INTERACTION_RULES = [
    # Anti-gravity related rules
    ["Smelly", "Banana", "Anti-gravity", "Smelly"],
    ["Munchies", "Paracetamol", "Anti-gravity", "Munchies"],
    ["Calming", "Mouth wash", "Anti-gravity", "Calming"],
    
    # Strain-specific effects - using strain names for accuracy
    # Sour Diesel specifics
    ["Refreshing", "Cuke", "Energizing", None],  # Sour Diesel + Cuke adds Energizing
    ["Refreshing", "Horse semen", "Long Faced", None],
    ["Refreshing", "Chili", "Shrinking", None],
    ["Refreshing", "Addy", "Glowing", None],
    
    # OG Kush specifics
    ["Calming", "Cuke", "Energizing", None],  # OG Kush + Cuke adds Energizing
    ["Calming", "Banana", "Sneaky", "Calming"],  # OG Kush + Banana adds Sneaky, removes Calming
    ["Calming", "Mouth wash", "Cyclopean", "Calming"],  # OG Kush + Mouth wash
    ["Calming", "Energy drink", "Athletic", None],
    ["Calming", "Addy", "Thought-Provoking", None],
    
    # Green Crack specifics
    ["Energizing", "Motor oil", "Slippery", None],
    ["Energizing", "Battery", "Bright-Eyed", None],
    ["Energizing", "Addy", "Thought-Provoking", None],
    ["Energizing", "Horse semen", "Long Faced", None],
    
    # Granddaddy Purple specifics
    ["Sedating", "Energy drink", "Bright-Eyed", "Sedating"],
    ["Sedating", "Flu medicine", "Bright-Eyed", None],
    ["Sedating", "Chili", "Spicy", None],
    
    # General effect combinations
    ["Paranoia", "Banana", "Zombifying", "Paranoia"],  # Only applies when Paranoia present
    ["Paranoia", "Cuke", "Shrinking", None],  # Only when Paranoia is already present
    ["Paranoia", "Mega bean", "Jennerising", None],
    ["Paranoia", "Iodine", "Foggy", None],
    ["Paranoia", "Paracetamol", "Sneaky", None],
    
    # Battery effects
    [None, "Battery", "Euphoric", None],  # Default effect
    ["Zombifying", "Battery", "Electrifying", None],  # Special when Zombifying exists
    
    # Mouth wash effects
    [None, "Mouth wash", "Explosive", None],  # Default effect
    
    # Other conditional effect rules from wiki
    ["Munchies", "Motor oil", "Energizing", None],
    ["Calorie-Dense", "Donut", "Explosive", None],
    ["Athletic", "Energy drink", "Glowing", None]
]

# Simple 1-to-1 effect replacement rules from the wiki's "Effect, Product to Add, Replaces Existing Trait" section
EFFECT_REPLACEMENTS = {
    # Format: (existing_effect, mixer): new_effect
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
    # Corrected: Chili does not replace Refreshing with Shrinking, it adds Spicy
    # ("Refreshing", "Chili"): "Shrinking",  # Removed this incorrect mapping
    ("Refreshing", "Addy"): "Glowing",
    ("Refreshing", "Horse Semen"): "Gingeritis",
    # Green Crack specific replacements (Energizing being replaced)
    ("Energizing", "Paracetamol"): "Paranoia",  # Green Crack + Paracetamol creates Paranoia instead of keeping Energizing
    # New replacements from test data
    ("Energizing", "Banana"): "Thought-Provoking",  # Green Crack + Banana 
    ("Calming", "Paracetamol"): "Slippery",  # OG Kush + Paracetamol
}

# Add addictiveness data from wiki for each product
ADDICTIVENESS = {
    "OG Kush": 0.0,  # 0% addictive base
    "Sour Diesel": 0.10,  # 10% addictive base
    "Green Crack": 0.34,  # 34% addictive base
    "Granddaddy Purple": 0.0,  # 0% addictive base
    "Methamphetamine": 0.60,  # 60% addictive base
    "Cocaine": 0.40  # 40% addictive base
}

# Add production information for Methamphetamine and Cocaine
PRODUCTION_INFO = {
    "Methamphetamine": {
        "ingredients_cost": 140,  # $40 Acid + $40 Red Phosphorus + $60 Pseudoephedrine
        "yield": 10,  # 10 crystals per batch
        "unit_value": 70  # $70 per crystal
    },
    "Cocaine": {
        "ingredients_cost": 245,  # Total production cost according to wiki
        "yield": 10,  # 10 grams per batch
        "unit_value": 150  # $150 per gram
    }
}

# Example recipes from the guide
RECIPES = {
    "Granddaddy Assblaster": {
        "base": ["Methamphetamine", "Cocaine"],  # Works with these bases
        "mixers": ["Horse semen", "Addy", "Gasoline", "Paracetamol", "Banana", 
                  "Horse semen", "Iodine", "Cuke", "Gasoline", "Horse semen", 
                  "Battery", "Energy drink", "Mega bean", "Mouth wash"],
        "effects": ["Shrinking", "Zombifying", "Cyclopean", "Anti-gravity", 
                   "Long Faced", "Electrifying", "Glowing", "Tropic Thunder"],
        "multiplier_total": 4.24
    },
    "Mega Diamond": {
        "base": ["Sour Diesel"],  # Works with this strain
        "mixers": ["Horse semen", "Iodine", "Addy", "Gasoline", "Paracetamol", 
                  "Banana", "Horse semen", "Iodine", "Cuke", "Gasoline", 
                  "Horse semen", "Battery", "Energy drink", "Mega bean", "Mouth wash"],
        "effects": ["Shrinking", "Zombifying", "Cyclopean", "Anti-gravity", 
                   "Long Faced", "Electrifying", "Glowing", "Tropic Thunder"],
        "multiplier_total": 4.24
    },
    "Efficient Mix": {  # Example of more efficient mix from comments
        "base": ["Methamphetamine"],
        "mixers": ["Banana", "Cuke", "Paracetamol", "Gasoline", "Cuke", 
                  "Battery", "Horse semen", "Mega bean"],
        "effects": ["Electrifying", "Glowing", "Tropic Thunder", "Zombifying", 
                   "Cyclopean", "Bright-Eyed", "Long Faced", "Foggy"],
        "profit": 302
    }
}