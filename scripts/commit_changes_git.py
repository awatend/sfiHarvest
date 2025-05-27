import os
import subprocess
import datetime
import time
import shutil

def copy_files(source_dir, target_dir):
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")
    
    os.makedirs(target_dir, exist_ok=True)
    
    for filename in os.listdir(source_dir):
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        
        if os.path.isfile(source_path):
            shutil.copy2(source_path, target_path)  # preserves metadata
            print(f"Copied: {filename}")
        else:
            print(f"Skipped (not a file): {filename}")

def push_data(repo_path):
	# Switch to the Git repo directory
	os.chdir(repo_path)

	# Step 2: Git add
	subprocess.run(["git", "add", "."], check=True)

	# Step 3: Git commit
	commit_message = f"Automated commit at {datetime.datetime.now().isoformat()}"
	subprocess.run(["git", "commit", "-m", commit_message], check=True)

	# Step 4: Git push
	subprocess.run(["git", "push", "origin", "main"], check=True)  # or your branch name


if __name__=='__main__':
	# Path to cloned GitHub repo
	repo_path = "/home/awa/sfiHarvest/sfiHarvest/"
	source="/home/awa/sfiHarvest/data_sniffing/gis_data/display"
	another_source="/home/awa/sfiHarvest/data_sniffing/gis_data/display/sinmod_models"
	target="/home/awa/sfiHarvest/sfiHarvest/"
	

	while True:
		copy_files(source,target)
		copy_files(another_source,target)
		push_data(repo_path)
		time.sleep(200)