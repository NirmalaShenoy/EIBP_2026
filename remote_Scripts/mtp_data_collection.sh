#!/bin/bash

# Remove additional log files
## Nirmala - I dont think we need this file 
sudo rm ~/*.log

# Kill the prior session if it is still there for some reason
tmux has-session -t mnlr 2>/dev/null
if [ $? == 0 ]; then
  tmux kill-session -t mnlr
fi

# Start collecting mtp messages and parse them when the experiment concludes.
tmux new-session -d -s mnlr "cd ~/MNLR && sudo ./MNLR"

echo "Script has finished"