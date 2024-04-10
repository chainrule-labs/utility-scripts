from typing import List, Mapping, Tuple
import time
from datetime import datetime
from enum import Enum

import requests
import numpy as np
import matplotlib.pyplot as plt


class Chains(str, Enum):
    ETHEREUM = "ethereum"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    POLYGON = "polygon"
    BINANCE = "binance"
    FANTOM = "fantom"
    GNOSIS = "gnosis"


CHAINS = {
    Chains.ETHEREUM: {
        "url": "https://api.etherscan.io/api",
        "api_key": "JQJC8P87GIS8GKAZPAT7P92H634I4HSXMD",
    },
    Chains.ARBITRUM: {
        "url": "https://api.arbiscan.io/api",
        "api_key": "725U35Z6SEB2WBGXFQHKQUXMU99FNE2UBZ",
    },
    Chains.OPTIMISM: {
        "url": "https://api-optimistic.etherscan.io/api",
        "api_key": "9UCF9F87E86NQHRTX2XMQR8Q9I3Q7VTNVA",
    },
    Chains.BASE: {
        "url": "https://api.basescan.org/api",
        "api_key": "QB3F41XXCNDNGPV68H7HS9I7UGQHP89G72",
    },
    Chains.POLYGON: {
        "url": "https://api.polygonscan.com/api",
        "api_key": "4QU12K8MVP7BHNQ4UHIRQH773VXNKRIR1G",
    },
    Chains.BINANCE: {
        "url": "https://api.bscscan.com/api",
        "api_key": "MHA537WM3DSQTBC6IR1GBHU1J7U1EXU1GQ",
    },
    Chains.FANTOM: {
        "url": "https://api.ftmscan.com/api",
        "api_key": "N2K2SKMSJXGWXBW67T4BWWI1IH1N6KPD5U",
    },
    Chains.GNOSIS: {
        "url": "https://api.gnosisscan.io/api",
        "api_key": "86K19VEPZA6SCZXFC9W13W5ANYDFFQZ728",
    },
}


def fetch_to_addresses(start_block: int, end_block: int) -> set[str]:
    """
    Fetches a list of 'to' addresses on Ethereum from the API calls for a given block range.
    """

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
        "apikey": CHAINS[Chains.ETHEREUM]["api_key"],
    }
    response = requests.get(CHAINS[Chains.ETHEREUM]["url"], params=params)
    if response.status_code == 200 and response.json()["status"] == "1":
        results = response.json()["result"]
        return {tx["to"] for tx in results}


def merge_address_sets() -> set[str]:
    """
    Merges addresses from different block ranges into a unique set.
    """
    # Fetch addresses for each block range

    new_york_2022_addresses = fetch_to_addresses(15200849, 15200849)
    sf_2022_addresses = fetch_to_addresses(16016081, 16016081)
    waterloo_addresses = fetch_to_addresses(17770857, 17770857)
    newyork_2023_addresses = fetch_to_addresses(18794474, 18794474)
    november13_2023_addresses = fetch_to_addresses(18561031, 18561031)
    istanbul_addresses = fetch_to_addresses(18345055, 18345055)
    march20_2024_addresses = fetch_to_addresses(19473113, 19473113)

    # Use set.union to merge all sets together
    merged_addresses = set.union(
        new_york_2022_addresses,
        sf_2022_addresses,
        waterloo_addresses,
        newyork_2023_addresses,
        istanbul_addresses,
        march20_2024_addresses,
        november13_2023_addresses,
    )

    return merged_addresses


def fetch_transactions_for_addresses(
    addresses: set[str], chain: Chains
) -> Mapping[str, List[Mapping[str, str]]]:
    """
    Fetches transactions for each address in the provided list with rate limiting.
    """
    transactions_per_address = {}
    calls_per_second = 5
    sleep_time = 1 / calls_per_second

    for address in addresses:
        transactions = make_api_call(address, chain)
        if transactions:
            transactions_per_address[address] = transactions
        # Rate limit requests
        time.sleep(sleep_time)

    return transactions_per_address


def make_api_call(address: str, chain: Chains) -> List[Mapping[str, str]]:
    """
    Makes an API call to fetch transactions for a given address on the provided chain.
    """

    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 1000,
        "sort": "desc",
        "apikey": CHAINS[chain]["api_key"],
    }
    response = requests.get(CHAINS[chain]["url"], params=params)
    if response.status_code == 200 and response.json()["status"] == "1":
        return response.json()["result"]


def calculate_duration_months(start_timestamp: str, end_timestamp: str) -> int:
    """Calculate duration in months between two timestamps."""
    start_date = datetime.fromtimestamp(int(start_timestamp))
    end_date = datetime.fromtimestamp(int(end_timestamp))
    return (
        (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    )


def calculate_user_stats(transactions: List[Mapping[str, str]]) -> Tuple[int, int]:
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


def calculate_global_stats(
    active_user_stats: List[Tuple[int, int]]
) -> Tuple[int, int, float, float]:
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


def remove_outliers(data: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
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

    return [x for x in data if lower_bound < x[0] < upper_bound]


if __name__ == "__main__":
    # 1. Get all user addressed across New York and Instanbul hackathons
    to_addresses = merge_address_sets()
    print(f"Merged addresses (total {len(to_addresses)}):", to_addresses)

    # 2. Fetch the last 1,000 transactions for each address on the provided chain
    transactions_per_address = fetch_transactions_for_addresses(
        to_addresses, Chains.GNOSIS
    )
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
    print("Number of accounts analyzed:", len(filtered_active_user_stats))
    print("Min Global Transactions per Month:", min_global)
    print("Max Global Transactions per Month:", max_global)
    print(
        "Global Average Transactions per Month:",
        global_average,
    )
    print(
        "Global Median Transactions per Month:",
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
    plt.title("Distribution of Average Transactions Per Month Per User (Gnosis)")
    plt.xlabel("Average Transactions Per Month")
    plt.ylabel("Number of Users")
    plt.grid(axis="y", alpha=0.75)
    plt.show()
