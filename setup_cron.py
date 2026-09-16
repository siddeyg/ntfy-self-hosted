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

    cron_lines = []
    
    for idx, site in enumerate(sites):
        module = site['module']
        custom_cron = site.get('cron_schedule')
        
        if custom_cron:
            cron_lines.append(f"{custom_cron} cd {repo_dir} && {venv_dir}/bin/python main.py --site {module} >> combined.log 2>&1")
        else:
            total_offset = 10 + (idx * 10)
            hour_shift = total_offset // 60
            minute = total_offset % 60
            
            start_hour = 8 + hour_shift
            end_hour = 20 + hour_shift
            
            hour_str = f"{start_hour}-{end_hour}/2"
            
            cron_lines.append(f"{minute} {hour_str} * * * cd {repo_dir} && {venv_dir}/bin/python main.py --site {module} >> combined.log 2>&1")

    # Read current crontab
    try:
        current_cron = subprocess.check_output(['crontab', '-l']).decode('utf-8')
    except subprocess.CalledProcessError:
        current_cron = ""

    # Filter out old ntfy-self-hosted jobs
    new_cron = []
    for line in current_cron.splitlines():
        if "ntfy-self-hosted" in line and "main.py" in line:
            continue
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
