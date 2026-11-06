#!/usr/bin/env bash
# Simulate docker pull stdout with \\r in-place refreshes (2–3 layers).
set -euo pipefail

# Layer aaa111: Downloading with MB/MB via \\r refreshes
printf 'aaa111: Pulling fs layer\n'
printf 'aaa111: Downloading [=>] 2.5MB/50MB\r'
sleep 0.05
printf 'aaa111: Downloading [====>] 12.5MB/50MB\r'
sleep 0.05
printf 'aaa111: Downloading [=========>] 25MB/50MB\r'
sleep 0.05
printf 'aaa111: Downloading [==================>] 50MB/50MB\r'
printf 'aaa111: Download complete\n'
printf 'aaa111: Extracting [=>] 20%%\r'
sleep 0.05
printf 'aaa111: Extracting [=====>] 60%%\r'
sleep 0.05
printf 'aaa111: Extracting [==========>] 100%%\r'
printf 'aaa111: Pull complete\n'

# Layer bbb222: parallel-ish download
printf 'bbb222: Pulling fs layer\n'
printf 'bbb222: Waiting\n'
printf 'bbb222: Downloading [=>] 1MB/20MB\r'
sleep 0.05
printf 'bbb222: Downloading [=====>] 10MB/20MB\r'
sleep 0.05
printf 'bbb222: Downloading [==========>] 20MB/20MB\r'
printf 'bbb222: Download complete\n'
printf 'bbb222: Extracting [====>] 40%%\r'
sleep 0.05
printf 'bbb222: Extracting [==========>] 100%%\r'
printf 'bbb222: Pull complete\n'

# Layer ccc333: already exists
printf 'ccc333: Already exists\n'

printf 'Digest: sha256:deadbeef\n'
printf 'Status: Downloaded newer image for example:latest\n'
exit 0
