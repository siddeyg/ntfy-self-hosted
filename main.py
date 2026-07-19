import json
import importlib
import sys
import os
import argparse

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run website scrapers for ntfy alerts.")
    parser.add_argument('--site', type=str, help='Specific site module to run (e.g., the_decoder). If omitted, runs all enabled sites sequentially.')
    args = parser.parse_args()

    config = load_config()
    sites = config.get('sites', [])
    
    if not sites:
        print("No sites configured in config.json")
        return
        
    for site_config in sites:
        if not site_config.get('enabled', False):
            print(f"Skipping {site_config.get('name')} (disabled)")
            continue
            
        module_name = site_config.get('module')
        
        if args.site and module_name != args.site:
            continue
            
        try:
            # Dynamically import the module from the scrapers folder
            module = importlib.import_module(f"scrapers.{module_name}")
            # Instantiate the Scraper class expected in the module
            scraper = module.Scraper(config, site_config)
            # Run it
            scraper.run()
        except Exception as e:
            print(f"Failed to load or run scraper for {site_config.get('name')}: {e}")

if __name__ == "__main__":
    main()
