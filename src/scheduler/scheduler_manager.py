import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional

# Path to the project root (two levels up from this file)
ROOT = Path(__file__).resolve().parents[2]
# Path to the main file (the entrypoint we want to run with --cron)
MAIN_SCRIPT = str(ROOT / "main.py")
# Use the current Python interpreter (important for venvs)
PY_EXE = sys.executable

# Helper function to check if the os is windows
def is_windows():
    return platform.system().lower() == "windows"

# Function to add a weekly task that runs `py main.py --cron` every <day> at <hour>:00.
def add_schedule_task(day:str, hour:int) -> bool:
    task_id = f"autoshorts_schedule_{day.lower()}_{hour}"

    # Check if the OS is windows
    if is_windows(): # Windows task scheduler flow
        win_day_map = {
            'sunday':'SUN', 'monday':'MON', 'tuesday':'TUE', 'wednesday':'WED',
            'thursday':'THU', 'friday':'FRI', 'saturday':'SAT'
        }

        time_str = f"{hour:02}:00"
        # Changes to the root of the project and executes the cron task
        tr = (
            f'cmd.exe /c "cd /d {ROOT} && '
            f'"{PY_EXE}" "{MAIN_SCRIPT}" --cron"'
        )

        # Executes the command to add the windows task scheduler 
        try:
            # schtasks command breakdown:
            # /Create -> create a new task
            # /SC WEEKLY -> repeat weekly
            # /D  -> Day of the week
            # /TN <task_id> -> unique task name
            # /TR <command> -> command to run
            # /ST <time> -> start time
            subprocess.run([
            'schtasks', '/Create',
            '/SC','WEEKLY',
            '/D', win_day_map[day.lower()],
            '/TN', task_id,
            '/TR',tr,
            '/ST', time_str,
            '/F'  # /F forces overwrite if the task already exists
            ], check=True)
            return True # On success returns true
        except subprocess.CalledProcessError:
            return False # On exception returns false
    else: # Cron flow 
        cron_day_map = {
            'sunday':'0', 'monday':'1', 'tuesday':'2', 'wednesday':'3',
            'thursday':'4', 'friday':'5', 'saturday':'6' 
        }

        # Cron entry with a unique marker (# task_id) so we can later identify/remove it
        cron_expr = f"0 {hour} * * {cron_day_map[day.lower()]} {PY_EXE} {MAIN_SCRIPT} --cron # {task_id} \n"

        # Reads existing crontab (if any)
        proc = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        existing = proc.stdout if proc.returncode == 0 else ""

        # If task already exists (marker present), don't duplicate
        if task_id in existing:
            return False

        # Append the new job to the crontab
        new_cron = (existing.strip() + "\n" if existing.strip() else "") + cron_expr
        # Executes the cron command
        try:
            subprocess.run(["crontab","-"], input=new_cron, text=True, check=True)
            return True # On success returns true
        except subprocess.CalledProcessError:
            return False # On exception returns false


# Function to remove the scheduled task created by add_schedul_task
def remove_schedule_task(day:str, hour:int) -> bool:
    task_id = f"autoshorts_schedule_{day.lower()}_{hour}"

    # Checks if the OS is windows
    if is_windows():
        # Removes the task from windows task scheduler
        try:
            subprocess.run(['schtasks','/Delete','/TN',task_id,'/F'], check=True)
            return True
        except:
            return False
    else:
        # Removes any lines containing the task_id marker
        # List the current crontabs
        proc = subprocess.run(["crontab","-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # If no cron tab to delete exist return false
        if proc.returncode != 0:
            return False

        existing = proc.stdout.splitlines()
        new_lines = [line for line in existing if task_id not in line]

        # If nothing was removed, return False
        if len(new_lines) == len(existing):
            return False

        # Write back the filtered crontab
        new_cron = "\n".join(new_lines) + "\n"

        # Executes the cron command
        try:    
            subprocess.run(["crontab", "-"], input=new_cron, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False