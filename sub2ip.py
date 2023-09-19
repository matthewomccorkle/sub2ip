import argparse
import socket
import csv
import sys
import time

def resolve_subdomains(input_file, output_file):
    results = []

    with open(input_file, 'r', encoding='utf-8') as f:
        subdomains = f.read().splitlines()

    total_subdomains = len(subdomains)
    start_time = time.time()

    for idx, subdomain in enumerate(subdomains, 1):
        ips = []
        if not subdomain:
            ips = "Empty subdomain"
        else:
            try:
                ip_list = socket.gethostbyname_ex(subdomain)[-1]
                ips = ', '.join(ip_list)
            except (socket.gaierror, socket.herror):
                ips = "Could not resolve. May be stale data."
            except UnicodeError:
                ips = "UnicodeError: label empty or too long"

        results.append([subdomain, ips])

        elapsed_time = time.time() - start_time
        estimated_time = (elapsed_time / idx) * (total_subdomains - idx)
        progress = f"Processed {idx}/{total_subdomains} subdomains. Estimated time to completion: {estimated_time:.2f} seconds"
        sys.stdout.write("\r" + progress)
        sys.stdout.flush()

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Subdomain', 'IPs'])
        writer.writerows(results)

def main():
    parser = argparse.ArgumentParser(description="Resolve subdomains to IP addresses and save results to a CSV file.")
    parser.add_argument("-i", "--input_file", required=True, help="Path to the input file containing subdomains.")
    parser.add_argument("-o", "--output_file", default="subdomains.csv", help="Path to the output CSV file. Default is 'subdomains.csv'.")

    args = parser.parse_args()

    resolve_subdomains(args.input_file, args.output_file)
    print("\nSubdomain resolution completed. CSV file created.")

if __name__ == "__main__":
    # Use parse_args() without arguments to handle incorrect flags and help menu display
    if len(sys.argv) == 1:
        sys.argv.append("-h")
    main()
