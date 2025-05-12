"""
Dealer data management module for Schedule I Calculator.
Handles loading, saving, and processing dealer data.
"""
import json
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup
import requests


def load_dealer_data(file_path="dealer_data.json"):
    """Load dealer data from JSON file.
    
    Args:
        file_path (str): Path to the dealer data file
        
    Returns:
        dict: Dealer data dictionary
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Could not parse {file_path}. File may be corrupted.")
            return {"dealers": []}
    else:
        print(f"Info: No dealer data file found at {file_path}. Creating a new one.")
        return {"dealers": []}


def save_dealer_data(data, file_path="dealer_data.json"):
    """Save dealer data to JSON file.
    
    Args:
        data (dict): Dealer data dictionary
        file_path (str): Path to save the dealer data file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"Dealer data saved to {file_path}")


def fix_dealer_data(dealer_data):
    """Fix and standardize dealer data entries.
    
    This function ensures all dealer data is properly formatted:
    - Fixes "Medium" standards to "Moderate"
    - Sets default values for missing data to "Not Available"
    - Adds missing fields like markup_percentage
    
    Args:
        dealer_data (dict): Dictionary containing dealer data
        
    Returns:
        dict: The fixed dealer data
    """
    # Make a copy to avoid modifying the original
    fixed_data = {"dealers": []}
    
    for dealer in dealer_data.get("dealers", []):
        fixed_dealer = dealer.copy()
        
        # Set default values for missing data
        if not fixed_dealer.get("region"):
            fixed_dealer["region"] = "Not Available"
            
        # Set default for empty location
        if not fixed_dealer.get("location"):
            fixed_dealer["location"] = "Unknown"
            
        # Set default for initial_buy_in
        if "initial_buy_in" not in fixed_dealer:
            fixed_dealer["initial_buy_in"] = 0
            
        # Set default for percentage_taken
        if "percentage_taken" not in fixed_dealer:
            fixed_dealer["percentage_taken"] = 0.0
            
        # Set default for assignable_customers
        if "assignable_customers" not in fixed_dealer:
            fixed_dealer["assignable_customers"] = 0
        
        # Set default for appearance
        if "appearance" not in fixed_dealer or not fixed_dealer["appearance"]:
            fixed_dealer["appearance"] = "No appearance information available"
            
        # Set default for location_details
        if "location_details" not in fixed_dealer or not fixed_dealer["location_details"]:
            fixed_dealer["location_details"] = "No location details available"
            
        # Set default for combat_info
        if "combat_info" not in fixed_dealer or not fixed_dealer["combat_info"]:
            fixed_dealer["combat_info"] = "No combat information available"
        
        if not fixed_dealer.get("preferred_effects"):
            fixed_dealer["preferred_effects"] = []
        
        if not fixed_dealer.get("transactions"):
            fixed_dealer["transactions"] = []
        
        # Add max_quantity if not present
        if "max_quantity" not in fixed_dealer:
            fixed_dealer["max_quantity"] = 0
            
        # Add last_transaction_date if not present
        if "last_transaction_date" not in fixed_dealer:
            fixed_dealer["last_transaction_date"] = ""
            
        # Add notes if not present
        if "notes" not in fixed_dealer:
            fixed_dealer["notes"] = ""
        
        fixed_data["dealers"].append(fixed_dealer)
    
    return fixed_data


def process_effects_list(effects):
    """Process a list of effects, handling cases where they're squished together.
    
    Args:
        effects (list): List of effects strings
        
    Returns:
        list: Properly separated effects
    """
    if not effects:
        return []
    
    # Known effect names for splitting squished text
    known_effects = [
        "Energizing", "Refreshing", "Calming", "Paranoia", "Sedating",
        "Calorie-Dense", "Balding", "Long Faced", "Foggy", "Jennerising", 
        "Spicy", "Gingeritis", "Sneaky", "Disorienting", "Athletic",
        "Tropic Thunder", "Glowing", "Electrifying", "Anti-gravity",
        "Cyclopean", "Zombifying", "Shrinking", "Bright-Eyed", "Explosive",
        "Lethal", "Toxic", "Slippery", "Thought-Provoking"
    ]
    
    # Process each effect string in the list
    new_effects = []
    for effect_text in effects:
        if not effect_text:
            continue
            
        # First try splitting by commas and other separators
        for part in re.split(r'[,;/]+', effect_text):
            part = part.strip()
            if not part:
                continue
                
            # If the effect contains known effect names without spaces between them
            if any(e in part for e in known_effects) and len(part) > 20:
                # Create a regex pattern that looks for all known effects
                pattern = '|'.join(known_effects)
                pattern = f'({pattern})'
                
                # Find all effect names in the string
                found_effects = re.findall(pattern, part)
                if found_effects:
                    new_effects.extend(found_effects)
                else:
                    new_effects.append(part)
            else:
                new_effects.append(part)
    
    # Remove duplicates while preserving order
    seen = set()
    return [x for x in new_effects if not (x in seen or seen.add(x))]


