import requests
import time
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt


def fetch_to_addresses(api_key, start_block, end_block):
    """
    Fetches a list of 'to' addresses from the API calls for a given block range.
    """
    url = "https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "address": "0xD152f549545093347A162Dce210e7293f1452150",
        "page": 1,
        "offset": 1000,
        "startblock": start_block,
        "endblock": end_block,
        "sort": "asc",
        "apikey": api_key,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json()["status"] == "1":
        results = response.json()["result"]
        return {tx["to"] for tx in results}  # Use a set to ensure uniqueness
    else:
        return set()  # Return an empty set if the call fails


def merge_address_sets(api_key):
    """
    Merges addresses from two different block ranges into a unique set.
    """
    addresses_from_first_range = fetch_to_addresses(
        api_key, 18794474, 18794474
    )  # New York Hackathon Payouts
    addresses_from_second_range = fetch_to_addresses(
        api_key, 18345055, 18345055
    )  # Istanbul Hackathon Payouts
    return addresses_from_first_range.union(addresses_from_second_range)


def fetch_transactions_for_addresses(addresses, api_key):
    """
    Fetches transactions for each address in the provided list with rate limiting.
    """
    transactions_per_address = {}
    calls_per_second = 5
    sleep_time = 1 / calls_per_second

    for address in addresses:
        transactions = make_api_call(address, api_key)
        if transactions:
            transactions_per_address[address] = transactions
        time.sleep(sleep_time)  # Rate limit our requests

    return transactions_per_address


def make_api_call(address, api_key):
    """
    Makes an API call to fetch transactions for a given address.
    """
    url = "https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 1000,
        "sort": "desc",
        "apikey": api_key,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json()["status"] == "1":
        return response.json()["result"]
    else:
        return None


def calculate_duration_months(start_timestamp, end_timestamp):
    """Calculate duration in months between two timestamps."""
    start_date = datetime.fromtimestamp(int(start_timestamp))
    end_date = datetime.fromtimestamp(int(end_timestamp))
    return (
        (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    )


def calculate_user_stats(transactions):
    """Calculate stats per user based on transactions."""
    if not transactions:
        return (
            0,
            0,
        )  # Assuming 0 transactions and 0 duration if there are no transactions

    timestamps = [int(tx["timeStamp"]) for tx in transactions]
    start_timestamp, end_timestamp = min(timestamps), max(timestamps)
    duration_months = calculate_duration_months(start_timestamp, end_timestamp)
    average_transactions = len(transactions) / duration_months if duration_months else 0
    return (
        average_transactions,
        duration_months,
    )


def calculate_global_stats(active_user_stats):
    """
    Calculate global stats based on active user stats, including min, max, average, and median.
    """
    averages = [stat[0] for stat in active_user_stats]
    min_transactions_per_month = min(averages) if averages else 0
    max_transactions_per_month = max(averages) if averages else 0
    average_transactions_per_month = np.mean(averages) if averages else 0
    median_transactions_per_month = np.median(averages) if averages else 0

    return (
        min_transactions_per_month,
        max_transactions_per_month,
        average_transactions_per_month,
        median_transactions_per_month,
    )


def remove_outliers(data):
    """
    Removes outliers from data using the interquartile range (IQR) and returns the filtered data.
    """
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    outlier_step = 1.5 * IQR

    # Filtering out users that fall outside of the lower and upper bounds
    lower_bound = Q1 - outlier_step
    upper_bound = Q3 + outlier_step

    filtered_data = [x for x in data if lower_bound < x[0] < upper_bound]

    return filtered_data


if __name__ == "__main__":
    API_KEY = "JQJC8P87GIS8GKAZPAT7P92H634I4HSXMD"

    # 1. Get all user addressed across New York and Instanbul hackathons
    to_addresses = merge_address_sets(API_KEY)
    print(f"Merged addresses (total {len(to_addresses)}):", to_addresses)

    # 2. Fetch the last 1,000 transactions for each address
    transactions_per_address = fetch_transactions_for_addresses(to_addresses, API_KEY)
    print("Fetched transactions for each address.")

    # 3. Calculate statistics for those transactions
    user_stats = [
        calculate_user_stats(transactions)
        for transactions in transactions_per_address.values()
    ]

    # 4. Filter out users with no transactions and remove outliers for active users
    active_user_stats = [stat for stat in user_stats if stat[0] > 0]
    filtered_active_user_stats = remove_outliers(active_user_stats)

    # 5. Calculate global stats without outliers
    min_global, max_global, global_average, global_median = calculate_global_stats(
        filtered_active_user_stats
    )
    print("Min Global Transactions per Month (Active Users, No Outliers):", min_global)
    print("Max Global Transactions per Month (Active Users, No Outliers):", max_global)
    print(
        "Global Average Transactions per Month (Active Users, No Outliers):",
        global_average,
    )
    print(
        "Global Median Transactions per Month (Active Users, No Outliers):",
        global_median,
    )

    # 6. Plot the distribution without outliers
    average_transactions_per_filtered_user = [
        stat[0] for stat in filtered_active_user_stats
    ]
    plt.figure(figsize=(10, 6))
    plt.hist(
        average_transactions_per_filtered_user,
        bins=30,
        color="skyblue",
        edgecolor="black",
    )
    plt.title("Distribution of Average Transactions Per Month Per User (No Outliers)")
    plt.xlabel("Average Transactions Per Month")
    plt.ylabel("Number of Users")
    plt.grid(axis="y", alpha=0.75)
    plt.show()
