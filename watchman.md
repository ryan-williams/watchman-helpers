# `watchman` basic example
I found [the `watchman` docs](https://facebook.github.io/watchman/) hard to follow / bereft of useful examples. Below is my attempt at a quickstart guide.

- [0. Install `watchman`](#install)
- [1. Configure a "watch" on the current directory](#watch)
    - [1b. List currently watched directories](#watch-list)
    - [1c. Remove a watched directory](#watch-del)
- [2. Set up a "trigger": continuously run a command in response to changes](#trigger)
    - [2a. `rsync` a directory to a remote host](#rsync-example)
        - [Is there a simpler way to trigger on all files?](#patterns)
        - [Factoring command to a file](#factor-command)
    - [2b. List active triggers for current directory](#trigger-list)
    - [2c. Delete trigger](#trigger-del)
- [3. Debugging / Monitoring](#debug)
    - [3a. `watchman-wait`: print changed file names noticed by `watchman`](#watchman-wait)
    - [3b. View logs from triggered scripts (and other `watchman` events)](#logs)
        - [Find `watchman` logfile](#logfile)
        - [Tail the log](#tail-logfile)

## 0. Install `watchman` <a id="install"></a>
See [installation docs](https://facebook.github.io/watchman/docs/install.html).

## 1. Configure a "watch" on the current directory <a id="watch"></a>
```bash
watchman watch .
```
([`watch` docs](https://facebook.github.io/watchman/docs/cmd/watch.html))

### 1b. List currently watched directories <a id="watch-list"></a>
```bash
watchman watch-list
# {
#     "version": "2023.02.20.00",
#     "roots": [
#         "$PWD"
#     ]
# }
```
This should just show the directory you told it to watch above (I've substituted `$PWD` here, it will be a literal absolute path on your system).

([`watch-list` docs](https://facebook.github.io/watchman/docs/cmd/watch-list.html))

### 1c. Remove a watched directory <a id="watch-del"></a>
```bash
watchman watch-del .
```

([`watch-del` docs](https://facebook.github.io/watchman/docs/cmd/watch-del.html))

## 2. Set up a "trigger": continuously run a command in response to changes <a id="trigger"></a>

### 2a. `rsync` a directory to a remote host <a id="rsync-example"></a>
In this example, we'll `rsync` the current directory to a remote host
```bash
# Set up params
HOST=ec2                                       # configure this SSH host in your ~/.ssh/config
DST_DIR="`basename`"                           # remote directory to mirror this one to; `basename` will target a directory with the same name on the remote host (under your $HOME directory on that host)
trigger_name=ec2-sync                          # arbitrary name, used for `trigger-del` later
trigger_patterns=('**/*' '**/.*')              # trigger on all files in the current directory
trigger_cmd=(rsync -avzh ./ "$HOST:$DST_DIR")  # rsync the current directory to the remote host/dir

# Create the "trigger". It will begin running immediately and continuously (in response to file changes in the current directory)
watchman -- trigger "$PWD" "$trigger_name" "${trigger_patterns[@]}" -- "${trigger_cmd[@]}"
```

#### Is there a simpler way to trigger on all files? <a id="patterns"></a>
The patterns `('**/*' '**/.*')` are the only way I've found to get all files recursively under the watched root (including "hidden" files and directories, that begin with a `.`). However, when creating the trigger I've had the watchman logs print an error like:

```
trigger <dir>:<name> failed: posix_spawnp: Argument list too long
```

Apparently there is an inital run attempt that includes all eligible files as positional arguments. Maybe there's a better way, or workaround 🤷‍♂️. The "[Simple Pattern Syntax](https://facebook.github.io/watchman/docs/simple-query.html)" page doesn't seem to say, and single globs like `(`'*' '.*')` (Bash array syntax, as above) did not trigger for changes in subfolders.

#### Factoring command to a file <a id="factor-command"></a>
If your command gets more complex, you might want to factor it out to its own file, e.g.:

<details><summary><code>sync.sh</code></summary>

```bash
#!/usr/bin/env bash

# Configure this SSH host in your ~/.ssh/config
HOST=ec2
# Remote directory to mirror the current directory to. As written here, will target a directory
# with the same `basename` on the remote host (under your `$HOME` directory on that host)
DST_DIR="$(basename "$(dirname "${BASH_SOURCE[0]}")")"

# List some exclude paths here to pass to `rsync`
excludes=(.DS_Store __pycache__ .ipynb_checkpoints .pytest_cache '*.egg-info')
exclude_args=()
for exclude in "${excludes[@]}"; do
    exclude_args+=(--exclude "$exclude")
done

rsync -avzh "$@" "${exclude_args[@]}" ./ "$HOST:$DST_DIR/"
```
</details>

Then make sure to mark it as executable, and pass an absolute path to that script to `watchman -- trigger …`:

```bash
chmod 755 sync.sh
watchman -- trigger "$PWD" "$trigger_name" "${trigger_patterns[@]}" -- "$PWD/sync.sh"
```

([`trigger` docs](https://facebook.github.io/watchman/docs/cmd/trigger.html))

### 2b. List active triggers for current directory <a id="trigger-list"></a>
```bash
watchman trigger-list .
# {
#     "version": "2023.02.20.00",
#     "triggers": [
#         {
#             "append_files": true,
#             "name": "ec2-sync",
#             "stdin": [ "name", "exists", "new", "size", "mode" ],
#             "expression": [ "anyof", [ "match", "*", "wholename" ] ],
#             "command": [ "rsync", "-avzh", "./", "$HOST:$DST_DIR" ]
#         }
#     ]
# }
```

([`trigger-list` docs](https://facebook.github.io/watchman/docs/cmd/trigger-list.html))

### 2c. Delete trigger <a id="trigger-del"></a>
```bash
watchman trigger-del . "$trigger_name"
```

([`trigger-del` docs](https://facebook.github.io/watchman/docs/cmd/trigger-del.html))

## 3. Debugging / Monitoring <a id="debug"></a>

### 3a. `watchman-wait`: print changed file names noticed by `watchman` <a id="watchman-wait"></a>
```bash
watchman-wait -m0 .
```
- `-m0` causes this to run indefinitely (by default, it exits after one event, i.e. `-m1`)
- `.` watches the current directory

([`watchman-wait` docs](https://facebook.github.io/watchman/docs/watchman-wait.html)

### 3b. View logs from triggered scripts (and other `watchman` events) <a id="logs"></a>

#### Find `watchman` logfile <a id="logfile"></a>
```bash
logfile="$(ps aux | grep watchman | grep -o -- '--logfile=\S*' | awk -F= '{ print $2 }')"
```
- For me (on macOS, with `watchman` installed by Homebrew]()), this is `/opt/homebrew/var/run/watchman/ryan-state/log`.
- Thanks to [this StackOverflow answer](https://stackoverflow.com/a/42385046/544236)
- ["Where are the logs"](https://facebook.github.io/watchman/docs/troubleshooting.html#where-are-the-logs) docs were not helpful

#### Tail the log <a id="tail-logfile"></a>
Continuously stream new output to the logfile:
```bash
tail -f "$logfile"
```
