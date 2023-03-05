# watchman-helpers
See [00-watchman.md](00-watchman.md) for a quickstart example

## [`watchman-filter-exec.py`](./watchman-filter-exec.py)
a.k.a. `wmx`: 
```bash
watchman-filter-exec.py --help
# Usage: watchman-filter-exec.py [OPTIONS] [ARGS]...
# 
#   Filter changed files output by `watchman`; by default, only output Git-
#   tracked files.
# 
#   watchman-wait -m0 <dir> | watchman-filter-exec.py [-G/--no-git-filter] [-p/--prefix
#   <prefix>] [-v/--verbose...]
# 
# Options:
#   -G, --no-git-filter  Bypass filtering to Git-tracking files
#   -p, --prefix TEXT    Filter to relative paths beginning with this prefix
#                        (and strip the prefix)
#   -v, --verbose        1x: log to stderr when files pass filters and commands
#                        are run, and when the Git file listing is refreshed;
#                        2x: also log files that are skipped
#   --help               Show this message and exit.
```

### Examples

```bash
# Print Git-tracked filenames as changes are made 
watchman-wait -m0 . | wmx

# Log to stderr:
# - commands run on Git-tracked files
# - Git file-list refreshes (whenever anything under `.git/` is changed)
# - skipped file paths (non-Git-tracked files; only in `-vv`, not `-v`) 
watchman-wait -m0 . | wmx -vv
```

#### Continuously sync Git worktree into a running Docker container
Create a `.dockerignore` that only includes Git-tracked files, using [`make-dockerignore.py`](https://gitlab.com/runsascoded/rc/docker/-/blob/main/make-dockerignore.py):
```bash
make-dockerignore.py
```

Dockerfile that `COPY`s all Git-tracked files (thanks to generated `.dockerignore` above), and runs `next dev` auto-reloading server:
```Dockerfile
# Dockerfile
FROM node
COPY package.json package.json
RUN npm i
COPY . .
ARG PORT=3000
EXPOSE ${PORT}/tcp
ENV PATH="${PATH}:node_modules/.bin"
ENTRYPOINT ["next", "dev"]
```
Build image, run container w/ exposed webserver port: 
```bash
port=3000
docker build --build-arg port=$port -t my-image .
docker run --rm -d -p $port:$port --name my-container my-image
```

Watch for changed files, copy changed Git-tracked files into `my-container`
```bash
watchman-wait -m0 . | wmx -v docker cp {} my-container:/{}
```

Leave this running, make changes, observe changed files to be copied into `my-container`:
```
Running: docker cp next.config.js my-container:/next.config.js
Refreshing Git file list (.git/index)
Running: docker cp package-lock.json my-container:/package-lock.json
…
```
