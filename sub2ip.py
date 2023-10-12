import argparse
import socket
import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import tldextract

# Set the maximum number of threads for DNS resolution
MAX_THREADS = 50
MIN_THREADS = 1

# Set the batch size for processing subdomains
BATCH_SIZE = 100  # You can adjust this as needed

# Set the progress update interval
PROGRESS_INTERVAL = 100

@lru_cache(maxsize=None)  # Cache DNS results
def resolve_dns(subdomain):
    try:
        ip_list = socket.gethostbyname_ex(subdomain)[-1]
        return ', '.join(ip_list)
    except (socket.gaierror, socket.herror):
        return "Could not resolve. May be stale data."
    except UnicodeError:
        return "UnicodeError: label empty or too long"

def process_batch(subdomains, output_file, scope_file, num_threads, total_subdomains, start_time):
    results = set()
    scope_results = set()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for subdomain in subdomains:
            ips = resolve_dns(subdomain)
            results.add((subdomain, ips))

            if is_in_scope(ips, scope_file):
                scope_results.add((subdomain, ips))

            if len(results) % PROGRESS_INTERVAL == 0:
                elapsed_time = time.time() - start_time
                processed_subdomains = len(results)
                remaining_subdomains = total_subdomains - processed_subdomains
                estimated_time = (elapsed_time / processed_subdomains) * remaining_subdomains

                print(f"Processed {processed_subdomains}/{total_subdomains} subdomains. Estimated time to completion: {estimated_time:.2f} seconds")

    with open("subdomains.csv", 'a', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        for subdomain, ips in results:
            domain = tldextract.extract(subdomain).registered_domain
            csv_writer.writerow([domain, subdomain, ips])

    if scope_results:
        with open("in-scope-subdomains.csv", 'a', newline='', encoding='utf-8') as f:
            csv_writer = csv.writer(f)
            for subdomain, ips in scope_results:
                domain = tldextract.extract(subdomain).registered_domain
                csv_writer.writerow([domain, subdomain, ips])

    elapsed_time = time.time() - start_time
    processed_subdomains = len(results)
    remaining_subdomains = total_subdomains - processed_subdomains
    estimated_time = (elapsed_time / processed_subdomains) * remaining_subdomains

    print(f"Processed {processed_subdomains}/{total_subdomains} subdomains. Estimated time to completion: {estimated_time:.2f} seconds")

def is_in_scope(ips, scope_file):
    if not scope_file:
        return False  # No scope file provided

    with open(scope_file, 'r', encoding='utf-8') as f:
        allowed_ips = f.read().splitlines()

    resolved_ips = ips.split(', ')
    return any(ip in resolved_ips for ip in allowed_ips)

def resolve_subdomains(input_files, scope_file, num_threads):
    for input_file in input_files:
        with open(input_file, 'r', encoding='utf-8') as f:
            subdomains = f.read().splitlines()

        total_subdomains = len(subdomains)
        start_time = time.time()

        batches = [subdomains[i:i + BATCH_SIZE] for i in range(0, total_subdomains, BATCH_SIZE)]

        for batch in batches:
            process_batch(batch, "subdomains.csv", scope_file, num_threads, total_subdomains, start_time)

def main():
    parser = argparse.ArgumentParser(description="Resolve subdomains to IP addresses and save results to CSV files.")
    parser.add_argument("-i", "--input", nargs='+', required=True, help="Paths to the input files containing subdomains.")
    parser.add_argument("-s", "--scope", help="Path to the scope file containing allowed IP addresses (optional).")
    parser.add_argument("-t", "--threads", type=int, default=MAX_THREADS, 
                        help="Number of threads for DNS resolution (1-50, default 50).")

    args = parser.parse_args()
    
    # Enforce thread limit
    num_threads = max(min(args.threads, MAX_THREADS), MIN_THREADS)

    resolve_subdomains(args.input, args.scope, num_threads)
    if args.scope:
        print("\nIn-scope subdomain resolution completed. CSV files created.")
    else:
        print("\nSubdomain resolution completed. CSV files created.")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("-h")
    main()
