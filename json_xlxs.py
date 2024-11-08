import os
import json
import pandas as pd
import re
import time

# List to keep track of tickers, years, and quarters with missing statements
missing_statements_log = []

def get_income_statement(xbrl_json, year_filter, ticker, quarter):
    income_statement_store = {}
    processed_columns = {} 
    
    exact_terms = [
        # Total revenue terms
        'Revenues', 'OtherSalesRevenueNet', 'TotalRevenue', 'RevenueFromContractWithCustomerExcludingAssessedTax', 
        'SalesRevenueNet', 'SalesRevenueGoodsNet','SalesRevenueServicesNet', 'RevenueFromContractWithCustomerIncludingAssessedTax', 
        'RealEstateRevenueNet', 'RegulatedOperatingRevenueGas',
        'RefiningAndMarketingRevenue', 'RegulatedOperatingRevenue', 'RevenueFromContractWithCustomerIncludingAssessedTax', 
        'RevenueFromContractWithCustomerIncludingAssessedTaxNet', 'InterestAndDividendIncomeOperating', 'RevenueLossesFromInvestments',
        'ElectricUtilityRevenue',
        
        # COGS terms
        'CostOfGoodsSold', 'CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization', 'CostOfGoodsAndServicesSold', 'CostOfServices', 
        'CostOfPropertyRepairsAndMaintenance', 'FuelPurchasedPowerAndCostOfGasSold', 'OperatingExpenses', 
        'CostOfServicesDepreciationAndLeaseCharges', 'OtherCostAndExpenseOperating', 'CostofRevenueEarningEquipmentSold', 
        'CostOfPurchasedPower', 'OtherInterestExpense', 'TotalCostsAndExpensesIncludingNonoperatingIncomeExpense', 
        'CostOfSalesExcludingDepreciation', 'BenefitsLossesAndExpenses', 'InterestExpense', 'CostsAndExpenses',
        
        # Gross profit terms
        'GrossProfit', 'InterestIncomeExpenseAfterProvisionForLoanLoss',
        
        # Pre-tax income terms
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxes', 
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments', 
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic',
        'OperatingIncomeLoss',

        # Income after tax terms
        'IncomeLoss', 'NetIncomeLoss', 'NetIncome', 'IncomeLossFromContinuingOperations', 'NetIncomeLossAvailableToCommonStockholdersBasic', 'ProfitLoss',  
        
        # EPS basic terms
        'EarningsPerShareBasic', 'EarningsPerShareBasicAndDiluted', 'IncomeLossFromContinuingOperationsPerBasicShare', 
    ]
    
    # Define a renaming dictionary for final column names
    rename_map = {
        r'Revenues|SalesRevenueNet|RevenueFromContractWithCustomerExcludingAssessedTax|OtherSalesRevenueNet|SalesRevenueGoodsNet|SalesRevenueServicesNet|RevenueFromContractWithCustomerIncludingAssessedTax|RealEstateRevenueNet|RegulatedOperatingRevenueGas|ElectrictilityRevenue|RefiningAndMarketingRevenue|RegulatedOperatingRevenue|RevenueFromContractWithCustomerIncludingAssessedTax|RevenueFromContractWithCustomerIncludingAssessedTaxNet|InterestAndDividendIncomeOperating|RevenueLossesFromInvestments|ElectricUtilityRevenue': 'Total Revenue',
        r'CostOfGoodsSold|CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization|CostOfGoodsAndServicesSold|CostOfServices|CostOfPropertyRepairsAndMaintenance|FuelPurchasedPowerAndCostOfGasSold|OperatingExpenses|CostOfServicesDepreciationAndLeaseCharges|OtherCostAndExpenseOperating|CostofRevenueEarningEquipmentSold|CostOfPurchasedPower|OtherInterestExpense|TotalCostsAndExpensesIncludingNonoperatingIncomeExpense|CostOfSalesExcludingDepreciation|CostOfRevenue|BenefitsLossesAndExpenses|InterestExpense|CostsAndExpenses': 'COGS',
        r'GrossProfit|InterestIncomeExpenseAfterProvisionForLoanLoss': 'Gross Profit',
        r'IncomeLossFromContinuingOperationsBeforeIncomeTaxes|IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments|IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest|IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic|OperatingIncomeLoss': 'Pre Tax Income',
        r'IncomeLoss|NetIncomeLoss|IncomeLossFromContinuingOperations|NetIncome|NetIncomeLossAvailableToCommonStockholdersBasic|ProfitLoss': 'Income After Tax',
        r'EarningsPerShareBasic|EarningsPerShareBasicAndDiluted|IncomeLossFromContinuingOperationsPerBasicShare': 'Earnings Per Share (Basic)',
    }

    # Define priority order for statement keys
    priority_order = [
        'StatementOfIncomeInterestBasedRevenue',        
        'StatementsOfIncome', 
        'StatementOfIncomeAlternative', 
        'ConsolidatedStatementsOfOperationsInThousandsExceptPerShareData',
        'CondensedConsolidatedStatementsOfOperationsUnauditedInThousandsExceptPerShareData',
        'StatementCONSOLIDATEDSTATEMENTSOFOPERATIONSANDRETAINEDEARNINGS',
        "CondensedConsolidatedStatementsOfOperationsUnauditedInThousandsExceptPerShareAmounts",
        'StatementsOfComprehensiveIncome',
        'StatementsOfOperations', 
        'StatementOfIncomeRealEstateExcludingREITs',
    ]

    relevant_key = None

    #Goes through priority first against a full match
    # Search for the exact matches first, then general matches
    for pattern in priority_order:
        found_match = False  # Variable to control the outer loop continuation

        # First, try exact matches
        for key in xbrl_json.keys():
            if re.fullmatch(pattern, key, re.IGNORECASE):  # Check for exact match
                relevant_key = key
                found_match = True
                print(f"Found exact match key: {relevant_key}")
                break  # Exit the inner loop once a match is found

        # If a match is found, break out of the outer loop
        if found_match:
            break
    
    #seperate loop only if relevant key is not found
    if relevant_key is None:
        for key in xbrl_json.keys():
            if re.search(pattern, key, re.IGNORECASE):  # Fallback to partial match
                relevant_key = key
                found_match = True
                print(f"Found partial match key: {relevant_key}")
                break  # Exit the inner loop once a match is found
            
            # If no relevant key is found after searching, continue with the next pattern
            if not found_match:
                print(f"No relevant income or operations statement found for ticker {ticker}, year {year_filter}, quarter {quarter}.")
                missing_statements_log.append({
                    "ticker": ticker,
                    "year": year_filter,
                    "quarter": quarter,
                    "reason": "No relevant income or operations statement found"
                })
            # If a relevant key is found, stop searching
            if relevant_key:
                break

    # print(*list(xbrl_json), sep='\n')
    # print('\n')
    # print(f"Relevant Key: {relevant_key}")
    # print(*list(xbrl_json[relevant_key]), sep='\n')

    for usGaapItem in xbrl_json.get(relevant_key, []):
        if usGaapItem in exact_terms:
            values = []
            indicies = []

            for fact in xbrl_json[relevant_key][usGaapItem]:
                if 'segment' not in fact and isinstance(fact, dict) and 'period' in fact and isinstance(fact['period'], dict):
                    start_date = fact['period'].get('startDate', '')
                    end_date = fact['period'].get('endDate', '')

                    # Adjust the year filtering logic to check against the end date
                    end_year = end_date[:4]  # Extract year from the end date
                    start_year = start_date[:4]

                    # Prioritize selecting values spanning the full year if available (for Q4)
                    if quarter == "Q4":
                        # If the period spans the whole year (e.g., startDate = "YYYY-01-01", endDate = "YYYY-12-31")
                        if start_date == f"{year_filter}-01-01" and end_date == f"{year_filter}-12-31":
                            index = start_date + '-' + end_date
                            if fact.get('value') is not None:
                                values.append(float(fact['value']))  # Ensure values are numeric
                                indicies.append(index)
                            break  # Since we found the full-year data, we can stop looking further for Q4
                        else:
                            # For other entries in Q4, collect them normally
                            if end_year == year_filter or int(end_year) == int(year_filter) - 1:
                                index = start_date + '-' + end_date
                                if fact.get('value') is not None:
                                    values.append(float(fact['value']))  # Ensure values are numeric
                                    indicies.append(index)
                    else:
                        # Non-Q4 logic (collect normal entries for matching year)
                        if end_year == year_filter:
                            index = start_date + '-' + end_date
                            if fact.get('value') is not None:
                                values.append(float(fact['value']))  # Ensure values are numeric
                                indicies.append(index)

            # Handling Total Revenue and COGS separately
            if usGaapItem in [
                'Revenues', 'OtherSalesRevenueNet', 'TotalRevenue', 'RevenueFromContractWithCustomerExcludingAssessedTax', 
                'SalesRevenueNet', 'SalesRevenueGoodsNet','SalesRevenueServicesNet', 'RevenueFromContractWithCustomerIncludingAssessedTax', 
                'RealEstateRevenueNet', 'RegulatedOperatingRevenueGas', 
                'RefiningAndMarketingRevenue', 'RegulatedOperatingRevenue', 'RevenueFromContractWithCustomerIncludingAssessedTax', 
                'RevenueFromContractWithCustomerIncludingAssessedTaxNet', 'InterestAndDividendIncomeOperating', 'RevenueLossesFromInvestments',
                'ElectricUtilityRevenue',
                    ]:
                
                if values:
                    max_value = max(values)
                    income_statement_store['Total Revenue'] = pd.Series([max_value], index=[indicies[values.index(max_value)]])

            elif usGaapItem in [
                'CostOfGoodsSold', 'CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization', 'CostOfGoodsAndServicesSold', 'CostOfServices', 
                'CostOfPropertyRepairsAndMaintenance', 'FuelPurchasedPowerAndCostOfGasSold', 'OperatingExpenses', 
                'CostOfServicesDepreciationAndLeaseCharges', 'OtherCostAndExpenseOperating', 'CostofRevenueEarningEquipmentSold', 
                'CostOfPurchasedPower', 'OtherInterestExpense', 'TotalCostsAndExpensesIncludingNonoperatingIncomeExpense', 
                'CostOfSalesExcludingDepreciation', 'BenefitsLossesAndExpenses', 'CostsAndExpenses',
                    ]:
                if values:
                    max_value = max(values)
                    income_statement_store['COGS'] = pd.Series([max_value], index=[indicies[values.index(max_value)]])
        
            
            # Handling Pre Tax Income with minimum absolute value
            elif usGaapItem in [
                'IncomeLossFromContinuingOperationsBeforeIncomeTaxes', 
                'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments', 
                'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic',
                'OperatingIncomeLoss',
            ]:
                numeric_values = []  # List to store valid numeric values
                valid_indicies = []  # List to store the corresponding indices

                # Convert values to floats and filter out non-numeric values
                for i, value in enumerate(values):
                    try:
                        numeric_value = float(value)
                        numeric_values.append(numeric_value)
                        valid_indicies.append(indicies[i])
                    except ValueError:
                        print(f"Skipping non-numeric value: {value}")

                if numeric_values:
                    # Find the value with the minimum absolute value but retain its original sign
                    min_abs_value = min(numeric_values, key=lambda x: abs(x))
                    income_statement_store['Pre Tax Income'] = pd.Series([min_abs_value], index=[valid_indicies[numeric_values.index(min_abs_value)]])


            else:
                series = pd.Series(values, index=indicies).groupby(level=0).first()
                income_statement_store[usGaapItem] = series

    # Convert to DataFrame
    income_statement = pd.DataFrame.from_dict(income_statement_store, orient='columns')

    # Renaming columns
    for col in income_statement.columns:
        for pattern, new_name in rename_map.items():
            if re.search(pattern, col, re.IGNORECASE):
                income_statement.rename(columns={col: new_name}, inplace=True)
                break

    return income_statement