def extract_dealer_data_from_html(soup, name, url):
    """Extract dealer data from HTML soup.
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object containing HTML
        name (str): Dealer name
        url (str): Source URL
        
    Returns:
        dict: Extracted dealer data
    """
    dealer_data = {
        "name": name,
        "region": "",
        "standards": "",
        "preferred_effects": [],
        "max_quantity": 0,
        "markup_percentage": 0.0,
        "transactions": [],
        "last_transaction_date": "",
        "notes": f"Imported from {url} on {datetime.now().strftime('%Y-%m-%d')}"
    }
    
    print(f"\n--- EXTRACTING DATA FOR DEALER: {name} ---")
    
    # Try to find the article content
    article = soup.find('article', class_='WikiaArticle') or soup.find('div', class_='mw-parser-output')
    if not article:
        print(f"Warning: Could not find article content for {name}")
        # Use whole page if article section not found
        article = soup
    
    # Multiple approaches to extract data from different wiki formats
    _extract_from_tables(article, dealer_data)
    _extract_from_infoboxes(article, dealer_data)
    _extract_from_bold_text(article, dealer_data)
    _extract_from_sections(article, dealer_data)
    _extract_from_templates(article, dealer_data)
    _extract_from_text_patterns(article, dealer_data)
    
    # Set default values for any empty fields
    if not dealer_data["region"]:
        dealer_data["region"] = "Not Available"
        
    if not dealer_data["standards"]:
        dealer_data["standards"] = "Not Available"
        
    if not dealer_data["preferred_effects"]:
        dealer_data["preferred_effects"] = ["Not Available"]
    
    # Standardize "Medium" to "Moderate"
    if dealer_data["standards"] == "Medium":
        dealer_data["standards"] = "Moderate"
    
    # Print summary of what we found
    print("\nExtraction summary:")
    print(f"Region: {dealer_data['region']}")
    print(f"Standards: {dealer_data['standards']}")
    print(f"Preferred Effects: {dealer_data['preferred_effects']}")
    print(f"Max Quantity: {dealer_data['max_quantity']}")
    print(f"Markup Percentage: {dealer_data['markup_percentage']}")
    
    return dealer_data


def _extract_from_tables(article, dealer_data):
    """Extract dealer data from tables."""
    try:
        print("Trying extraction from tables...")
        tables = article.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                # Try to find header and value cells
                header_cell = row.find('th')
                value_cell = row.find('td')
                
                if header_cell and value_cell:
                    header_text = header_cell.get_text().strip().lower()
                    value_text = value_cell.get_text().strip()
                    
                    print(f"Found table row: {header_text} = {value_text}")
                    
                    if "region" in header_text:
                        dealer_data["region"] = value_text
                    elif "standard" in header_text:
                        if "low" in value_text.lower():
                            dealer_data["standards"] = "Low"
                        elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                            dealer_data["standards"] = "Moderate"
                        elif "high" in value_text.lower():
                            dealer_data["standards"] = "High"
                    elif "effect" in header_text and ("preferred" in header_text or "favorite" in header_text or "favourite" in header_text):
                        effects = process_effects_list([value_text])
                        dealer_data["preferred_effects"] = effects
                    elif "markup" in header_text or "margin" in header_text:
                        try:
                            # Extract percentage value
                            percentage_match = re.search(r'(\d+(\.\d+)?)%?', value_text)
                            if percentage_match:
                                dealer_data["markup_percentage"] = float(percentage_match.group(1))
                        except ValueError:
                            print(f"Couldn't convert markup value to float: {value_text}")
                    elif "quantity" in header_text or "capacity" in header_text or "max" in header_text:
                        try:
                            # Extract numeric value
                            quantity_match = re.search(r'(\d+)', value_text)
                            if quantity_match:
                                dealer_data["max_quantity"] = int(quantity_match.group(1))
                        except ValueError:
                            print(f"Couldn't convert quantity value to int: {value_text}")
    except Exception as e:
        print(f"Error in table extraction: {e}")


