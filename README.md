These Fabric Scripts were updated to support both hardware and software failures.   
The PTP_EIBP_SliceBuilder... sets up the the slice (in this case a 13 router slice) at a FABRIC sie that supports PTP. PTP offers microsecond level time synchronization. The thirteen router topology is provided in the graphml file.       
EIBPDepsLarge - installs all development tools in the remote VMs. This uses remote_scripts, which will be uploaded to the remote VMs.    
EIBPStartLarge - will execute the code with the required tier values and IP addresses which is provided in the config_large_13nodes txt file.  
config_large_13Nodes file has to be edited with the proper eth port numbers which connect the Access Routers Ax to the ipnodes. we get this information from the slice reservation information we get after bulding the slice.    
After executing EIBPStartLarge, we can log in to any one of the ip hosts and ping the others. The setup disbales IP forwarding. and there is not routing protocol. So EIBP will deliver the IP packet arriving at the access routers to the destination IP node.    
To test EIBP working we can also run tcpdump or tshark at an interface to see EIBP traffic. it will be carried in frames with a type value of 85.  
EIBPTestLarge can be used slectively introduce failure at router interfaces. it will create logs. 
IF_DIRECT_DOWN_Analysis will parse the logs and print out the convergence time, the control overhead generated and the blast radius.   
If_Direct_Down_AnlaysisHelper is used by IF_DIRECT_DOWN_Analysis.   
