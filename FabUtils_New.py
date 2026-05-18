'''
Author: Peter Willis
Desc: Collection of scripts to aid in the testing of FABRIC experiments. 

THE SLICE MUST ALREADY BE CREATED FOR THIS TO WORK
'''

from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
from ipaddress import ip_address, IPv4Address, IPv4Network
import datetime
import ntpath

class FabOrchestrator:
    # Constructor, get access to the slice and nodesdownlo
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

    def _check_for_errors(self, stdout, stderr):
        """Check both stdout and stderr for error indicators.
        
        Catches:
        - stderr with error keywords
        - stdout with curl/connection errors (Recv failure, Connection reset)
        - stdout with DNF/package resolution errors
        - stdout with permission errors
        - stdout with file not found errors
        """
        
        # Error patterns to search for in BOTH stdout and stderr
        error_patterns = [
            'error',
            'failed',
            'failure',
            'not found',
            'cannot find',
            'permission denied',
            'no such file',
            'unable to',
            'exception',
            'traceback',
        ]
        
        # Specific error patterns that appear in stdout during installation
        stdout_error_patterns = [
            '[error]',
            'curl error',
            'connection reset by peer',
            'recv failure',
            'status code: 40',  # 403, 404, etc.
            'unable to resolve',
            'no packages matched',
            'broken dependencies',
            'transaction check failed',
            'transaction test failed',
            'running transaction failed',
            'nothing to do',  # Can indicate package not found
        ]
        
        # Check stderr
        if stderr:
            stderr_lower = stderr.lower()
            for pattern in error_patterns:
                if pattern in stderr_lower:
                    return True
        
        # Check stdout for installation/download errors
        if stdout:
            stdout_lower = stdout.lower()
            
            # Check general error patterns
            for pattern in error_patterns:
                if pattern in stdout_lower:
                    return True
            
            # Check specific stdout error patterns
            for pattern in stdout_error_patterns:
                if pattern in stdout_lower:
                    return True
        
        return False

    def _extract_error_message(self, stdout, stderr):
        """Extract a concise error message from stdout or stderr."""
        
        # Priority: check stderr first
        if stderr:
            lines = stderr.split('\n')
            for line in lines:
                line_clean = line.strip()
                if line_clean and any(keyword in line_clean.lower() for keyword in ['error', 'failed', 'exception']):
                    return f"STDERR: {line_clean[:250]}"
        
        # Then check stdout for specific error patterns
        if stdout:
            lines = stdout.split('\n')
            
            # Look for lines with [MIRROR] errors or Curl errors
            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue
                
                if '[MIRROR]' in line_clean or 'Curl error' in line_clean:
                    return f"STDOUT: {line_clean[:250]}"
            
            # Look for lines with error keywords
            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue
                
                if any(keyword in line_clean.lower() for keyword in ['error', 'failed', 'connection reset', 'recv failure', 'unable to']):
                    return f"STDOUT: {line_clean[:250]}"
            
            # If no specific error line found, look for status codes or common errors
            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue
                
                if 'status code' in line_clean.lower():
                    return f"STDOUT: {line_clean[:250]}"
        
        return None
        
    def executeCommandsParallel(self, command, prefixList=None, excludedList=None, addNodeName=False, returnOutput=False, show_only_errors=True):    
        """Execute a command, in parallel using threads, on all or a subset of
            remote FABRIC nodes. ONLY SHOWS FAILURES BY DEFAULT.
            
            param command: Command string to execute
            param prefix_list: A naming prefix (ex. 'C' for client) that groups nodes together to run the same configuration.
            param excluded_list: A naming prefix that groups nodes together to NOT run the desired configuration.
            param addNodeName: Add the name of the node to the command. The command MUST include the string format '{name}' for this to work.
            param returnOutput: If the stdout/console output should be captured, set to True.
            param show_only_errors: If True (default), only show failures. If False, show all output.
            returns: The stdout of the command run on each node if set in returnOutput, otherwise None.
        """
        # Nodes...
        cmd_output = {}
        try:
            # Create/execute threads
            execute_threads = {}
            
            for node in self.selectedNodes(prefixList, excludedList):
                node_name = node.get_name()
                
                if addNodeName is True:
                    final_command = command.format(name=node_name)
                else:
                    final_command = command
                
                print(f"Starting command on node {node_name}")
                print(f"Command to execute: {final_command}")
                
                execute_threads[node] = node.execute_thread(final_command)

            # Wait for results from threads
            failed_nodes = {}
            successful_count = 0
                
            for node, thread in execute_threads.items():
                node_name = node.get_name()
                stdout, stderr = thread.result()
                
                # Check if command failed - look in both stdout and stderr
                is_failed = self._check_for_errors(stdout, stderr)
                
                if is_failed:
                    # Store failed node info
                    failed_nodes[node_name] = {
                        'stdout': stdout,
                        'stderr': stderr
                    }
                    
                    # Show failure immediately with extracted error message
                    print(f"\n FAILURE on {node_name}:")
                    error_msg = self._extract_error_message(stdout, stderr)
                    if error_msg:
                        print(f"   {error_msg}\n")
                    else:
                        # Fallback: show last 300 chars
                        if stderr:
                            print(f"   STDERR: {stderr[-300:]}\n")
                        elif stdout:
                            print(f"   STDOUT: {stdout[-300:]}\n")
                
                else:
                    successful_count += 1
                
                if returnOutput:
                    cmd_output[node_name] = stdout
            
            # Summary
            total = successful_count + len(failed_nodes)
            if not show_only_errors or (show_only_errors and successful_count > 0 and len(failed_nodes) == 0):
                print(f"\n Completed: {successful_count}/{total} nodes succeeded")
            
            if failed_nodes and show_only_errors:
                print(f"\n  {len(failed_nodes)} node(s) had errors")
        
        except Exception as e:
            print(f"Exception: {e}")

        if returnOutput:
            return cmd_output
        return None
    
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

    
    def downloadFilesParallel(self, localLocation, remoteLocation, prefixList=None, excludedList=None, addNodeName=False):
        '''
        Download a file, in parallel using threads, from all or a subset of remote FABRIC nodes.

        :param localLocation: The path to where the downloaded file should be stored, including the filename.
        :param remoteLocation: The full path of the file to be downloaded.
        :param prefixList: A naming prefix (ex: C for client) that groups nodes together to run the same configuration.
        :param excludedList: A naming prefix that groups nodes together to NOT run the desired configuration.
        :param addNodeName: Add the name of the node to the file path (local and/or remote). The path MUST include the string format {name} for this to work.
        '''
        
        #Create execute threads
        execute_threads = {}
        for node in self.selectedNodes(prefixList, excludedList):
            nodeName = node.get_name()
            if(addNodeName is True):
                finalRemoteLocation = remoteLocation.format(name=nodeName)
                finalLocalLocation =  localLocation.format(name=nodeName)
            else:
                finalRemoteLocation = remoteLocation
                finalLocalLocation =  localLocation

            print(f"Starting download on node {nodeName}")
            print(f'File to download: {finalRemoteLocation}')
            print(f'Location of download: {finalLocalLocation}')

            execute_threads[node] = node.download_file_thread(finalLocalLocation, finalRemoteLocation)

        #Wait for results from threads
        for node,thread in execute_threads.items():
            print(f"Waiting for result from node {node.get_name()}")
            
            try:
                output = thread.result()
            except Exception as e:
                print(f"Exception: {e}")
            
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
