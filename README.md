# Synchronization Tool

This performs a periodic one-way synchronization of a selected directory, maintaining an exact copy of the directories and files present in the Source directory.

## Usage

Command:

`python main.py <source_directory> <replica_directory> <log_file> <sync_interval>`

- `<source_directory>`: Path to the directory you want to sync.
- `<relpica_directory>`: Path to the directory where synced files will be stored.
- `<log_file>`: Path to the log file.
- `<sync_interval>`: Time, in seconds, between each execution.

Example:

`python main.py /files/source /files/replica /logs/log_file.log 60`

The example above would sync the contents from `/files/source` into `/files/replica` every `60` seconds, keeping modification logs at `logs/log_file.log`.