def process_json_file(file_path, year, ticker, quarter):
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
            income_statement = get_income_statement(data, year, ticker, quarter)
            # If the dataframe is empty, try with year_filter - 1
            if income_statement.empty:
                print(f"No data found for {year}, retrying with {int(year) - 1}")
                income_statement = get_income_statement(data, str(int(year) - 1), ticker, quarter)
            # Return the final result
            return income_statement

            
        except json.JSONDecodeError as e:
            print(f"Error reading JSON from {file_path}: {e}")
            missing_statements_log.append({
                "ticker": ticker,
                "year": year,
                "quarter": quarter,
                "reason": f"JSON Decode Error: {e}"
            })
            return pd.DataFrame()  # Return an empty DataFrame in case of an error

def process_ticker_folder(ticker_folder, ticker):
    statement_data = pd.DataFrame()

    for root, _, files in os.walk(ticker_folder):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)

                file_info = file.split("_")
                if len(file_info) >= 4:
                    year = file_info[1]
                    quarter = file_info[3].replace(".json", "")
                else:
                    year = "Unknown"
                    quarter = "Unknown"

                extracted_values = process_json_file(file_path, year, ticker, quarter)
                
                # Add ticker, year, and quarter as columns to the DataFrame
                extracted_values['ticker'] = ticker
                extracted_values['year'] = year
                extracted_values['quarter'] = quarter
                columns = ['ticker', 'year', 'quarter'] + [col for col in extracted_values.columns if col not in ['ticker', 'year', 'quarter']]
                extracted_values = extracted_values[columns]
                
                # Ensure unique index values
                extracted_values = extracted_values.loc[~extracted_values.index.duplicated(keep='first')].reset_index(drop=True)

                # Ensure no duplicate columns
                if extracted_values.columns.duplicated().any():
                    extracted_values = extracted_values.loc[:, ~extracted_values.columns.duplicated()]

                statement_data = pd.concat([statement_data, extracted_values], axis=0, ignore_index=True)
                time.sleep(0.05)

    # Check if the number of entries is less than 24 for this ticker
    num_entries = len(statement_data)
    if num_entries < 24:
        print(f"Ticker {ticker} has less than 24 entries: {num_entries}. Logging as missing or incomplete data.")
        missing_statements_log.append({
            "ticker": ticker,
            "entries_found": num_entries,
            "expected_entries": 24,
            "reason": "Incomplete data (less than 24 entries)"
        })

    return statement_data

