#!/bin/bash

# $1 = name of node

# Prep for tmux
echo "tmux pipe-pane -o 'cat >>~/EIBP_$1.log'" > ~/tmux_start_logging.sh
sudo chmod 777 ~/tmux_start_logging.sh
echo "set -g remain-on-exit on" > ~/.tmux.conf
echo "set-hook -g after-new-session 'run ~/tmux_start_logging.sh'" >> ~/.tmux.conf