def _extract_from_infoboxes(article, dealer_data):
    """Extract dealer data from div-based infoboxes."""
    try:
        print("Trying extraction from div-based infoboxes...")
        infobox = article.find('div', class_='portable-infobox') or article.find('aside', class_='portable-infobox')
        if infobox:
            # Extract from portable infobox (modern)
            for item in infobox.find_all('div', class_='pi-item'):
                label = item.find('h3', class_='pi-data-label')
                value = item.find('div', class_='pi-data-value')
                
                if label and value:
                    label_text = label.get_text().strip().lower()
                    value_text = value.get_text().strip()
                    
                    print(f"Found infobox item: {label_text} = {value_text}")
                    
                    if "region" in label_text:
                        dealer_data["region"] = value_text
                    elif "standard" in label_text:
                        if "low" in value_text.lower():
                            dealer_data["standards"] = "Low"
                        elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                            dealer_data["standards"] = "Moderate"
                        elif "high" in value_text.lower():
                            dealer_data["standards"] = "High"
                    elif "effect" in label_text and ("preferred" in label_text or "favorite" in label_text or "favourite" in label_text):
                        effects = process_effects_list([value_text])
                        dealer_data["preferred_effects"] = effects
                    elif "markup" in label_text or "margin" in label_text:
                        try:
                            # Extract percentage value
                            percentage_match = re.search(r'(\d+(\.\d+)?)%?', value_text)
                            if percentage_match:
                                dealer_data["markup_percentage"] = float(percentage_match.group(1))
                        except ValueError:
                            print(f"Couldn't convert markup value to float: {value_text}")
                    elif "quantity" in label_text or "capacity" in label_text or "max" in label_text:
                        try:
                            # Extract numeric value
                            quantity_match = re.search(r'(\d+)', value_text)
                            if quantity_match:
                                dealer_data["max_quantity"] = int(quantity_match.group(1))
                        except ValueError:
                            print(f"Couldn't convert quantity value to int: {value_text}")
        
        # Try older style div infoboxes
        div_labels = article.find_all('div', class_='label')
        for label in div_labels:
            label_text = label.get_text().strip().lower()
            value_div = label.find_next_sibling('div')
            
            if value_div:
                value_text = value_div.get_text().strip()
                print(f"Found div label: {label_text} = {value_text}")
                
                if "region" in label_text:
                    dealer_data["region"] = value_text
                elif "standard" in label_text:
                    if "low" in value_text.lower():
                        dealer_data["standards"] = "Low"
                    elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                        dealer_data["standards"] = "Moderate"
                    elif "high" in value_text.lower():
                        dealer_data["standards"] = "High"
                elif "effect" in label_text and ("preferred" in label_text or "favorite" in label_text or "favourite" in label_text):
                    # Check if it's a list
                    list_items = value_div.find_all('li')
                    if list_items:
                        effects = [li.get_text().strip() for li in list_items]
                        effects = process_effects_list(effects)
                    else:
                        effects = process_effects_list([value_text])
                    dealer_data["preferred_effects"] = effects
                elif "markup" in label_text or "margin" in label_text:
                    try:
                        # Extract percentage value
                        percentage_match = re.search(r'(\d+(\.\d+)?)%?', value_text)
                        if percentage_match:
                            dealer_data["markup_percentage"] = float(percentage_match.group(1))
                    except ValueError:
                        print(f"Couldn't convert markup value to float: {value_text}")
                elif "quantity" in label_text or "capacity" in label_text or "max" in label_text:
                    try:
                        # Extract numeric value
                        quantity_match = re.search(r'(\d+)', value_text)
                        if quantity_match:
                            dealer_data["max_quantity"] = int(quantity_match.group(1))
                    except ValueError:
                        print(f"Couldn't convert quantity value to int: {value_text}")
    except Exception as e:
        print(f"Error in div infobox extraction: {e}")


def _extract_from_bold_text(article, dealer_data):
    """Extract dealer data from bold text patterns."""
    try:
        print("Trying extraction from bold text patterns...")
        # Find all bold elements
        bold_elements = article.find_all(['b', 'strong'])
        for bold in bold_elements:
            bold_text = bold.get_text().strip().lower()
            next_element = bold.next_sibling
            if next_element and isinstance(next_element, str):
                value_text = next_element.strip()
                if value_text.startswith(':'):
                    value_text = value_text[1:].strip()
                
                print(f"Found bold pattern: {bold_text} => {value_text}")
                
                if "region" in bold_text:
                    dealer_data["region"] = value_text
                elif "standard" in bold_text:
                    if "low" in value_text.lower():
                        dealer_data["standards"] = "Low"
                    elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                        dealer_data["standards"] = "Moderate"
                    elif "high" in value_text.lower():
                        dealer_data["standards"] = "High"
                elif "effect" in bold_text and ("preferred" in bold_text or "favorite" in bold_text or "favourite" in bold_text):
                    effects = process_effects_list([value_text])
                    dealer_data["preferred_effects"] = effects
                elif "markup" in bold_text or "margin" in bold_text:
                    try:
                        # Extract percentage value
                        percentage_match = re.search(r'(\d+(\.\d+)?)%?', value_text)
                        if percentage_match:
                            dealer_data["markup_percentage"] = float(percentage_match.group(1))
                    except ValueError:
                        print(f"Couldn't convert markup value to float: {value_text}")
                elif "quantity" in bold_text or "capacity" in bold_text or "max" in bold_text:
                    try:
                        # Extract numeric value
                        quantity_match = re.search(r'(\d+)', value_text)
                        if quantity_match:
                            dealer_data["max_quantity"] = int(quantity_match.group(1))
                    except ValueError:
                        print(f"Couldn't convert quantity value to int: {value_text}")
    except Exception as e:
        print(f"Error in bold text extraction: {e}")


