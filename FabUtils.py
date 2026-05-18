'''
Author: Peter Willis
Desc: Collection of scripts to aid in the testing of FABRIC experiments. 

THE SLICE MUST ALREADY BE CREATED FOR THIS TO WORK
'''

from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
from ipaddress import ip_address, IPv4Address, IPv4Network
from pathlib import Path
import datetime
import ntpath

class FabOrchestrator:
    # Constructor, get access to the slice and nodes
    def __init__(self, sliceName):
        '''
        Gain access to the FABRIC slice and its nodes.

        :param sliceName: The name of the slice you are working on.
        '''
        
        try:            
            # Slice
            self.slice = fablib_manager().get_slice(sliceName)

            # Nodes
            self.nodes = self.slice.get_nodes()

            print(f"Slice name: {sliceName}\nSlice and nodes were acquired successfully.")
 
        except Exception as e:
            print(f"Exception: {e}")

    
    def selectedNodes(self, prefixList=None, excludedList=None):
        '''
        Perform an action (execute a command, up/download a file, etc.) on a subset of nodes.
        This is an iterator meant to be used by other functions or in a loop.

        :param prefixList: A naming prefix (ex: C for client) that groups nodes together to run the same configuration.
        :param excludedList: A naming prefix that groups nodes together to NOT run the desired configuration.
        '''
        
        if(prefixList):
            prefixList = tuple(map(str.strip, prefixList.split(",")))

        if(excludedList):
            excludedList = tuple(map(str.strip, excludedList.split(",")))
        
        for node in self.nodes:
            nodeName = node.get_name()

            if((excludedList and nodeName.startswith(excludedList)) or (prefixList and not nodeName.startswith(prefixList))):
                continue
            
            yield node

    
    def executeCommandsParallel(self, command, prefixList=None, excludedList=None,
                                fmt=None, returnOutput=False, test=False):
        '''
        Execute a command, in parallel using threads, on all or a subset of remote FABRIC nodes.

        :param prefixList: A naming prefix (ex: C for client) that groups nodes together to run the same configuration.
        :param excludedList: A naming prefix that groups nodes together to NOT run the desired configuration.
        :param addNodeName: Add the name of the node to the command. The command MUST include the string format {name} for this to work.
        :param returnOutput: If the stdout/console output should be captured, set to True.
        :returns: The stdout of the command run on each node if set in returnOutput, otherwise None.
        '''

        cmdOutput = {}
        try:
            # --- launch one thread per node ------------------------------------
            execute_threads = {}
            for node in self.selectedNodes(prefixList, excludedList):
                nodeName = node.get_name()

                # base substitutions
                subs = {"name": nodeName}

                if(fmt):
                    if callable(fmt):               # dynamic per-node mapping
                        subs.update(fmt(nodeName))
                    elif isinstance(fmt, dict):     # static per-node mapping
                        subs.update(fmt.get(nodeName, {}))
                    # fmt == True -> legacy: no additional keys

                finalCommand = command.format(**subs)
                print(f"Starting command on node {nodeName}")
                print(f"Command to execute: {finalCommand}")

                if(not test):
                    execute_threads[node] = node.execute_thread(finalCommand)

            if(test):
                return

            # --- collect results -----------------------------------------------
            for node, thread in execute_threads.items():
                nodeName = node.get_name()
                print(f"\n==== {nodeName} RESULTS ====")
                stdout, stderr = thread.result()
                print(f"stdout:\n{stdout}")
                print(f"stderr:\n{stderr}")
                
                if(returnOutput):
                    cmdOutput[nodeName] = stdout

        except Exception as e:
            print(f"Exception: {e}")

        if(returnOutput):
            return cmdOutput


    
    def uploadDirectoryParallel(self, directory, remoteLocation=None, prefixList=None, excludedList=None):
        '''
        Upload a directory, in parallel using threads, onto all or a subset of remote FABRIC nodes.

        :param directory: The path to the directory you wish to upload.
        :param remoteLocation: The full path of the remote directory you wish to place the uploaded directory.
        :param prefixList: A naming prefix (ex: C for client) that groups nodes together to run the same configuration.
        :param excludedList: A naming prefix that groups nodes together to NOT run the desired configuration.
        '''
        
        if(remoteLocation is None):
            remoteLocation = "/home/rocky"
        
        print(f'Directory to upload: {directory}\nPlaced in: {remoteLocation}')

        try:
            #Create execute threads
            execute_threads = {}
            for node in self.selectedNodes(prefixList, excludedList):
                print(f"Starting upload on node {node.get_name()}")
                execute_threads[node] = node.upload_directory_thread(directory, remoteLocation)

            #Wait for results from threads
            for node,thread in execute_threads.items():
                print(f"Waiting for result from node {node.get_name()}")
                output = thread.result()
                print(f"Output: {output}")

        except Exception as e:
            print(f"Exception: {e}")

        return    

    
    def uploadFileParallel(self, file, remoteLocation=None, prefixList=None, excludedList=None):
        '''
        Upload a file, in parallel using threads, onto all or a subset of remote FABRIC nodes.

        :param file: The path to the file you wish to upload.
        :param remoteLocation: The full path of the remote directory you wish to place the uploaded directory.
        :param prefixList: A naming prefix (ex: C for client) that groups nodes together to run the same configuration.
        :param excludedList: A naming prefix that groups nodes together to NOT run the desired configuration.
        '''
        
        if(remoteLocation is None):
            fileName = ntpath.basename(file)
            remoteLocation = f"/home/rocky/{fileName}"
        
        print(f'File to upload: {file}\nPlaced in: {remoteLocation}')

        try:
            #Create execute threads
            execute_threads = {}
            for node in self.selectedNodes(prefixList, excludedList):
                print(f"Starting upload on node {node.get_name()}")
                execute_threads[node] = node.upload_file_thread(file, remoteLocation)

            #Wait for results from threads
            for node,thread in execute_threads.items():
                print(f"Waiting for result from node {node.get_name()}")
                output = thread.result()
                print(f"Output: {output}")

        except Exception as e:
            print(f"Exception: {e}")

        return

    
    def downloadFilesParallel(
            self,
            localLocation,
            remoteLocation,
            prefixList=None,
            excludedList=None,
            fmt=None,
        ):
        """
        Download a file in parallel from multiple FABRIC nodes.

        localLocation / remoteLocation may be str or pathlib.Path and
        may contain placeholders like {name}.
        """

        # Convert Path objects to strings once, up front
        localTemplate  = str(localLocation)
        remoteTemplate = str(remoteLocation)

        execute_threads = {}

        for node in self.selectedNodes(prefixList, excludedList):
            nodeName = node.get_name()

            # Substitution variables for this node
            fmt_vars = {"name": nodeName}
            if fmt and nodeName in fmt:
                fmt_vars.update(fmt[nodeName])

            try:
                finalRemoteLocation = remoteTemplate.format(**fmt_vars)
                finalLocalLocation  = localTemplate.format(**fmt_vars)
            except KeyError as e:
                raise ValueError(
                    f"Missing format key {e} for node {nodeName}"
                ) from None

            print(f"Starting download on node {nodeName}")
            print(f"File to download:     {finalRemoteLocation}")
            print(f"Location of download: {finalLocalLocation}")

            execute_threads[node] = node.download_file_thread(
                finalLocalLocation, finalRemoteLocation
            )

        # Gather results
        for node, thread in execute_threads.items():
            print(f"Waiting for result from node {node.get_name()}")
            try:
                output = thread.result()
            except Exception as e:
                print(f"Exception: {e}")
            else:
                print(f"Output: {output}")

        return


    
    def addIPAddressToInterface(self, node, interface, ipAddress, mask):
        '''
        Add a NetworkManager-controlled IPv4 address to a node on a specific interface.
        This should only be used if NetworkManager is required, there are easier ways
        of adding addressing in FABRIC that does not involve NetworkManager.

        :param node: The FABRIC Node object to modify.
        :param interface: The name of the interface to add the IPv4 address.
        :param ipAddress: The dotted-decimal IPv4 address without any mask information.
        :param mask: The subnet mask of the IPv4 address using the CIDR prefix (no slash).
        '''

        command = ("sudo nmcli con add type ethernet " 
                  f"con-name {interface} ifname {interface} "
                  f"autoconnect yes ipv4.method manual ipv4.addresses {ipAddress}/{mask} "
                  f"&& sudo nmcli dev set {interface} managed yes")
        
        node.execute(command)
        print(f"Interface {interface} has been configured with IP address {ipAddress}/{mask}")
        
        return

    
    def saveSSHCommands(self):
        '''
        Grab the SSH command for each node in the topology and save it to a file in the local directory.
        '''
        
        with open(f"{self.slice.get_name()}_ssh_cmds.txt", "w") as sshFile:
            for node in self.nodes:
                sshFile.write(f"{node.get_name()}:\n")
                sshFile.write(f"{node.get_ssh_command()}\n")

        return

    
    def renewSlice(self, daysToAdd):
        '''
        Renew the slice for a set number of days.

        :param daysToAdd: The number of days to add to the slice lifetime.
        '''
        
        endDate = (datetime.datetime.now() + datetime.timedelta(days=daysToAdd)).strftime("%Y-%m-%d %H:%M:%S %z") + "+0000"
        self.slice.renew(endDate)
        
        return

    
    def getInterfaceSubnet(self, intfName):
        '''
        Return the subnet of a FABRIC node's interface
        '''
        
        intf = self.slice.get_interface(intfName)
        
        subnet = IPv4Network(f"{intf.get_ip_addr()}/24", strict=False)
        
        return subnet


    def getInterfaceName(self, nodeName, neighborName):
        '''
        Return the name of an interface (e.g., ethX) given the name of the node and who they are connected to.
        '''

        return self.slice.get_interface(f"{nodeName}-intf-{neighborName}-p1").get_device_name()
