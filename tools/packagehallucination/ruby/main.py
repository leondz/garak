import time
import requests
from datetime import datetime, date
import backoff


@backoff.on_exception(backoff.expo,
                      (requests.exceptions.RequestException, requests.exceptions.HTTPError),
                      max_tries=5)
def get_gem_first_push_date(gem_name):
    url = f"https://rubygems.org/api/v1/versions/{gem_name}.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()  # This will raise an HTTPError for bad responses

    versions = response.json()

    # Sort versions by creation date and get the earliest one
    earliest_version = min(versions, key=lambda v: datetime.strptime(v['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ"))
    
    first_push_date = datetime.strptime(earliest_version['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").date()
    
    return first_push_date

def main():
    cutoff_date = date(2023, 3, 1)
    # Replace these with your file paths
    input_file = '/home/arjun/gems.txt'
    output_file = 'filtered_gems.txt'

    total_gems = sum(1 for _ in open(input_file, 'r'))
    processed = 0
    included = 0
    excluded = 0
    errors = 0
    start_time = time.time()

    print(f"Starting to process {total_gems} gems...")
    print(f"Cutoff date: {cutoff_date}")

    with open(input_file, 'r') as infile, open(output_file, 'a') as outfile:
        for line in infile:
            gem_name = line.strip()
            gem_name = gem_name.split(" (")[0]
            try:
                creation_date = get_gem_first_push_date(gem_name)
                
                if creation_date and creation_date <= cutoff_date:
                    outfile.write(f"{gem_name}\n")
                    outfile.flush()
                    included += 1
                    status = "Included"
                else:
                    excluded += 1
                    status = "Excluded"
            except Exception as e:
                print(f"Error processing gem '{gem_name}': {e}")
                errors += 1
                status = "Error"
                creation_date = None
            
            processed += 1
            
            if processed % 10 == 0 or processed == total_gems:
                elapsed_time = time.time() - start_time
                gems_per_second = processed / elapsed_time
                estimated_total_time = total_gems / gems_per_second
                estimated_remaining_time = estimated_total_time - elapsed_time
                
                print(f"Processed: {processed}/{total_gems} ({processed/total_gems*100:.2f}%)")
                print(f"Current gem: {gem_name}")
                print(f"Creation date: {creation_date}")
                print(f"Status: {status}")
                print(f"Included: {included}, Excluded: {excluded}, Errors: {errors}")
                print(f"Elapsed time: {elapsed_time:.2f} seconds")
                print(f"Estimated remaining time: {estimated_remaining_time:.2f} seconds")
                print(f"Processing speed: {gems_per_second:.2f} gems/second")
                print("-" * 50)

    print(f"Filtering complete. Results saved in {output_file}")
    print(f"Total gems processed: {processed}")
    print(f"Gems included: {included}")
    print(f"Gems excluded: {excluded}")
    print(f"Gems with errors: {errors}")
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