def _extract_from_sections(article, dealer_data):
    """Extract dealer data from section headings."""
    try:
        print("Trying section-based extraction...")
        headers = article.find_all(['h2', 'h3', 'h4'])
        for header in headers:
            header_text = header.get_text().strip().lower()
            print(f"Found section header: {header_text}")
            
            if "region" in header_text:
                next_p = header.find_next('p')
                if next_p:
                    dealer_data["region"] = next_p.get_text().strip()
                    print(f"Found region text: {dealer_data['region']}")
            elif "standard" in header_text:
                next_p = header.find_next('p')
                if next_p:
                    standards_text = next_p.get_text().strip().lower()
                    if "low" in standards_text:
                        dealer_data["standards"] = "Low"
                    elif "moderate" in standards_text or "medium" in standards_text:
                        dealer_data["standards"] = "Moderate"
                    elif "high" in standards_text:
                        dealer_data["standards"] = "High"
                    print(f"Found standards text: {dealer_data['standards']}")
            elif ("preferred" in header_text or "favorite" in header_text or "favourite" in header_text) and "effect" in header_text:
                next_p = header.find_next('p')
                if next_p:
                    effects_text = next_p.get_text().strip()
                    effects = process_effects_list([effects_text])
                    dealer_data["preferred_effects"] = effects
                    print(f"Found effects text: {dealer_data['preferred_effects']}")
            elif "markup" in header_text or "margin" in header_text:
                next_p = header.find_next('p')
                if next_p:
                    markup_text = next_p.get_text().strip()
                    try:
                        # Extract percentage value
                        percentage_match = re.search(r'(\d+(\.\d+)?)%?', markup_text)
                        if percentage_match:
                            dealer_data["markup_percentage"] = float(percentage_match.group(1))
                            print(f"Found markup text: {dealer_data['markup_percentage']}%")
                    except ValueError:
                        print(f"Couldn't convert markup value to float: {markup_text}")
            elif "quantity" in header_text or "capacity" in header_text or "max" in header_text:
                next_p = header.find_next('p')
                if next_p:
                    quantity_text = next_p.get_text().strip()
                    try:
                        # Extract numeric value
                        quantity_match = re.search(r'(\d+)', quantity_text)
                        if quantity_match:
                            dealer_data["max_quantity"] = int(quantity_match.group(1))
                            print(f"Found quantity text: {dealer_data['max_quantity']}")
                    except ValueError:
                        print(f"Couldn't convert quantity value to int: {quantity_text}")
    except Exception as e:
        print(f"Error in section extraction: {e}")


def _extract_from_templates(article, dealer_data):
    """Extract dealer data from template-defined data."""
    try:
        print("Trying template data extraction...")
        # Check for data in specially formatted areas, which might be from templates
        data_blocks = article.find_all('div', class_='data')
        for block in data_blocks:
            # Look for header inside or before the block
            header = block.find_previous_sibling('div', class_='header') or block.find('div', class_='header')
            if header:
                header_text = header.get_text().strip().lower()
                value_text = block.get_text().strip()
                
                print(f"Found data block: {header_text} = {value_text}")
                
                if "region" in header_text:
                    dealer_data["region"] = value_text
                elif "standard" in header_text:
                    if "low" in value_text.lower():
                        dealer_data["standards"] = "Low"
                    elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                        dealer_data["standards"] = "Moderate"
                    elif "high" in value_text.lower():
                        dealer_data["standards"] = "High"
                elif "effect" in header_text and ("preferred" in header_text or "favorite" in header_text or "favourite" in header_text):
                    effects = process_effects_list([value_text])
                    dealer_data["preferred_effects"] = effects
                elif "markup" in header_text or "margin" in header_text:
                    try:
                        # Extract percentage value
                        percentage_match = re.search(r'(\d+(\.\d+)?)%?', value_text)
                        if percentage_match:
                            dealer_data["markup_percentage"] = float(percentage_match.group(1))
                    except ValueError:
                        print(f"Couldn't convert markup value to float: {value_text}")
                elif "quantity" in header_text or "capacity" in header_text or "max" in header_text:
                    try:
                        # Extract numeric value
                        quantity_match = re.search(r'(\d+)', value_text)
                        if quantity_match:
                            dealer_data["max_quantity"] = int(quantity_match.group(1))
                    except ValueError:
                        print(f"Couldn't convert quantity value to int: {value_text}")
    except Exception as e:
        print(f"Error in template data extraction: {e}")


