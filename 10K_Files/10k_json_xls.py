import pandas as pd
import json
import re

def clean_text(text):
    # Replace HTML entities with appropriate characters
    clean_text = re.sub(r'&#160;|&nbsp;', ' ', text)
    clean_text = re.sub(r'&#8220;', '"', clean_text)
    clean_text = re.sub(r'&#8221;', '"', clean_text)
    clean_text = re.sub(r'&#8217;', "'", clean_text)
    clean_text = re.sub(r'&#38;', '&', clean_text)
    clean_text = re.sub(r'&#32;', ' ', clean_text)  # Remove non-breaking spaces
    clean_text = re.sub(r'&#174;', '', clean_text)  # Remove registered trademark symbol
    
    # Remove newline characters and excessive whitespace
    clean_text = re.sub(r'\\n', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)

    # Remove table markers and other unwanted tags
    clean_text = re.sub(r'##TABLE_START.*?##TABLE_END', '', clean_text)
    
    # Remove any remaining backslashes
    clean_text = clean_text.replace('\\', '')
    
    return clean_text

# Load the ticker DataFrame
ticker_df = pd.read_csv("10k_finder/gd_tickers.csv")

# Load JSON data from a file
with open('10k_finder/data/russel_10k_extracted.json', 'r') as f:
    data = json.load(f)

# Define the batch size
batch_size = 50  # Adjust this size as needed
batch_number = 1

# Process the data in batches
for i in range(0, len(data), batch_size):
    print(f"Processing batch {batch_number}...")

    # Extract the current batch
    batch = data[i:i + batch_size]
    print(f"Batch {batch_number} contains {len(batch)} entries.")

    # Initialize a list to store rows for the current batch
    rows = []

    # Loop through each entry in the batch
    for entry in batch:
        if entry.get("ticker") in ticker_df['Ticker'].values:
            
            print(f"processing {entry.get('ticker')}")

            rows.append({
                "ticker": entry.get("ticker"),
                "companyName": entry.get("companyName"),
                "cik": entry.get("cik"),
                "formType": entry.get("formType"),
                "year": entry.get("year"),
                "filedAt": entry.get("filedAt"),
                "filingUrl": entry.get("filingUrl"),
                "FLS": clean_text(entry.get("FLS")),
                "item7": clean_text(entry.get("item7")),
            })
        else:
            continue

    # Convert the list of rows into a pandas DataFrame
    df = pd.DataFrame(rows)

    # Save the DataFrame to an Excel file (append mode)
    with pd.ExcelWriter('10k_finder/data/russel_10k_extracted.xlsx', mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, index=False, header=writer.sheets.get('Sheet1') is None, startrow=writer.sheets['Sheet1'].max_row if 'Sheet1' in writer.sheets else 0)

    print(f"Batch {batch_number} written to Excel successfully.\n")
    batch_number += 1

print("Data has been successfully written to 'russel_10k_extracted.xlsx'")
