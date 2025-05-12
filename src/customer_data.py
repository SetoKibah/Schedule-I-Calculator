"""
Customer data management module for Schedule I Calculator.
Handles loading, saving, and processing customer data.
"""
import json
import re
import os
from datetime import datetime


def load_customer_data(file_path="customer_data.json"):
    """Load customer data from a JSON file.
    
    Args:
        file_path (str): Path to the customer data JSON file
        
    Returns:
        dict: Dictionary containing customer data
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Return empty data structure if file is corrupted
            return {"customers": []}
    return {"customers": []}


def save_customer_data(data, file_path="customer_data.json"):
    """Save customer data to a JSON file.
    
    Args:
        data (dict): Dictionary containing customer data
        file_path (str): Path to save the customer data JSON file
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving customer data: {e}")
        return False


def fix_customer_data(customer_data):
    """Fix and standardize customer data entries.
    
    This function ensures all customer data is properly formatted:
    - Fixes "Medium" standards to "Moderate"
    - Separates effects and relations that are squished together
    - Sets default values for missing data to "Not Available"
    
    Args:
        customer_data (dict): Dictionary containing customer data
        
    Returns:
        dict: The fixed customer data
    """
    # Make a copy to avoid modifying the original
    fixed_data = {"customers": []}
    
    for customer in customer_data.get("customers", []):
        fixed_customer = customer.copy()
        
        # Fix standards - change "Medium" to "Moderate"
        if fixed_customer.get("standards") == "Medium":
            fixed_customer["standards"] = "Moderate"
        
        # Set default values for missing data
        if not fixed_customer.get("region"):
            fixed_customer["region"] = "Not Available"
            
        if not fixed_customer.get("standards"):
            fixed_customer["standards"] = "Not Available"
            
        if not fixed_customer.get("favorite_effects"):
            fixed_customer["favorite_effects"] = ["Not Available"]
        else:
            # Process effects list to separate squished effects
            fixed_customer["favorite_effects"] = process_effects_list(fixed_customer["favorite_effects"])
            
        if not fixed_customer.get("relations"):
            fixed_customer["relations"] = ["Not Available"]
        else:
            # Process relations list to separate squished names
            fixed_customer["relations"] = process_relations_list(fixed_customer["relations"])
            
        if not fixed_customer.get("residency"):
            fixed_customer["residency"] = "Not Available"
            
        if not fixed_customer.get("work"):
            fixed_customer["work"] = "Not Available"
        
        fixed_data["customers"].append(fixed_customer)
    
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
    
    # List of all known effects for pattern matching
    known_effects = [
        "Calming", "Sedating", "Refreshing", "Euphoric", "Energizing", 
        "Disorienting", "Foggy", "Glowing", "Balding", "Athletic", 
        "Focused", "Thought-Provoking", "Sneaky", "Munchies", 
        "Smelly", "Spicy", "Toxic", "Slippery", "Calorie-Dense",
        "Shrinking", "Gingeritis", "Long Faced", "Bright-Eyed",
        "Seizure-Inducing", "Laxative", "Paranoia", "Tropic Thunder",
        "Schizophrenic", "Explosive", "Anti-Gravity", "Lethal",
        "Jennerising", "Electrifying"
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
    
    return new_effects if new_effects else []


def process_relations_list(relations):
    """Process a list of relations, handling cases where they're squished together.
    
    Args:
        relations (list): List of relations strings
        
    Returns:
        list: Properly separated relations
    """
    if not relations:
        return []
    
    # Process each relation string in the list
    new_relations = []
    for relation_text in relations:
        if not relation_text:
            continue
            
        # First try splitting by commas and other separators
        for part in re.split(r'[,;/]+', relation_text):
            part = part.strip()
            if not part:
                continue
                
            # If the relation is unusually long without spaces, try to split it
            if len(part) > 20 and not re.search(r'\s', part):
                # Split by capital letter preceded by lowercase (e.g., "JohnSmith" -> ["John", "Smith"])
                split_relations = re.findall(r'[A-Z][^A-Z]*', part)
                if split_relations:
                    new_relations.extend(split_relations)
                else:
                    new_relations.append(part)
            else:
                new_relations.append(part)
    
    return new_relations if new_relations else []


def extract_customer_data_from_html(soup, name, url):
    """Extract customer data from HTML soup.
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object containing HTML
        name (str): Customer name
        url (str): Source URL
        
    Returns:
        dict: Extracted customer data
    """
    customer_data = {
        "name": name,
        "region": "",
        "standards": "",
        "favorite_effects": [],
        "relations": [],
        "residency": "",
        "work": "",
        "notes": f"Imported from {url} on {datetime.now().strftime('%Y-%m-%d')}"
    }
    
    print(f"\n--- EXTRACTING DATA FOR {name} ---")
    
    # Try to find the article content
    article = soup.find('article', class_='WikiaArticle') or soup.find('div', class_='mw-parser-output')
    if not article:
        print(f"Warning: Could not find article content for {name}")
        # Use whole page if article section not found
        article = soup
    
    # Multiple approaches to extract data from different wiki formats
    _extract_from_tables(article, customer_data)
    _extract_from_infoboxes(article, customer_data)
    _extract_from_bold_text(article, customer_data)
    _extract_from_sections(article, customer_data)
    _extract_from_templates(article, customer_data)
    _extract_from_text_patterns(article, customer_data)
    
    # Set default values for any empty fields
    if not customer_data["region"]:
        customer_data["region"] = "Not Available"
        
    if not customer_data["standards"]:
        customer_data["standards"] = "Not Available"
        
    if not customer_data["favorite_effects"]:
        customer_data["favorite_effects"] = ["Not Available"]
        
    if not customer_data["relations"]:
        customer_data["relations"] = ["Not Available"]
        
    if not customer_data["residency"]:
        customer_data["residency"] = "Not Available"
        
    if not customer_data["work"]:
        customer_data["work"] = "Not Available"
    
    # Standardize "Medium" to "Moderate"
    if customer_data["standards"] == "Medium":
        customer_data["standards"] = "Moderate"
    
    # Print summary of what we found
    print("\nExtraction summary:")
    print(f"Region: {customer_data['region']}")
    print(f"Standards: {customer_data['standards']}")
    print(f"Favorite Effects: {customer_data['favorite_effects']}")
    print(f"Relations: {customer_data['relations']}")
    print(f"Residency: {customer_data['residency'][:30]}..." if len(customer_data['residency']) > 30 else f"Residency: {customer_data['residency']}")
    print(f"Work: {customer_data['work'][:30]}..." if len(customer_data['work']) > 30 else f"Work: {customer_data['work']}")
    
    return customer_data


def _extract_from_tables(article, customer_data):
    """Extract customer data from tables."""
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
                        customer_data["region"] = value_text
                    elif "standard" in header_text:
                        if "low" in value_text.lower():
                            customer_data["standards"] = "Low"
                        elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                            customer_data["standards"] = "Moderate"
                        elif "high" in value_text.lower():
                            customer_data["standards"] = "High"
                    elif "effect" in header_text and ("favorite" in header_text or "favourite" in header_text):
                        effects = process_effects_list([value_text])
                        customer_data["favorite_effects"] = effects
                    elif "relation" in header_text:
                        relations = process_relations_list([value_text])
                        customer_data["relations"] = relations
    except Exception as e:
        print(f"Error in table extraction: {e}")


def _extract_from_infoboxes(article, customer_data):
    """Extract customer data from div-based infoboxes."""
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
                        customer_data["region"] = value_text
                    elif "standard" in label_text:
                        if "low" in value_text.lower():
                            customer_data["standards"] = "Low"
                        elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                            customer_data["standards"] = "Moderate"
                        elif "high" in value_text.lower():
                            customer_data["standards"] = "High"
                    elif "effect" in label_text and ("favorite" in label_text or "favourite" in label_text):
                        effects = process_effects_list([value_text])
                        customer_data["favorite_effects"] = effects
                    elif "relation" in label_text:
                        relations = process_relations_list([value_text])
                        customer_data["relations"] = relations
        
        # Try older style div infoboxes
        div_labels = article.find_all('div', class_='label')
        for label in div_labels:
            label_text = label.get_text().strip().lower()
            value_div = label.find_next_sibling('div')
            
            if value_div:
                value_text = value_div.get_text().strip()
                print(f"Found div label: {label_text} = {value_text}")
                
                if "region" in label_text:
                    customer_data["region"] = value_text
                elif "standard" in label_text:
                    if "low" in value_text.lower():
                        customer_data["standards"] = "Low"
                    elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                        customer_data["standards"] = "Moderate"
                    elif "high" in value_text.lower():
                        customer_data["standards"] = "High"
                elif "effect" in label_text and ("favorite" in label_text or "favourite" in label_text):
                    # Check if it's a list
                    list_items = value_div.find_all('li')
                    if list_items:
                        effects = [li.get_text().strip() for li in list_items]
                        effects = process_effects_list(effects)
                    else:
                        effects = process_effects_list([value_text])
                    customer_data["favorite_effects"] = effects
                elif "relation" in label_text:
                    # Check if it's a list
                    list_items = value_div.find_all('li')
                    if list_items:
                        relations = [li.get_text().strip() for li in list_items]
                        relations = process_relations_list(relations)
                    else:
                        relations = process_relations_list([value_text])
                    customer_data["relations"] = relations
    except Exception as e:
        print(f"Error in div infobox extraction: {e}")


def _extract_from_bold_text(article, customer_data):
    """Extract customer data from bold text patterns."""
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
                    customer_data["region"] = value_text
                elif "standard" in bold_text:
                    if "low" in value_text.lower():
                        customer_data["standards"] = "Low"
                    elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                        customer_data["standards"] = "Moderate"
                    elif "high" in value_text.lower():
                        customer_data["standards"] = "High"
                elif "effect" in bold_text and ("favorite" in bold_text or "favourite" in bold_text):
                    effects = process_effects_list([value_text])
                    customer_data["favorite_effects"] = effects
                elif "relation" in bold_text:
                    relations = process_relations_list([value_text])
                    customer_data["relations"] = relations
    except Exception as e:
        print(f"Error in bold text extraction: {e}")


def _extract_from_sections(article, customer_data):
    """Extract customer data from section headings."""
    try:
        print("Trying section-based extraction...")
        headers = article.find_all(['h2', 'h3', 'h4'])
        for header in headers:
            header_text = header.get_text().strip().lower()
            print(f"Found section header: {header_text}")
            
            if "residency" in header_text:
                # Get the next paragraph
                next_p = header.find_next('p')
                if next_p:
                    customer_data["residency"] = next_p.get_text().strip()
                    print(f"Found residency text: {customer_data['residency'][:30]}...")
            elif "work" in header_text:
                # Get the next paragraph
                next_p = header.find_next('p')
                if next_p:
                    customer_data["work"] = next_p.get_text().strip()
                    print(f"Found work text: {customer_data['work'][:30]}...")
    except Exception as e:
        print(f"Error in section extraction: {e}")


def _extract_from_templates(article, customer_data):
    """Extract customer data from template-defined data."""
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
                    customer_data["region"] = value_text
                elif "standard" in header_text:
                    if "low" in value_text.lower():
                        customer_data["standards"] = "Low"
                    elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                        customer_data["standards"] = "Moderate"
                    elif "high" in value_text.lower():
                        customer_data["standards"] = "High"
                elif "effect" in header_text and ("favorite" in header_text or "favourite" in header_text):
                    effects = process_effects_list([value_text])
                    customer_data["favorite_effects"] = effects
                elif "relation" in header_text:
                    relations = process_relations_list([value_text])
                    customer_data["relations"] = relations
    except Exception as e:
        print(f"Error in template data extraction: {e}")


def _extract_from_text_patterns(article, customer_data):
    """Extract customer data from direct text patterns in the HTML."""
    try:
        print("Trying direct text pattern search...")
        html_content = str(article)
        
        # Look for region data
        region_match = re.search(r'[Rr]egion\s*[:-]\s*([^<>\n,]+)', html_content)
        if region_match and not customer_data["region"]:
            customer_data["region"] = region_match.group(1).strip()
            print(f"Found region via regex: {customer_data['region']}")
        
        # Look for standards data
        standards_match = re.search(r'[Ss]tandards?\s*[:-]\s*([^<>\n,]+)', html_content)
        if standards_match and not customer_data["standards"]:
            standards_text = standards_match.group(1).strip().lower()
            if "low" in standards_text:
                customer_data["standards"] = "Low"
            elif "moderate" in standards_text or "medium" in standards_text:
                customer_data["standards"] = "Moderate"
            elif "high" in standards_text:
                customer_data["standards"] = "High"
            print(f"Found standards via regex: {customer_data['standards']}")
        
        # Look for effects data
        effects_match = re.search(r'[Ff]av(?:ou|o)rite [Ee]ffects?\s*[:-]\s*([^<>]+?)(?:<|$)', html_content)
        if effects_match and not customer_data["favorite_effects"]:
            effects_text = effects_match.group(1).strip()
            effects = process_effects_list([effects_text])
            customer_data["favorite_effects"] = effects
            print(f"Found effects via regex: {customer_data['favorite_effects']}")
        
        # Look for relations data
        relations_match = re.search(r'[Rr]elations?\s*[:-]\s*([^<>]+?)(?:<|$)', html_content)
        if relations_match and not customer_data["relations"]:
            relations_text = relations_match.group(1).strip()
            relations = process_relations_list([relations_text])
            customer_data["relations"] = relations
            print(f"Found relations via regex: {customer_data['relations']}")
        
        # Look for residency data
        if not customer_data["residency"]:
            residency_match = re.search(r'(?:<h[23]>.*?[Rr]esidency.*?</h[23]>)(.*?)(?:<h[23]>|$)', html_content, re.DOTALL)
            if residency_match:
                residency_html = residency_match.group(1).strip()
                # Extract text from paragraph if present
                paragraph_match = re.search(r'<p>(.*?)</p>', residency_html, re.DOTALL)
                if paragraph_match:
                    residency_text = paragraph_match.group(1).strip()
                    # Remove HTML tags
                    residency_text = re.sub(r'<[^>]+>', '', residency_text)
                    customer_data["residency"] = residency_text
                    print(f"Found residency via regex: {customer_data['residency'][:30]}...")
        
        # Look for work data
        if not customer_data["work"]:
            work_match = re.search(r'(?:<h[23]>.*?[Ww]ork.*?</h[23]>)(.*?)(?:<h[23]>|$)', html_content, re.DOTALL)
            if work_match:
                work_html = work_match.group(1).strip()
                # Extract text from paragraph if present
                paragraph_match = re.search(r'<p>(.*?)</p>', work_html, re.DOTALL)
                if paragraph_match:
                    work_text = paragraph_match.group(1).strip()
                    # Remove HTML tags
                    work_text = re.sub(r'<[^>]+>', '', work_text)
                    customer_data["work"] = work_text
                    print(f"Found work via regex: {customer_data['work'][:30]}...")
    except Exception as e:
        print(f"Error in direct text search: {e}")


def update_customers_preserve_assignments(file_path="customer_data.json", progress_callback=None):
    """Update customer data from wiki while preserving dealer assignments.
    
    Args:
        file_path (str): Path to the customer data file
        progress_callback (function, optional): Function to call with progress updates
        
    Returns:
        dict: Updated customer data
    """
    # Load existing customer data
    if progress_callback:
        progress_callback("Loading existing customer data...", 5)
    existing_data = load_customer_data(file_path)
    
    # Fetch new customer data from the wiki - avoid circular import by importing here
    if progress_callback:
        progress_callback("Preparing to fetch new customer data...", 10)
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def fetch_progress(message, percentage):
        # Map the fetch progress (0-100) to our overall progress (10-90)
        if progress_callback:
            mapped_percentage = 10 + (percentage * 0.8)
            progress_callback(message, mapped_percentage)
    
    from fetch_dealers_improved import fetch_all_customers
    
    try:
        if progress_callback:
            progress_callback("Connecting to customer wiki...", 15)
        
        new_customers = fetch_all_customers(progress_callback=fetch_progress if progress_callback else None)
        
        # If we couldn't fetch customers, use existing data
        if not new_customers:
            if progress_callback:
                progress_callback("Warning: No customers fetched from wiki. Using existing customer data.", 90)
            print("Warning: No customers fetched from wiki. Using existing customer data.")
            return existing_data
        
        # Fix customer data to ensure all fields are properly formatted
        if progress_callback:
            progress_callback("Standardizing customer data format...", 92)
        new_customers_fixed = []
        for customer in new_customers:
            # Fix standards formatting
            if customer.get("standards") == "Medium":
                customer["standards"] = "Moderate"
            
            # Make sure all required fields exist
            if "name" not in customer:
                continue  # Skip customers without names
                
            if "region" not in customer or not customer["region"]:
                customer["region"] = "Not Available"
                
            if "standards" not in customer or not customer["standards"]:
                customer["standards"] = "Not Available"
                
            if "favorite_effects" not in customer:
                customer["favorite_effects"] = []
                
            if "relations" not in customer:
                customer["relations"] = []
                
            if "residency" not in customer:
                customer["residency"] = "Not Available"
                
            if "work" not in customer:
                customer["work"] = "Not Available"
                
            new_customers_fixed.append(customer)
        
        # Save the updated customer data
        if progress_callback:
            progress_callback("Saving updated customer data...", 95)
        
        updated_data = {"customers": new_customers_fixed}
        save_customer_data(updated_data, file_path)
        
        if progress_callback:
            progress_callback("Customer data update complete", 100)
        
        return updated_data
        
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error updating customer data: {e}", 100)
        print(f"Error updating customer data: {e}")
        # Return existing data in case of error
        return existing_data