import multiprocessing
import ETS2LA.frontend.immediate as immediate
from ETS2LA.plugins.runner import PluginRunner
import threading
import time
import json
import requests

global commits_save
commits_save = []

class PluginRunnerController():
    def __init__(self, pluginName):
        # Initialize the plugin runner
        global runners
        runners[pluginName] = self # So that we can access this runner later from the main thread or other runners.
        self.pluginName = pluginName
        # Make the queue (comms) and start the process.
        self.queue = multiprocessing.JoinableQueue()
        self.functionQueue = multiprocessing.JoinableQueue()
        self.runner = multiprocessing.Process(target=PluginRunner, args=(pluginName, self.queue, self.functionQueue, ), daemon=True)
        self.runner.start()
        self.run()
        
    def run(self):
        global frameTimes
        while True:
            try: data = self.queue.get(timeout=0.5) # Get the data returned from the plugin runner.
            except Exception as e: 
                time.sleep(0.00001)
                continue
            
            if type(data) == type(None): # If the data is None, then we just skip this iteration.
                time.sleep(0.00001)
                continue
            
            if "function" in data:
                # Send the data back to wait for the answer.
                self.queue.put(self.lastData)
                time.sleep(0.01)
                continue
            
            if type(data) != dict: # If the data is not a dictionary, we can assume it's return data, instead of a command.
                self.lastData = data
                continue
            
            if "frametimes" in data: # Save the frame times
                frametime = data["frametimes"]
                frameTimes[self.pluginName] = frametime[self.pluginName]
            elif "get" in data: # If the data is a get command, then we need to get the data from another plugin.
                plugins = data["get"]
                for plugin in plugins:
                    if plugin in runners:
                        self.queue.put(runners[plugin].lastData)
                    else:
                        self.queue.put(None)
            elif "sonner" in data:
                sonnerType = data["sonner"]["type"]
                sonnerText = data["sonner"]["text"]
                immediate.sonner(sonnerText, sonnerType)
            else:
                    self.lastData = data
        
        
runners = {}
frameTimes = {}

AVAILABLE_PLUGINS = {}
def GetAvailablePlugins():
    global AVAILABLE_PLUGINS
    import os
    # Get list of everything in the plugins folder
    plugins = os.listdir("ETS2LA/plugins")
    # Check if it's a folder or a file.
    for plugin in plugins:
        if os.path.isdir(f"ETS2LA/plugins/{plugin}"):
            AVAILABLE_PLUGINS[plugin] = {}
    # Remove the pycache folder.
    AVAILABLE_PLUGINS.pop("__pycache__")
    # Add the plugins.json file contents to AVAILABLE_PLUGINS[plugin][file]
    for plugin in AVAILABLE_PLUGINS:
        try:
            with open(f"ETS2LA/plugins/{plugin}/plugin.json", "r") as f:
                AVAILABLE_PLUGINS[plugin]["file"] = json.loads(f.read())
        except:
            AVAILABLE_PLUGINS[plugin]["file"] = {
                "name": plugin,
                "authors": "Unknown",
                "version": "Unknown",
                "description": "No description provided.",
                "image": "None",
                "dependencies": "None"
            }
        
    # Return
    return AVAILABLE_PLUGINS

ENABLED_PLUGINS = []
def GetEnabledPlugins():
    global ENABLED_PLUGINS
    ENABLED_PLUGINS = []
    for runner in runners:
        ENABLED_PLUGINS.append(runner)
        
    return ENABLED_PLUGINS
    
def CallPluginFunction(plugin, function, args, kwargs):
    try:
        if plugin in runners:
            runners[plugin].functionQueue.put({"function": function, "args": args, "kwargs": kwargs})
            # Wait for the answer
            startTime = time.time()
            while time.time() - startTime < 5:
                data = runners[plugin].functionQueue.get()
                if data == {"function": function, "args": args, "kwargs": kwargs}:
                    print("Waiting for answer...")
                    runners[plugin].functionQueue.put({"function": function, "args": args, "kwargs": kwargs})
                    time.sleep(0.01)
                else:
                    print("Got answer!")
                    return data
            print("Failed to get an answer.")
            return True
        else:
            return False
    except:
        import traceback
        traceback.print_exc()
        return False

def AddPluginRunner(pluginName):
    # Run the plugin runner in a separate thread. This is done to avoid blocking the main thread.
    runner = threading.Thread(target=PluginRunnerController, args=(pluginName, ), daemon=True)
    runner.start()

def RemovePluginRunner(pluginName):
    # Stop the plugin runner
    runners[pluginName].runner.terminate()
    runners.pop(pluginName)

def GetGitHistory():
    global commits_save
    try:
        # If the git history has already been retrieved, then return that instead of searching again
        if commits_save == []:
            # Vars
            api_requests = 0
            commits = []
            authors = {}

            # Get the git history as json
            import git
            repo = git.Repo(search_parent_directories=True)
            
            for commit in repo.iter_commits():
                # Add the commit to the list
                commits.append({
                    "author": commit.author.name,
                    "message": commit.message,
                    "time": commit.committed_date
                })
            
            count = len(commits)
            index = 0
            for commit in commits:
                if index <= 100: # Only get images for the first 100 commits
                    if not commit["author"] in authors:
                        if commit["author"] == "DylDev": # Hardcded because of usernames
                            url = f"https://api.github.com/users/DylDevs"
                        else:
                            print(commit["author"])
                            url = f"https://api.github.com/users/{commit['author']}"
                        # Get the avatar url from the GitHub API
                        response = requests.get(url, timeout=4)
                        api_requests += 1
                        if response.status_code == 200:
                            data = response.json()
                            avatar_url = data["avatar_url"]
                            authors[commit["author"]] = avatar_url
                        else:
                            authors[commit["author"]] = "https://github.com/favicon.ico"
                    else:
                        pass
                    
                    commit["picture"] = authors[commit["author"]]
                
                index += 1

            commits_save = commits
            return commits
        else:
            return commits_save
    except:
        import traceback
        traceback.print_exc()
        return []

# These are run on startup.
GetAvailablePlugins()