def process_results_folder(results_folder):
    all_statements = pd.DataFrame()

    for root, dirs, _ in os.walk(results_folder):
        for ticker_folder in dirs:
            ticker_path = os.path.join(root, ticker_folder)
            print(f"Processing {ticker_folder} folder...")
            ticker_statements = process_ticker_folder(ticker_path, ticker_folder)

            # Group by 'ticker', 'year', and 'quarter' to aggregate and avoid duplicates
            ticker_statements = ticker_statements.groupby(['ticker', 'year', 'quarter'], as_index=False).first()

            all_statements = pd.concat([all_statements, ticker_statements], axis=0, ignore_index=True)
    
    desired_order = ['ticker', 'year', 'quarter', 'Total Revenue', 'COGS', 'Gross Profit', 'Pre Tax Income', 'Income After Tax', 'Earnings Per Share (Basic)']
    all_statements = all_statements.reindex(columns=desired_order)
    return all_statements

def save_statements_to_excel(output_file, all_statements):
    all_statements.to_excel(output_file, index=False)

def save_missing_statements_log(output_file):
    if missing_statements_log:
        df_missing = pd.DataFrame(missing_statements_log)
        df_missing.to_excel(output_file, index=False)
        print(f"Missing statements log saved to {output_file}")
    else:
        print("No missing statements to log.")

if __name__ == "__main__":
    results_folder = "nasdaq/results"
    all_statements = process_results_folder(results_folder)

    if not all_statements.empty:
        output_file = "statements_of_income_v5.xlsx"
        save_statements_to_excel(output_file, all_statements)
        print(f"All key-value pairs from 'StatementsOfIncome' extracted and saved to {output_file}")
    else:
        print("No data found to process.")

    missing_log_file = "missing_statements_log.xlsx"
    save_missing_statements_log(missing_log_file)
