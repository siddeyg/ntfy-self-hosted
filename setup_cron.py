import json
import os
import subprocess
import sys

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        sys.exit(1)

def main():
    repo_dir = "/home/cy/ntfy-self-hosted"
    venv_dir = os.path.join(repo_dir, "venv")
    
    config = load_config()
    sites = [s for s in config.get('sites', []) if s.get('enabled', False)]
    
    if not sites:
        print("No enabled sites found in config.json to schedule.")
        return

    # Base hours: 07, 12, 18
    # We will offset each site by 10 minutes from the base time
    
    cron_lines = []
    
    for idx, site in enumerate(sites):
        offset = idx * 10
        if offset >= 60:
            print(f"Warning: Too many sites! Offset {offset}m exceeds an hour.")
            # Advanced handling could wrap to the next hour, but let's keep it simple for now
            offset = offset % 60
            
        module = site['module']
        
        # Schedule for ~07:00
        cron_lines.append(f"{offset} 7 * * * cd {repo_dir} && {venv_dir}/bin/python main.py --site {module} >> combined.log 2>&1")
        # Schedule for ~12:30
        cron_lines.append(f"{30 + (offset % 30) if 30 + (offset % 30) < 60 else offset % 30} 12 * * * cd {repo_dir} && {venv_dir}/bin/python main.py --site {module} >> combined.log 2>&1")
        # Schedule for ~18:30
        cron_lines.append(f"{30 + (offset % 30) if 30 + (offset % 30) < 60 else offset % 30} 18 * * * cd {repo_dir} && {venv_dir}/bin/python main.py --site {module} >> combined.log 2>&1")

    # Read current crontab
    try:
        current_cron = subprocess.check_output(['crontab', '-l']).decode('utf-8')
    except subprocess.CalledProcessError:
        current_cron = ""

    # Filter out old ntfy-self-hosted jobs
    new_cron = []
    for line in current_cron.splitlines():
        if "ntfy-self-hosted/main.py" not in line:
            new_cron.append(line)
            
    # Add new jobs
    new_cron.extend(cron_lines)
    new_cron.append("") # Ensure trailing newline
    
    # Write to temporary file and install
    cron_file = "mycron_temp"
    with open(cron_file, 'w') as f:
        f.write("\n".join(new_cron))
        
    subprocess.run(['crontab', cron_file])
    os.remove(cron_file)
    
    print("Successfully updated cron jobs with 10-minute offsets!")
    for line in cron_lines:
        print(f"Added: {line}")

if __name__ == "__main__":
    main()