def _extract_from_text_patterns(article, dealer_data):
    """Extract dealer data from direct text patterns in the HTML."""
    try:
        print("Trying direct text pattern search...")
        html_content = str(article)
        
        # Look for region data
        region_match = re.search(r'[Rr]egion\s*[:-]\s*([^<>\n,]+)', html_content)
        if region_match and not dealer_data["region"]:
            dealer_data["region"] = region_match.group(1).strip()
            print(f"Found region via regex: {dealer_data['region']}")
        
        # Look for standards data
        standards_match = re.search(r'[Ss]tandards?\s*[:-]\s*([^<>\n,]+)', html_content)
        if standards_match and not dealer_data["standards"]:
            standards_text = standards_match.group(1).strip().lower()
            if "low" in standards_text:
                dealer_data["standards"] = "Low"
            elif "moderate" in standards_text or "medium" in standards_text:
                dealer_data["standards"] = "Moderate"
            elif "high" in standards_text:
                dealer_data["standards"] = "High"
            print(f"Found standards via regex: {dealer_data['standards']}")
        
        # Look for effects data
        effects_match = re.search(r'[Pp]referred [Ee]ffects?\s*[:-]\s*([^<>]+?)(?:<|$)', html_content) or \
                       re.search(r'[Ff]av(?:ou|o)rite [Ee]ffects?\s*[:-]\s*([^<>]+?)(?:<|$)', html_content)
        if effects_match and not dealer_data["preferred_effects"]:
            effects_text = effects_match.group(1).strip()
            effects = process_effects_list([effects_text])
            dealer_data["preferred_effects"] = effects
            print(f"Found effects via regex: {dealer_data['preferred_effects']}")
        
        # Look for markup data
        markup_match = re.search(r'[Mm]arkup(?:\s*[Pp]ercentage)?\s*[:-]\s*([^<>\n,]+)', html_content) or \
                      re.search(r'[Mm]argin\s*[:-]\s*([^<>\n,]+)', html_content)
        if markup_match and dealer_data["markup_percentage"] == 0.0:
            markup_text = markup_match.group(1).strip()
            try:
                # Extract percentage value
                percentage_match = re.search(r'(\d+(\.\d+)?)%?', markup_text)
                if percentage_match:
                    dealer_data["markup_percentage"] = float(percentage_match.group(1))
                    print(f"Found markup via regex: {dealer_data['markup_percentage']}%")
            except ValueError:
                print(f"Couldn't convert markup value to float: {markup_text}")
        
        # Look for quantity data
        quantity_match = re.search(r'[Mm]ax(?:imum)?\s*[Qq]uantity\s*[:-]\s*([^<>\n,]+)', html_content) or \
                        re.search(r'[Cc]apacity\s*[:-]\s*([^<>\n,]+)', html_content)
        if quantity_match and dealer_data["max_quantity"] == 0:
            quantity_text = quantity_match.group(1).strip()
            try:
                # Extract numeric value
                quantity_match = re.search(r'(\d+)', quantity_text)
                if quantity_match:
                    dealer_data["max_quantity"] = int(quantity_match.group(1))
                    print(f"Found quantity via regex: {dealer_data['max_quantity']}")
            except ValueError:
                print(f"Couldn't convert quantity value to int: {quantity_text}")
                
        # Look for transaction data in sections
        transaction_section_match = re.search(r'(?:<h[23]>.*?[Tt]ransactions?.*?</h[23]>)(.*?)(?:<h[23]>|$)', html_content, re.DOTALL)
        if transaction_section_match:
            transaction_html = transaction_section_match.group(1).strip()
            # Try to find individual transactions
            transaction_matches = re.findall(r'<li>(.*?)</li>', transaction_html, re.DOTALL)
            if transaction_matches:
                for transaction_text in transaction_matches:
                    clean_text = re.sub(r'<[^>]+>', '', transaction_text).strip()
                    if clean_text:
                        # Try to identify date, product, quantity, price
                        # Example: "300 Sweet Monkey units at $100 each (04/25/2025)"
                        transaction = {"text": clean_text}
                        
                        # Extract date
                        date_match = re.search(r'\((\d{2}/\d{2}/\d{4})\)', clean_text)
                        if date_match:
                            transaction["date"] = date_match.group(1)
                            # Update last transaction date if this is more recent
                            if not dealer_data["last_transaction_date"] or transaction["date"] > dealer_data["last_transaction_date"]:
                                dealer_data["last_transaction_date"] = transaction["date"]
                        
                        # Extract quantity, product and price
                        quantity_match = re.search(r'(\d+)\s+([^$]+?)(?:\s+at\s+\$(\d+))?', clean_text)
                        if quantity_match:
                            transaction["quantity"] = int(quantity_match.group(1))
                            transaction["product"] = quantity_match.group(2).strip()
                            if quantity_match.group(3):
                                transaction["price"] = int(quantity_match.group(3))
                        
                        dealer_data["transactions"].append(transaction)
                        print(f"Found transaction: {transaction}")
    except Exception as e:
        print(f"Error in direct text search: {e}")


