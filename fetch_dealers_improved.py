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

def progress_callback(message, percentage):
    """Display progress as the script runs"""
    sys.stdout.write(f"\r{message} - {percentage:.1f}%")
    sys.stdout.flush()
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

def fetch_actual_dealers():
    """Fetch dealer data focusing only on actual dealers from the dealers table"""
    dealers = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Get the main dealers page
        url = "https://schedule-1.fandom.com/wiki/Dealers"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        main_soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the dealers table
        dealer_tables = main_soup.find_all('table', class_='article-table')
        
        dealer_links = []
        
        for table in dealer_tables:
            # Skip tables without enough rows (likely not the dealer table)
            if len(table.find_all('tr')) < 3:
                continue
                
            # Extract dealer links from the table rows
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 2:  # Need at least name and region
                    name_cell = cells[0]
                    link = name_cell.find('a')
                    if link and link.has_attr('href'):
                        dealer_name = link.get_text().strip()
                        dealer_url = "https://schedule-1.fandom.com" + link['href']
                        dealer_links.append((dealer_name, dealer_url))
                        print(f"Found dealer in table: {dealer_name}")
        
        if not dealer_links:
            # If we couldn't find links in tables, try to find them in the text
            dealer_section = main_soup.find(lambda tag: tag.name == 'h2' and 'dealer' in tag.get_text().lower())
            if dealer_section:
                next_ul = dealer_section.find_next('ul')
                if next_ul:
                    for li in next_ul.find_all('li'):
                        link = li.find('a')
                        if link and link.has_attr('href'):
                            dealer_name = link.get_text().strip()
                            dealer_url = "https://schedule-1.fandom.com" + link['href']
                            dealer_links.append((dealer_name, dealer_url))
                            print(f"Found dealer in list: {dealer_name}")
        
        # Process each dealer
        total_dealers = len(dealer_links)
        for i, (name, url) in enumerate(dealer_links):
            progress = (i / total_dealers) * 100
            progress_callback(f"Processing {i+1} of {total_dealers}: {name}", progress)
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract dealer data
                dealer_data = extract_dealer_data(soup, name, url)
                dealers.append(dealer_data)
                print(f"Added dealer: {name}")
                
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Add a manually verified dealer record for the example from notes (Benji Coleman)
        benji_verified = False
        for dealer in dealers:
            if dealer["name"] == "Benji Coleman":
                benji_verified = True
                # Add transaction from notes
                transaction = {
                    "date": "04/25/2025",
                    "product": "Sweet Monkey",
                    "quantity": 300,
                    "price": 100,
                    "text": "300 Sweet Monkey units at $100 each (04/25/2025)"
                }
                dealer["transactions"].append(transaction)
                dealer["last_transaction_date"] = "04/25/2025"
                print("Added verified transaction to Benji Coleman from notes")
        
        if not benji_verified and not any(d["name"] == "Benji Coleman" for d in dealers):
            # Add Benji manually if he wasn't scraped
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
        
        progress_callback(f"Completed fetching {len(dealers)} dealers", 100)
        
    except Exception as e:
        print(f"Error fetching dealers: {str(e)}")
        progress_callback(f"Error: {str(e)}", 100)
        import traceback
        traceback.print_exc()
    
    return dealers

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
    dealers = fetch_actual_dealers()
    
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