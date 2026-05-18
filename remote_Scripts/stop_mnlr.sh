#!/bin/bash

## Provides a way of stopping an MTP process and record the time it is stopped.

# Get the time
date +%s%3N > stop_time.txt

# Stop MTP process
tmux kill-session -t MNLR