def fetch_all_dealers(callback=None):
    """Fetch all dealers from the Dealers wiki page.
    
    Args:
        callback (function, optional): Function to call with progress updates
        
    Returns:
        list: List of dealer data dictionaries
    """
    dealers = []
    
    try:
        if callback:
            callback("Connecting to wiki...", 0)
        
        # Request headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Get the dealers page
        url = "https://schedule-1.fandom.com/wiki/Dealers"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all dealer links
        dealer_links = []
        
        # Different ways to find dealer links
        # Look for links in a list
        for ul in soup.find_all('ul'):
            for li in ul.find_all('li'):
                a_tag = li.find('a')
                if a_tag and a_tag.has_attr('href') and "/wiki/" in a_tag['href'] and ":" not in a_tag['href']:
                    dealer_links.append("https://schedule-1.fandom.com" + a_tag['href'])
        
        # Also look for links in paragraphs
        for a_tag in soup.find_all('a'):
            if a_tag.has_attr('href') and "/wiki/" in a_tag['href'] and ":" not in a_tag['href']:
                full_url = "https://schedule-1.fandom.com" + a_tag['href']
                if full_url not in dealer_links:
                    dealer_links.append(full_url)
        
        if not dealer_links:
            print("No dealer links found on the page")
            if callback:
                callback("No dealer links found", 100)
            return dealers
        
        print(f"Found {len(dealer_links)} potential dealer links")
        
        # Process each dealer
        for i, link in enumerate(dealer_links):
            progress = (i / len(dealer_links)) * 100
            
            try:
                dealer_name = link.split('/')[-1].replace('_', ' ')
                
                if callback:
                    callback(f"Processing {i+1} of {len(dealer_links)}: {dealer_name}", progress)
                
                # Request the dealer page
                print(f"Fetching {dealer_name} from {link}")
                response = requests.get(link, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract dealer name from title
                title = soup.find('title')
                name = title.text.split('|')[0].strip() if title else dealer_name
                
                # Skip if this is a category page, template, or redirection
                if ("Category:" in name or "Template:" in name or 
                    soup.find('div', class_='mw-redirectedfrom')):
                    print(f"Skipping {name} - not a dealer page")
                    continue
                
                # Extract dealer data
                dealer_data = extract_dealer_data_from_html(soup, name, link)
                
                # Add to dealers list if we got meaningful data
                if (dealer_data["region"] != "Not Available" or 
                    dealer_data["standards"] != "Not Available" or 
                    dealer_data["preferred_effects"] != ["Not Available"] or
                    dealer_data["markup_percentage"] > 0 or
                    dealer_data["max_quantity"] > 0):
                    dealers.append(dealer_data)
                    print(f"Added {name} with {len(dealer_data['preferred_effects'])} preferred effects")
                else:
                    print(f"Skipping {name} - no meaningful data found")
                
            except Exception as e:
                print(f"Error processing {link}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        if callback:
            callback(f"Completed fetching {len(dealers)} dealers", 100)
        
    except Exception as e:
        print(f"Error fetching dealers: {str(e)}")
        if callback:
            callback(f"Error: {str(e)}", 100)
        import traceback
        traceback.print_exc()
    
    return dealers


def add_dealer_transaction(dealer_data, dealer_name, product, quantity, price, date=None):
    """Add a transaction to a dealer's history.
    
    Args:
        dealer_data (dict): The dealer data dictionary
        dealer_name (str): Name of the dealer
        product (str): Name of the product sold
        quantity (int): Quantity of product sold
        price (int): Price per unit
        date (str, optional): Date in MM/DD/YYYY format. If None, current date is used.
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not date:
        date = datetime.now().strftime('%m/%d/%Y')
    
    # Find the dealer
    for dealer in dealer_data.get("dealers", []):
        if dealer["name"].lower() == dealer_name.lower():
            # Create transaction record
            transaction = {
                "date": date,
                "product": product,
                "quantity": quantity,
                "price": price,
                "text": f"{quantity} {product} units at ${price} each ({date})"
            }
            
            # Add to transactions list
            dealer.setdefault("transactions", []).append(transaction)
            
            # Update last transaction date if this is more recent
            if not dealer.get("last_transaction_date") or date > dealer["last_transaction_date"]:
                dealer["last_transaction_date"] = date
            
            return True
    
    return False


def estimate_dealer_profit(dealer, product_name, quantity, base_value):
    """Estimate the profit a dealer will make based on their markup percentage.
    
    Args:
        dealer (dict): Dealer data dictionary
        product_name (str): Name of the product
        quantity (int): Quantity of product
        base_value (int): Base value of the product
        
    Returns:
        dict: Profit calculation, including dealer's price, markup, total value, etc.
    """
    # Use percentage_taken as the markup
    markup = dealer.get("percentage_taken", 20.0)
    
    # Calculate dealer's price
    dealer_price = base_value * (1 + (markup / 100))
    
    # Calculate total values
    total_base_value = base_value * quantity
    total_dealer_value = dealer_price * quantity
    dealer_profit = total_dealer_value - total_base_value
    
    return {
        "dealer_name": dealer["name"],
        "product": product_name,
        "quantity": quantity,
        "base_value": base_value,
        "dealer_price": dealer_price,
        "markup_percentage": markup,
        "total_base_value": total_base_value,
        "total_dealer_value": total_dealer_value,
        "dealer_profit": dealer_profit
    }


def find_best_dealer_for_product(dealer_data, product_name, product_effects):
    """Find the best dealer for a given product based on effect matches and markup.
    
    Args:
        dealer_data (dict): The dealer data dictionary
        product_name (str): Name of the product
        product_effects (list): List of effects in the product
        
    Returns:
        list: Ranked list of dealers with matching scores
    """
    matches = []
    
    for dealer in dealer_data.get("dealers", []):
        # Count matching effects
        matching_effects = 0
        for effect in product_effects:
            if effect in dealer.get("preferred_effects", []):
                matching_effects += 1
        
        # Calculate effect match percentage
        effect_match = 0
        if dealer.get("preferred_effects"):
            effect_match = (matching_effects / len(dealer["preferred_effects"])) * 100 if len(dealer["preferred_effects"]) > 0 else 0
        
        # Get markup
        markup = dealer.get("percentage_taken", 20.0)
        
        # Get max quantity
        max_quantity = dealer.get("max_quantity", 0)
        
        # Calculate overall score (higher is better)
        # Effect match is most important, then lower markup, then higher quantity capacity
        score = (effect_match * 0.6) + ((100 - markup) * 0.3) + (min(max_quantity, 500) / 500 * 0.1 * 100)
        
        matches.append({
            "dealer_name": dealer["name"],
            "region": dealer.get("region", "Not Available"),
            "location": dealer.get("location", "Unknown"),
            "matching_effects": matching_effects,
            "effect_match_percentage": effect_match,
            "markup_percentage": markup,
            "max_quantity": max_quantity,
            "score": score
        })
    
    # Sort by score (descending)
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    return matches


def calculate_batch_profit(recipe_name, seed_cost, yield_amount, recipe_value, quantity=1):
    """Calculate expected profit for a growth batch.
    
    Args:
        recipe_name (str): Name of the recipe
        seed_cost (float): Cost of seeds
        yield_amount (int): Expected yield amount
        recipe_value (float): Value of a single unit of the recipe
        quantity (int): Number of batches
        
    Returns:
        dict: Profit calculation
    """
    # Calculate costs and revenue
    total_seed_cost = seed_cost * quantity
    total_yield = yield_amount * quantity
    total_revenue = recipe_value * total_yield
    total_profit = total_revenue - total_seed_cost
    roi_percentage = (total_profit / total_seed_cost) * 100
    
    return {
        "recipe_name": recipe_name,
        "batches": quantity,
        "seed_cost_per_batch": seed_cost,
        "total_seed_cost": total_seed_cost,
        "yield_per_batch": yield_amount,
        "total_yield": total_yield,
        "value_per_unit": recipe_value,
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "roi_percentage": roi_percentage
    }


def fetch_dealer_details(url, headers=None):
    """Fetch detailed information about a dealer from their wiki page.
    
    Args:
        url (str): URL of the dealer's wiki page
        headers (dict, optional): Request headers
        
    Returns:
        dict: Dictionary containing dealer information
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    # Initialize dealer data
    dealer_data = {
        "name": "",
        "region": "",
        "location": "",
        "initial_buy_in": 0,
        "percentage_taken": 0.0,
        "assignable_customers": 0,
        "appearance": "",
        "location_details": "",
        "combat_info": "",
        "preferred_effects": [],
        "max_quantity": 300,  # Default to 300 based on the Benji example
        "transactions": [],
        "last_transaction_date": "",
        "notes": ""
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the dealer name from the title
        title = soup.find('title')
        if title:
            dealer_name = title.text.split('|')[0].strip()
            dealer_data["name"] = dealer_name
        
        # Find the dealer info box
        infobox = soup.find('div', class_='portable-infobox') or soup.find('aside', class_='portable-infobox')
        if infobox:
            # Extract info from the infobox
            for item in infobox.find_all('div', class_='pi-item'):
                label = item.find('h3', class_='pi-data-label')
                value = item.find('div', class_='pi-data-value')
                
                if label and value:
                    label_text = label.get_text().strip().lower()
                    value_text = value.get_text().strip()
                    
                    if "region" in label_text:
                        dealer_data["region"] = value_text
                    elif "location" in label_text:
                        dealer_data["location"] = value_text
                    elif "initial buy in" in label_text:
                        try:
                            # Strip $ and commas and convert to int
                            buy_in_match = re.search(r'\$?(\d+(?:,\d+)*)', value_text)
                            if buy_in_match:
                                dealer_data["initial_buy_in"] = int(buy_in_match.group(1).replace(',', ''))
                        except ValueError:
                            pass
                    elif "percentage taken" in label_text:
                        try:
                            # Strip % and convert to float
                            percentage_match = re.search(r'(\d+(?:\.\d+)?)%?', value_text)
                            if percentage_match:
                                dealer_data["percentage_taken"] = float(percentage_match.group(1))
                        except ValueError:
                            pass
                    elif "assignable customers" in label_text:
                        try:
                            # Extract number
                            customers_match = re.search(r'(\d+)', value_text)
                            if customers_match:
                                dealer_data["assignable_customers"] = int(customers_match.group(1))
                        except ValueError:
                            pass
        
        # Find the article content
        article = soup.find('article', class_='WikiaArticle') or soup.find('div', class_='mw-parser-output')
        if not article:
            article = soup
        
        # Extract appearance
        appearance_section = article.find(lambda tag: tag.name in ['h2', 'h3'] and 'appearance' in tag.get_text().lower())
        if appearance_section:
            next_tag = appearance_section.find_next(['p', 'div'])
            if next_tag:
                dealer_data["appearance"] = next_tag.get_text().strip()
        
        # Extract location details
        location_section = article.find(lambda tag: tag.name in ['h2', 'h3'] and 'location' in tag.get_text().lower())
        if location_section:
            next_tag = location_section.find_next(['p', 'div'])
            if next_tag:
                dealer_data["location_details"] = next_tag.get_text().strip()
        
        # Extract combat info
        combat_section = article.find(lambda tag: tag.name in ['h2', 'h3'] and 'combat' in tag.get_text().lower())
        if combat_section:
            next_tag = combat_section.find_next(['p', 'div'])
            if next_tag:
                dealer_data["combat_info"] = next_tag.get_text().strip()
        
        # Extract controversy if it exists
        controversy_section = article.find(lambda tag: tag.name in ['h2', 'h3'] and 'controversy' in tag.get_text().lower())
        if controversy_section:
            next_tag = controversy_section.find_next(['p', 'div'])
            if next_tag:
                dealer_data["controversy"] = next_tag.get_text().strip()
        
        # Extract bugs if they exist
        bugs_section = article.find(lambda tag: tag.name in ['h2', 'h3'] and 'bugs' in tag.get_text().lower())
        if bugs_section:
            next_tag = bugs_section.find_next(['p', 'div'])
            if next_tag:
                dealer_data["bugs"] = next_tag.get_text().strip()
        
        # Extract preferred effects if mentioned
        html_content = str(article)
        effects_match = re.search(r'(?:prefers|likes|enjoys|favorite|preferred)\s+(?:effects?|products?)\s*(?:with|like|such as)?\s*[:-]?\s*([^.<>]+?)(?:<|\.|\n|$)', html_content, re.IGNORECASE)
        if effects_match:
            effects_text = effects_match.group(1).strip()
            # Split by common separators and clean up
            effects = [e.strip() for e in re.split(r'[,;&/]+', effects_text) if e.strip()]
            dealer_data["preferred_effects"] = effects
        
        # Extract general description/notes from the first paragraph
        first_p = article.find('p')
        if first_p:
            dealer_data["notes"] = first_p.get_text().strip()
        
    except Exception as e:
        print(f"Error fetching dealer details from {url}: {e}")
    
    return dealer_data


def fetch_dealers_from_urls(urls, callback=None):
    """Fetch dealer information from a list of wiki URLs.
    
    Args:
        urls (list): List of wiki URLs for dealers
        callback (function, optional): Function to call with progress updates
        
    Returns:
        list: List of dealer data dictionaries
    """
    dealers = []
    
    for i, url in enumerate(urls):
        try:
            if callback:
                progress = (i / len(urls)) * 100
                callback(f"Fetching data from {url.split('/')[-1].replace('_', ' ')}", progress)
                
            print(f"Fetching data from {url}")
            dealer_data = fetch_dealer_details(url)
            
            if dealer_data["name"]:
                dealers.append(dealer_data)
                print(f"Successfully fetched data for {dealer_data['name']}")
            else:
                print(f"Failed to extract dealer name from {url}")
        except Exception as e:
            print(f"Error processing {url}: {e}")
    
    return dealers


def update_dealers_preserve_assignments(file_path="dealer_data.json", progress_callback=None):
    """Update dealer data from wiki while preserving customer assignments.
    
    Args:
        file_path (str): Path to the dealer data file
        progress_callback (function, optional): Function to call with progress updates
        
    Returns:
        dict: Updated dealer data with preserved customer assignments
    """
    # Load existing dealer data with customer assignments
    if progress_callback:
        progress_callback("Loading existing dealer data...", 5)
    existing_data = load_dealer_data(file_path)
    existing_dealers = {d["name"]: d for d in existing_data.get("dealers", [])}
    
    # Create a mapping of dealer names to their assigned customers
    if progress_callback:
        progress_callback("Preserving customer assignments...", 10)
    assignments = {}
    for dealer_name, dealer in existing_dealers.items():
        if "assigned_customers" in dealer:
            assignments[dealer_name] = dealer["assigned_customers"]
    
    # Fetch new dealer data from the wiki - avoid circular import by importing here
    if progress_callback:
        progress_callback("Fetching new dealer data from wiki...", 15)
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def fetch_progress(message, percentage):
        # Map the fetch progress (0-100) to our overall progress (15-90)
        if progress_callback:
            mapped_percentage = 15 + (percentage * 0.75)
            progress_callback(message, mapped_percentage)
    
    from fetch_dealers_improved import fetch_actual_dealers
    
    try:
        new_dealers = fetch_actual_dealers(progress_callback=fetch_progress if progress_callback else None)
        
        # If we couldn't fetch dealers, use existing data
        if not new_dealers:
            if progress_callback:
                progress_callback("Warning: No dealers fetched from wiki. Using existing dealer data.", 90)
            print("Warning: No dealers fetched from wiki. Using existing dealer data.")
            return existing_data
        
        # Merge the new dealer data with existing customer assignments
        if progress_callback:
            progress_callback("Merging new dealer data with assignments...", 95)
        
        for dealer in new_dealers:
            dealer_name = dealer["name"]
            if dealer_name in assignments:
                dealer["assigned_customers"] = assignments[dealer_name]
        
        # Save the updated dealer data
        updated_data = {"dealers": new_dealers}
        if progress_callback:
            progress_callback("Saving updated dealer data...", 98)
        save_dealer_data(updated_data, file_path)
        
        if progress_callback:
            progress_callback("Dealer data update complete", 100)
        
        return updated_data
        
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error updating dealer data: {e}", 100)
        print(f"Error updating dealer data: {e}")
        # Return existing data in case of error
        return existing_data