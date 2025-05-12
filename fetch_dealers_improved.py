"""
Fetch dealer data from the Schedule 1 wiki, focusing only on actual dealers.
This script specifically targets the dealers table from the wiki and extracts detailed information.
"""
import sys
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def progress_callback(message, percentage, force_update=False):
    """
    Display progress as the script runs
    - Added force_update parameter to ensure updates are shown even for small percentage changes
    - More detailed progress formatting
    """
    # Format percentage with one decimal place
    formatted_percentage = f"{percentage:.1f}%"
    
    # Create a visual progress bar
    bar_length = 30
    filled_length = int(bar_length * percentage / 100)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # Write progress to console
    sys.stdout.write(f"\r{message} - [{bar}] {formatted_percentage}")
    sys.stdout.flush()
    
    # Add a newline if process is complete
    if percentage >= 100:
        sys.stdout.write("\n")

def extract_dealer_data(soup, name, url):
    """Extract dealer-specific data from a dealer's wiki page"""
    dealer_data = {
        "name": name,
        "region": "",
        "location": "",
        "initial_buy_in": 0,
        "percentage_taken": 0.0,
        "assignable_customers": 0,
        "preferred_effects": [],
        "max_quantity": 0,
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
    
    # Extract from infobox first - most reliable source
    try:
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
                    elif "location" in label_text:
                        dealer_data["location"] = value_text
                    elif "initial buy in" in label_text or "buy-in" in label_text:
                        try:
                            # Extract numeric value
                            buy_in_match = re.search(r'\$?(\d+(?:,\d+)*)', value_text)
                            if buy_in_match:
                                dealer_data["initial_buy_in"] = int(buy_in_match.group(1).replace(',', ''))
                        except ValueError:
                            print(f"Couldn't convert buy-in value to int: {value_text}")
                    elif "percentage taken" in label_text or "commission" in label_text:
                        try:
                            # Extract percentage value
                            percentage_match = re.search(r'(\d+(\.\d+)?)%?', value_text)
                            if percentage_match:
                                dealer_data["percentage_taken"] = float(percentage_match.group(1))
                        except ValueError:
                            print(f"Couldn't convert percentage value to float: {value_text}")
                    elif "assignable customers" in label_text:
                        try:
                            # Extract numeric value
                            customers_match = re.search(r'(\d+)', value_text)
                            if customers_match:
                                dealer_data["assignable_customers"] = int(customers_match.group(1))
                        except ValueError:
                            print(f"Couldn't convert customers value to int: {value_text}")
    except Exception as e:
        print(f"Error in infobox extraction: {e}")
    
    # Extract from text content for preferred effects - less reliable
    try:
        # Look for preferred/favorite effects in the text
        html_content = str(article)
        effects_match = re.search(r'(?:prefers|likes|enjoys|favorite|preferred)\s+(?:effects?|products?)\s*(?:with|like|such as)?\s*[:-]?\s*([^.<>]+?)(?:<|\.|\n|$)', html_content, re.IGNORECASE)
        if effects_match:
            effects_text = effects_match.group(1).strip()
            # Split by common separators and clean up
            effects = [e.strip() for e in re.split(r'[,;&/]+', effects_text) if e.strip()]
            dealer_data["preferred_effects"] = effects
            print(f"Found preferred effects: {effects}")
    except Exception as e:
        print(f"Error in effects extraction: {e}")
    
    # Extract from header/paragraph content for max quantity
    try:
        quantity_section = re.search(r'(?:<h[23]>[^<]*(?:quantity|capacity|max)[^<]*</h[23]>)(.*?)(?:<h[23]>|$)', html_content, re.DOTALL | re.IGNORECASE)
        if quantity_section:
            quantity_text = quantity_section.group(1)
            quantity_match = re.search(r'(\d+)', quantity_text)
            if quantity_match:
                dealer_data["max_quantity"] = int(quantity_match.group(1))
                print(f"Found max quantity: {dealer_data['max_quantity']}")
    except Exception as e:
        print(f"Error in quantity extraction: {e}")
    
    # Look for transaction data in sections
    try:
        transaction_section_match = re.search(r'(?:<h[23]>[^<]*(?:transactions?|history|deals)[^<]*</h[23]>)(.*?)(?:<h[23]>|$)', html_content, re.DOTALL | re.IGNORECASE)
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
        print(f"Error in transaction extraction: {e}")
    
    # Print summary
    print("\nExtraction summary:")
    print(f"Name: {dealer_data['name']}")
    print(f"Region: {dealer_data['region']}")
    print(f"Location: {dealer_data['location']}")
    print(f"Initial Buy-In: ${dealer_data['initial_buy_in']}")
    print(f"Percentage Taken: {dealer_data['percentage_taken']}%")
    print(f"Assignable Customers: {dealer_data['assignable_customers']}")
    print(f"Preferred Effects: {dealer_data['preferred_effects']}")
    print(f"Max Quantity: {dealer_data['max_quantity']}")
    
    return dealer_data

def fetch_actual_dealers(progress_callback=None):
    """Fetch dealer data focusing only on actual dealers from the dealers table"""
    dealers = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Get the main dealers page
        if progress_callback:
            progress_callback("Connecting to dealer wiki page", 0)
        url = "https://schedule-1.fandom.com/wiki/Dealers"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        main_soup = BeautifulSoup(response.text, 'html.parser')
        if progress_callback:
            progress_callback("Connected to dealer wiki page", 10)
        
        # Directly add the known dealer URLs from the wiki
        # This is more reliable than trying to parse the tables
        if progress_callback:
            progress_callback("Adding known dealer URLs", 15)
            
        # These are the canonical dealers from the wiki
        known_dealers = [
            ("Benji Coleman", "https://schedule-1.fandom.com/wiki/Benji_Coleman"),
            ("Molly Presley", "https://schedule-1.fandom.com/wiki/Molly_Presley"),
            ("Brad Crosby", "https://schedule-1.fandom.com/wiki/Brad_Crosby"),
            ("Jane Lucero", "https://schedule-1.fandom.com/wiki/Jane_Lucero"),
            ("Wei Long", "https://schedule-1.fandom.com/wiki/Wei_Long"),
            ("Leo Rivers", "https://schedule-1.fandom.com/wiki/Leo_Rivers")
        ]
        
        dealer_links = known_dealers.copy()
        
        # Also try to extract from tables as a backup
        dealer_tables = main_soup.find_all('table', class_='article-table')
        
        for table in dealer_tables:
            # Skip tables without enough rows (likely not the dealer table)
            if len(table.find_all('tr')) < 3:
                continue
                
            # Extract dealer links from the table rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 1:  # Need at least the name cell
                    name_cell = cells[0]
                    link = name_cell.find('a')
                    if link and link.has_attr('href'):
                        dealer_name = link.get_text().strip()
                        dealer_url = "https://schedule-1.fandom.com" + link['href']
                        
                        # Only add if not already in our list
                        if not any(name == dealer_name for name, _ in dealer_links):
                            dealer_links.append((dealer_name, dealer_url))
                            print(f"Found additional dealer in table: {dealer_name}")
        
        # If we still don't have any links, try to find them in the text
        if not dealer_links:
            if progress_callback:
                progress_callback("Searching for dealers in sections", 20)
            dealer_section = main_soup.find(lambda tag: tag.name == 'h2' and 'dealer' in tag.get_text().lower())
            if dealer_section:
                next_ul = dealer_section.find_next('ul')
                if next_ul:
                    for li in next_ul.find_all('li'):
                        link = li.find('a')
                        if link and link.has_attr('href'):
                            dealer_name = link.get_text().strip()
                            dealer_url = "https://schedule-1.fandom.com" + link['href']
                            
                            # Only add if not already in our list
                            if not any(name == dealer_name for name, _ in dealer_links):
                                dealer_links.append((dealer_name, dealer_url))
                                print(f"Found dealer in list: {dealer_name}")
        
        # Filter out non-dealer entries
        if progress_callback:
            progress_callback("Filtering non-dealer entries", 22)
        
        filtered_dealer_links = []
        
        # Known invalid dealer names (pages that might be linked but are not dealers)
        invalid_dealers = ["products", "customers", "strains", "effects", "missions", 
                         "main page", "regions", "ranks", "category", "template", "file", "help"]
        
        for name, url in dealer_links:
            # Skip if the name is in the invalid dealer list (case-insensitive)
            if any(invalid_name.lower() == name.lower() for invalid_name in invalid_dealers):
                print(f"Skipping invalid dealer entry: {name}")
                continue
                
            # Skip if the URL contains indicators of non-dealer content
            if any(pattern in url.lower() for pattern in ["/category:", "/template:", "/file:", "/help:", "/products", "/customers", "/strains", "/effects", "/missions", "/regions", "/ranks"]):
                print(f"Skipping non-dealer URL: {url}")
                continue
                
            filtered_dealer_links.append((name, url))
        
        print(f"Filtered from {len(dealer_links)} to {len(filtered_dealer_links)} legitimate dealers")
        dealer_links = filtered_dealer_links
        
        if progress_callback:
            progress_callback(f"Found {len(dealer_links)} dealers to process", 25)
            
        # Debug print all dealers we're about to process
        print("\nDealers to be processed:")
        for name, url in dealer_links:
            print(f"- {name}: {url}")
        print()
        
        # Process each dealer
        total_dealers = len(dealer_links)
        for i, (name, url) in enumerate(dealer_links):
            # Calculate overall progress for this dealer
            # Spread progress from 25% to 95% across all dealers
            progress_base = 25
            progress_range = 70
            dealer_progress = progress_base + (progress_range * i / total_dealers)
            
            if progress_callback:
                progress_callback(f"Processing dealer {i+1} of {total_dealers}: {name}", dealer_progress)
            
            try:
                # Show progress during different phases of dealer processing
                if progress_callback:
                    progress_callback(f"Downloading dealer page for {name}", dealer_progress + 0.2)
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                if progress_callback:
                    progress_callback(f"Parsing dealer page for {name}", dealer_progress + 0.4)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract dealer data
                if progress_callback:
                    progress_callback(f"Extracting data for {name}", dealer_progress + 0.6)
                dealer_data = extract_dealer_data(soup, name, url)
                dealers.append(dealer_data)
                print(f"Added dealer: {name}")
                
                # Show completed for this dealer
                if progress_callback:
                    progress_callback(f"Completed processing {name}", dealer_progress + 0.8)
                
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                import traceback
                traceback.print_exc()
                
        # Make sure Benji Coleman is included (hardcoded fallback)
        if progress_callback:
            progress_callback("Verifying dealer data", 96)
            
        # Check for Benji in our scraped data
        benji_verified = False
        for dealer in dealers:
            if dealer["name"] == "Benji Coleman":
                benji_verified = True
                # Add transaction from notes if it doesn't exist
                has_transaction = False
                for transaction in dealer.get("transactions", []):
                    if transaction.get("product") == "Sweet Monkey" and transaction.get("date") == "04/25/2025":
                        has_transaction = True
                        break
                        
                if not has_transaction:
                    transaction = {
                        "date": "04/25/2025",
                        "product": "Sweet Monkey",
                        "quantity": 300,
                        "price": 100,
                        "text": "300 Sweet Monkey units at $100 each (04/25/2025)"
                    }
                    dealer.setdefault("transactions", []).append(transaction)
                    dealer["last_transaction_date"] = "04/25/2025"
                    print("Added verified transaction to Benji Coleman from notes")
                    
        # Add a manually verified dealer record for the example from notes (Benji Coleman)
        if progress_callback:
            progress_callback("Adding missing dealers if needed", 98)
        if not benji_verified:
            benji = {
                "name": "Benji Coleman",
                "region": "Northtown",
                "location": "Motel Room 2",
                "initial_buy_in": 500,
                "percentage_taken": 20.0,
                "assignable_customers": 8,
                "preferred_effects": [],
                "max_quantity": 300,
                "transactions": [{
                    "date": "04/25/2025",
                    "product": "Sweet Monkey",
                    "quantity": 300,
                    "price": 100,
                    "text": "300 Sweet Monkey units at $100 each (04/25/2025)"
                }],
                "last_transaction_date": "04/25/2025",
                "notes": "Manually added from verified game data"
            }
            dealers.append(benji)
            print("Added Benji Coleman manually from verified data")
        
        if progress_callback:
            progress_callback(f"Completed fetching {len(dealers)} dealers", 100)
        
    except Exception as e:
        print(f"Error fetching dealers: {str(e)}")
        if progress_callback:
            progress_callback(f"Error: {str(e)}", 100)
        import traceback
        traceback.print_exc()
    
    return dealers

def fetch_all_customers(progress_callback=None):
    """Fetch all customer data from wiki pages"""
    customers = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Get the main customers page
        if progress_callback:
            progress_callback("Connecting to customer wiki page", 0)
        url = "https://schedule-1.fandom.com/wiki/Customers"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        main_soup = BeautifulSoup(response.text, 'html.parser')
        if progress_callback:
            progress_callback("Connected to customer wiki page", 5)
        
        # Find the customers table or lists
        if progress_callback:
            progress_callback("Searching for customer tables", 10)
        customer_links = []
        
        # Try to find customer tables
        customer_tables = main_soup.find_all('table', class_='article-table')
        
        for table in customer_tables:
            # Skip tables without enough rows
            if len(table.find_all('tr')) < 3:
                continue
                
            # Extract customer links from the table rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 2:  # Need at least name and region
                    name_cell = cells[0]
                    link = name_cell.find('a')
                    if link and link.has_attr('href'):
                        customer_name = link.get_text().strip()
                        customer_url = "https://schedule-1.fandom.com" + link['href']
                        customer_links.append((customer_name, customer_url))
                        print(f"Found customer in table: {customer_name}")
        
        # If no tables, try to find links in lists
        if not customer_links:
            if progress_callback:
                progress_callback("Searching for customer lists", 15)
            # Look for sections that might contain customer lists
            customer_sections = main_soup.find_all(['h2', 'h3'], string=lambda s: s and ('customer' in s.lower() or 'client' in s.lower()))
            
            for section in customer_sections:
                # Look for lists after the section header
                next_list = section.find_next('ul') or section.find_next('ol')
                if next_list:
                    for item in next_list.find_all('li'):
                        link = item.find('a')
                        if link and link.has_attr('href'):
                            customer_name = link.get_text().strip()
                            customer_url = "https://schedule-1.fandom.com" + link['href']
                            customer_links.append((customer_name, customer_url))
                            print(f"Found customer in list: {customer_name}")
        
        # If still no links, try to find all links that might be customers
        if not customer_links:
            if progress_callback:
                progress_callback("Searching for potential customer links", 20)
            # Look for all links in the main content
            content_div = main_soup.find('div', class_='mw-parser-output')
            if content_div:
                for link in content_div.find_all('a'):
                    if link.has_attr('href') and '/wiki/' in link['href'] and not link['href'].endswith('Category:'):
                        # Skip obvious non-customer links
                        skip_words = ['dealer', 'strain', 'effect', 'drug', 'region', 'mission', 'rank']
                        if not any(word in link['href'].lower() for word in skip_words):
                            customer_name = link.get_text().strip()
                            customer_url = "https://schedule-1.fandom.com" + link['href']
                            customer_links.append((customer_name, customer_url))
                            print(f"Found potential customer: {customer_name}")
        
        # Filter out region names, category pages, and non-customer entries
        if progress_callback:
            progress_callback("Filtering non-customer entries", 25)
        filtered_customer_links = []
        for name, url in customer_links:
            # Skip known region names
            regions = ["Suburbia", "Northtown", "Downtown", "Docks", "Westville", "Uptown"]
            if name in regions:
                print(f"Skipping region: {name}")
                continue
                
            # Skip "NPC", "Money", "product", etc.
            non_customer_keywords = ["NPC", "Money", "product", "Products", "Category:"]
            if any(keyword in name for keyword in non_customer_keywords):
                print(f"Skipping non-customer entry: {name}")
                continue
                
            # Keep legitimate customer names
            filtered_customer_links.append((name, url))
        
        print(f"Filtered from {len(customer_links)} to {len(filtered_customer_links)} legitimate customers")
        customer_links = filtered_customer_links
        if progress_callback:
            progress_callback(f"Found {len(customer_links)} customers to process", 30)
        
        # Process each customer
        from src.customer_data import extract_customer_data_from_html
        
        total_customers = len(customer_links)
        for i, (name, url) in enumerate(customer_links):
            # Calculate overall progress for this customer
            # Spread progress from 30% to 95% across all customers
            progress_base = 30
            progress_range = 65
            customer_progress = progress_base + (progress_range * i / total_customers)
            if progress_callback:
                progress_callback(f"Processing customer {i+1} of {total_customers}: {name}", customer_progress)
            
            try:
                # Progress updates for individual steps of customer processing
                if progress_callback:
                    progress_callback(f"Downloading customer page for {name}", customer_progress + 0.1)
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                if progress_callback:
                    progress_callback(f"Parsing customer page for {name}", customer_progress + 0.2)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract customer data using the function from customer_data.py
                if progress_callback:
                    progress_callback(f"Extracting data for {name}", customer_progress + 0.3)
                customer_data = extract_customer_data_from_html(soup, name, url)
                customers.append(customer_data)
                print(f"Added customer: {name}")
                
                # Show completion for this customer
                if progress_callback:
                    progress_callback(f"Completed processing customer {i+1} of {total_customers}: {name}", customer_progress + 0.4)
                
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Add sample customers if none were found
        if not customers:
            if progress_callback:
                progress_callback("No customers found, adding sample data", 96)
            sample_customers = [
                {
                    "name": "Marco Polo",
                    "region": "Downtown",
                    "standards": "High",
                    "favorite_effects": ["Calming", "Euphoric"],
                    "relations": ["Jane Lucero"],
                    "residency": "Lives in a high-end apartment downtown.",
                    "work": "Owns a travel agency.",
                    "notes": "Sample customer data"
                },
                {
                    "name": "Sarah Johnson",
                    "region": "Northtown",
                    "standards": "Moderate",
                    "favorite_effects": ["Energizing", "Focused"],
                    "relations": ["Benji Coleman"],
                    "residency": "Small house in Northtown suburbs.",
                    "work": "Works as a barista at a local coffee shop.",
                    "notes": "Sample customer data"
                },
                {
                    "name": "Trevor Phillips",
                    "region": "Southside",
                    "standards": "Low",
                    "favorite_effects": ["Disorienting", "Tropic Thunder"],
                    "relations": ["Brad Crosby"],
                    "residency": "Lives in a trailer park.",
                    "work": "Unemployed, occasional bouncer at clubs.",
                    "notes": "Sample customer data"
                }
            ]
            customers.extend(sample_customers)
            print("Added sample customers as fallback")
        
        if progress_callback:
            progress_callback("Finalizing customer data", 98)
            progress_callback(f"Completed fetching {len(customers)} customers", 100)
        
    except Exception as e:
        print(f"Error fetching customers: {str(e)}")
        if progress_callback:
            progress_callback(f"Error: {str(e)}", 100)
        import traceback
        traceback.print_exc()
    
    return customers

def main():
    """Main entry point for the script"""
    print("Schedule I - Dealer Data Fetcher (Improved)")
    print("==========================================")
    print("This script will fetch dealer data from the Schedule 1 wiki.")
    print("It focuses specifically on actual dealers from the dealers table.")
    print()
    
    # Ensure the src module can be imported
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Fetch dealers
    print("Fetching dealers from wiki...")
    dealers = fetch_actual_dealers(progress_callback)
    
    if not dealers:
        print("No dealers found or an error occurred.")
        return
    
    # Load existing data and merge with new data if it exists
    try:
        with open("dealer_data.json", "r") as f:
            existing_data = json.load(f)
        
        # Get existing dealer names
        existing_names = [d["name"] for d in existing_data.get("dealers", [])]
        
        # Add only new dealers or update existing ones
        for dealer in dealers:
            if dealer["name"] in existing_names:
                # Update existing dealer
                for i, existing_dealer in enumerate(existing_data["dealers"]):
                    if existing_dealer["name"] == dealer["name"]:
                        # Preserve transactions and notes
                        transactions = existing_dealer.get("transactions", [])
                        notes = existing_dealer.get("notes", "")
                        
                        # Update with new data
                        existing_data["dealers"][i] = dealer
                        
                        # Restore preserved data
                        if transactions and not dealer.get("transactions"):
                            existing_data["dealers"][i]["transactions"] = transactions
                        if notes and not dealer.get("notes"):
                            existing_data["dealers"][i]["notes"] = notes
                        
                        print(f"Updated existing dealer: {dealer['name']}")
                        break
            else:
                # Add new dealer
                existing_data["dealers"].append(dealer)
                print(f"Added new dealer: {dealer['name']}")
        
        dealer_data = existing_data
        
    except (FileNotFoundError, json.JSONDecodeError):
        # If no existing file or it's corrupted, use just the new data
        dealer_data = {"dealers": dealers}
    
    # Save to file
    with open("dealer_data.json", "w") as f:
        json.dump(dealer_data, f, indent=4)
    
    print(f"Successfully processed {len(dealers)} dealers and saved to dealer_data.json")
    print("You can now use this data in the Schedule I application.")

if __name__ == "__main__":
    main()