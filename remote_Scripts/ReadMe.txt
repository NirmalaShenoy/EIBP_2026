mtp_data_collection is not necessary.
to run EIBP we use a config file that provides node scpecifc CL parameters to be included durng executable execution
we are using cells to start EIBP and kill EIBP


stop_MNLR is also not necessary as we have cells to record the stop time and to kill tmux.

init_mtp - should be renamed as init_mnlr
this sets up the mux sessions at every node and stores the screen prints in the node_logs

intf_down.sh
uses nft for the traffic throttling. 
records the time ?? what time (Peter) 
