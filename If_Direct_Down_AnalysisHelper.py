import re
import os
from collections import defaultdict
from collections import Counter

def extract_node_name(filename):
    """Extract clean node name from filename, handling various formats"""
    name = filename.replace('EIBP_', '').replace('.log', '')
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    return name.strip()

def is_log_file(filename):
    """Check if file is an EIBP log file"""
    return filename.startswith('EIBP_') and filename.endswith('.log')

def extract_if_direct_down_time(log_dir_path, end_time):
    """Extracts the earliest IF_DIRECT_DOWN timestamp from ALL nodes.
    Only considers events before end_time.
    Returns (timestamp, file_path, node_name)."""
    
    earliest_failure = None
    earliest_file = None
    earliest_node = None
    
    # Also collect ALL IF_DIRECT_DOWN events for detailed reporting
    all_events = []
    
    all_files = sorted(os.listdir(log_dir_path))
    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        node_name = extract_node_name(filename)
        
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as file:
                    for line in file:
                        if "IF_DIRECT_DOWN" in line:
                            match = re.search(r'IF_DIRECT_DOWN:(\d+\.\d+)', line)
                            if match:
                                ts = float(match.group(1))
                                if ts <= end_time:
                                    all_events.append((ts, node_name, file_path))
                                    if earliest_failure is None or ts < earliest_failure:
                                        earliest_failure = ts
                                        earliest_file = file_path
                                        earliest_node = node_name
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
    
    if earliest_failure is None:
        print(f"WARNING: No IF_DIRECT_DOWN found before END_TIME!")
    else:
        print(f"\n===== All IF_DIRECT_DOWN Events =====")
        for ts, node, fp in sorted(all_events):
            delta = ts - earliest_failure
            print(f"  {node}: {ts:.6f} (delta: +{delta:.6f}s) - {os.path.basename(fp)}")
    
    return earliest_failure, earliest_file, earliest_node


def find_earliest_deletion_time(log_dir_path, end_time=None):
    """Finds the earliest MESSAGE_TYPE_MY_LABELS_DELETE timestamp across all logs.
    Only considers events before end_time if specified."""
    earliest_deletion = None
    all_files = sorted(os.listdir(log_dir_path))

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as file:
                    for line in file:
                        if "MESSAGE_TYPE_MY_LABELS_DELETE" in line:
                            match = re.search(r'CURRENT_TIME:\s*(\d+\.\d+)', line)
                            if match:
                                deletion_time = float(match.group(1))
                                if end_time is not None and deletion_time > end_time:
                                    continue
                                if earliest_deletion is None or deletion_time < earliest_deletion:
                                    earliest_deletion = deletion_time
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

    return earliest_deletion

def extract_routing_tables(content, node_name):
    """Extract all routing tables (entries_LL) from logs"""

    lines = content.split('\n')
    tables = []

    current_time = None

    for i, line in enumerate(lines):
        time_match = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', line)
        if time_match:
            current_time = float(time_match.group(1))

        is_routing_table = False
        if 'Tier Address' in line and 'IP Address' in line:
            is_routing_table = True
        elif 'Printing Tier Address to IP Adress mapping' in line:
            is_routing_table = True

        if is_routing_table:
            entries = {}
            j = i + 1

            while j < len(lines):
                entry_match = re.search(r'^([\d.]+)\s+([\d.]+/\d+)', lines[j])
                if entry_match:
                    tier_addr = entry_match.group(1)
                    ip_cidr = entry_match.group(2)
                    entries[tier_addr] = ip_cidr
                    j += 1
                elif lines[j].strip() == '':
                    j += 1
                elif '**' in lines[j]:
                    break
                else:
                    break

            if entries:
                tables.append({
                    'timestamp': current_time,
                    'entries': entries,
                    'line_num': i,
                    'entry_count': len(entries)
                })

    return tables

def get_pre_failure_routing_state(log_dir_path, failure_time, time_buffer=1.0):
    """Gets the routing table state for each node just before failure"""
    pre_failure_routing = {}
    all_files = sorted(os.listdir(log_dir_path))

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if os.path.isfile(file_path):
            node_name = extract_node_name(filename)

            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                routing_tables = extract_routing_tables(content, node_name)

                last_routing = None
                for table in routing_tables:
                    if table['timestamp'] and table['timestamp'] < failure_time and table['entry_count'] > 0:
                        last_routing = table['entries']

                if last_routing:
                    pre_failure_routing[node_name] = last_routing

            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

    return pre_failure_routing

def get_converged_post_failure_routing_state(log_dir_path, failure_time, pre_failure_routing, end_time=None, convergence_window=10.0):
    """Gets the converged routing table state after failure (after delete messages processed).
    Only considers events within [failure_time, end_time] window."""
    post_failure_routing = {}
    all_files = sorted(os.listdir(log_dir_path))

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if not os.path.isfile(file_path):
            continue

        node_name = extract_node_name(filename)

        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            delete_process_time = None
            current_time = None
            for line in lines:
                time_match = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', line)
                if time_match:
                    current_time = float(time_match.group(1))
                ifd_match = re.search(r'IF_DIRECT_DOWN:([\d.]+)', line)
                if ifd_match:
                    current_time = float(ifd_match.group(1))
                if 'Removing Label' in line or 'MESSAGE_TYPE_PUBLISH_IP_DELETE' in line or 'MESSAGE_TYPE_MY_LABELS_DELETE' in line:
                    if current_time and current_time >= failure_time and (end_time is None or current_time <= end_time):
                        delete_process_time = current_time
                        break
                if 'Label to IP Table after removing' in line:
                    if current_time and current_time >= failure_time and (end_time is None or current_time <= end_time):
                        delete_process_time = current_time
                        break

            routing_tables = extract_routing_tables(content, node_name)
            pre_failure_entries = pre_failure_routing.get(node_name, {})

            valid_post_tables = [
                t for t in routing_tables
                if t['timestamp'] and t['timestamp'] >= failure_time
                and (end_time is None or t['timestamp'] <= end_time)
            ]

            if delete_process_time:
                for table in valid_post_tables:
                    if table['timestamp'] >= delete_process_time:
                        post_failure_routing[node_name] = (table['timestamp'], table['entries'])
                        break
            
            if node_name not in post_failure_routing:
                for table in valid_post_tables:
                    if set(table['entries'].keys()) != set(pre_failure_entries.keys()):
                        post_failure_routing[node_name] = (table['timestamp'], table['entries'])
                        break
            
            if node_name not in post_failure_routing:
                for table in valid_post_tables:
                    post_failure_routing[node_name] = (table['timestamp'], table['entries'])
                    break

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    return post_failure_routing

def get_pre_failure_my_labels_state(log_dir_path, failure_time, time_buffer=1.0):
    """Gets the My Labels for each node just before failure"""
    pre_failure_state = {}
    all_files = sorted(os.listdir(log_dir_path))

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if os.path.isfile(file_path):
            node_name = extract_node_name(filename)
            last_my_labels = None

            try:
                lines = open(file_path).read().splitlines()
                for i, line in enumerate(lines):
                    if 'printMyLabels' in line or 'My labels are:' in line:
                        # Try to find the time for this entry
                        current_time = None
                        for j in range(max(0, i-20), i):
                            time_match = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', lines[j])
                            if time_match:
                                current_time = float(time_match.group(1))

                        if current_time and current_time < failure_time:
                            labels = set()
                            for j in range(i, min(i+10, len(lines))):
                                label_match = re.search(r'label:\s*(\S+)', lines[j])
                                if label_match:
                                    labels.add(label_match.group(1))
                                if '**' in lines[j]:
                                    break
                            if labels:
                                last_my_labels = labels
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

            if last_my_labels is not None:
                pre_failure_state[node_name] = last_my_labels

    return pre_failure_state

def get_post_failure_my_labels_state(log_dir_path, failure_time, end_time=None):
    """Gets the My Labels for each node after failure (within analysis window)"""
    post_failure_state = {}
    all_files = sorted(os.listdir(log_dir_path))

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if os.path.isfile(file_path):
            node_name = extract_node_name(filename)
            first_post_my_labels = None

            try:
                lines = open(file_path).read().splitlines()
                for i, line in enumerate(lines):
                    if 'printMyLabels' in line or 'My labels are:' in line:
                        # Find time first - look back up to 20 lines for CURRENT_TIME or IF_DIRECT_DOWN
                        current_time = None
                        for j in range(max(0, i-20), i+1):
                            # Also check for IF_DIRECT_DOWN timestamp
                            ifd_match = re.search(r'IF_DIRECT_DOWN:([\d.]+)', lines[j])
                            if ifd_match:
                                current_time = float(ifd_match.group(1))
                            time_match = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', lines[j])
                            if time_match:
                                current_time = float(time_match.group(1))

                        if current_time and current_time >= failure_time and (end_time is None or current_time <= end_time):
                            labels = set()
                            # Start from i+1 to skip the printMyLabels header line
                            for j in range(i+1, min(i+10, len(lines))):
                                label_match = re.search(r'label:\s*(\S+)', lines[j])
                                if label_match:
                                    labels.add(label_match.group(1))
                                if '**' in lines[j]:
                                    break
                            if first_post_my_labels is None:  # Only take the first one after failure
                                first_post_my_labels = labels
                                break
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

            if first_post_my_labels is not None:
                post_failure_state[node_name] = first_post_my_labels

    return post_failure_state

def get_pre_failure_neighbor_state(log_dir_path, failure_time, time_buffer=1.0):
    """Gets the neighbor table state for each node just before failure"""

    pre_failure_state = {}
    all_files = sorted(os.listdir(log_dir_path))

    neighbor_table_pattern = re.compile(r'\*+ Neighbour Table \*+ CURRENT_TIME:(\d+\.\d+)')
    neighbor_entry_pattern = re.compile(r'-------\s*(.+?)\s*-----')

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if os.path.isfile(file_path):
            node_name = extract_node_name(filename)
            last_neighbors_before_failure = None

            try:
                lines = open(file_path).read().splitlines()
                for i, line in enumerate(lines):
                    match = neighbor_table_pattern.search(line)
                    if match:
                        timestamp = float(match.group(1))
                        if timestamp < failure_time:
                            neighbors = set()
                            for j in range(i + 1, len(lines)):
                                neighbor_match = neighbor_entry_pattern.search(lines[j])
                                if neighbor_match:
                                    neighbors.add(neighbor_match.group(1))
                                else:
                                    break
                            last_neighbors_before_failure = neighbors
                        else:
                            break
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

            if last_neighbors_before_failure is not None:
                pre_failure_state[node_name] = last_neighbors_before_failure

    return pre_failure_state

def get_post_delete_neighbor_state(log_dir_path, failure_time, end_time=None):
    """Gets the neighbor table state for each node RIGHT AFTER the first delete event.
    For IF_DIRECT_DOWN analysis: uses IF_DIRECT_DOWN as one of the delete keywords."""
    post_failure_state = {}
    all_files = sorted(os.listdir(log_dir_path))

    neighbor_table_pattern = re.compile(r'\*+ Neighbour Table \*+ CURRENT_TIME:(\d+\.\d+)')
    neighbor_entry_pattern = re.compile(r'-------\s*(.+?)\s*-----')

    delete_keywords = [
        'Removing Label', 'MESSAGE_TYPE_LABELS_LOST',
        'MESSAGE_TYPE_MY_LABELS_DELETE', 'Received MESSAGE_TYPE_PUBLISH_IP_DELETE',
        'Removing label', 'IF_DIRECT_DOWN'
    ]

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if not os.path.isfile(file_path):
            continue
        node_name = extract_node_name(filename)

        try:
            lines = open(file_path).read().splitlines()

            current_time = None
            first_delete_idx = None
            for i, line in enumerate(lines):
                time_match = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', line)
                if time_match:
                    current_time = float(time_match.group(1))

                # Also parse timestamp directly from IF_DIRECT_DOWN lines
                # e.g. "IF_DIRECT_DOWN:1774455771.296968"
                ifd_match = re.search(r'IF_DIRECT_DOWN:([\d.]+)', line)
                if ifd_match:
                    current_time = float(ifd_match.group(1))

                if current_time and current_time >= failure_time and (end_time is None or current_time <= end_time):
                    for kw in delete_keywords:
                        if kw in line:
                            first_delete_idx = i
                            break
                    if first_delete_idx is not None:
                        break

            if first_delete_idx is not None:
                # Collect the LAST neighbor table after the first delete event (to get final converged state)
                last_table = None
                for i in range(first_delete_idx + 1, len(lines)):
                    match = neighbor_table_pattern.search(lines[i])
                    if match:
                        ts = float(match.group(1))
                        if end_time is not None and ts > end_time:
                            break
                        neighbors = set()
                        for j in range(i + 1, len(lines)):
                            nm = neighbor_entry_pattern.search(lines[j])
                            if nm:
                                neighbors.add(nm.group(1))
                            else:
                                break
                        last_table = (ts, neighbors)
                if last_table:
                    post_failure_state[node_name] = last_table
            else:
                last_table = None
                for i, line in enumerate(lines):
                    match = neighbor_table_pattern.search(line)
                    if match:
                        ts = float(match.group(1))
                        if ts < failure_time:
                            continue
                        if end_time is not None and ts > end_time:
                            break
                        neighbors = set()
                        for j in range(i + 1, len(lines)):
                            nm = neighbor_entry_pattern.search(lines[j])
                            if nm:
                                neighbors.add(nm.group(1))
                            else:
                                break
                        last_table = (ts, neighbors)
                if last_table:
                    post_failure_state[node_name] = last_table

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    return post_failure_state

def get_post_delete_state(log_dir_path, failure_time, end_time=None):
    result = {}
    all_files = sorted(os.listdir(log_dir_path))

    neighbor_table_pattern = re.compile(r'\*+ Neighbour Table \*+ CURRENT_TIME:(\d+\.\d+)')
    neighbor_entry_pattern = re.compile(r'-------\s*(.+?)\s*-----')

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if not os.path.isfile(file_path):
            continue
        node_name = extract_node_name(filename)

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            current_time = None
            first_delete_idx = None   # <-- CHANGED: track FIRST, not last
            first_delete_ts = None    # <-- CHANGED
            deleted_labels = []

            for i, line in enumerate(lines):
                line_stripped = line.strip()

                time_match = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', line_stripped)
                if time_match:
                    current_time = float(time_match.group(1))

                # Also parse timestamp directly from IF_DIRECT_DOWN lines
                # e.g. "IF_DIRECT_DOWN:1774455771.296968"
                ifd_match = re.search(r'IF_DIRECT_DOWN:([\d.]+)', line_stripped)
                if ifd_match:
                    current_time = float(ifd_match.group(1))

                is_delete_event = False
                if 'Removing' in line_stripped and 'label' in line_stripped.lower():
                    is_delete_event = True
                    # Match patterns like "Removing Label: X" or "Removing label X from Neighbour Table"
                    label_match = re.search(r'Removing\s+[Ll]abel[:\s]+(\S+)', line_stripped)
                    if label_match and current_time:
                        if current_time >= failure_time and (end_time is None or current_time <= end_time):
                            deleted_labels.append(label_match.group(1))
                elif 'Removing neighbor' in line_stripped:
                    is_delete_event = True
                    label_match = re.search(r'Removing neighbor:\s*(\S+)', line_stripped)
                    if label_match and current_time:
                        if current_time >= failure_time and (end_time is None or current_time <= end_time):
                            deleted_labels.append(label_match.group(1))
                elif 'Deleting' in line_stripped and 'from my label table' in line_stripped:
                    is_delete_event = True
                    label_match = re.search(r'Deleting\s+(\S+)\s+from my label table', line_stripped)
                    if label_match and current_time:
                        if current_time >= failure_time and (end_time is None or current_time <= end_time):
                            deleted_labels.append(label_match.group(1))
                elif 'Found grandchild in Ip to Label Table, deleting:' in line_stripped:
                    is_delete_event = True
                    label_match = re.search(r'deleting:\s*(\S+)', line_stripped)
                    if label_match and current_time:
                        if current_time >= failure_time and (end_time is None or current_time <= end_time):
                            deleted_labels.append(label_match.group(1))
                elif 'Deleted' in line_stripped and 'labels, forwarding:' in line_stripped:
                    is_delete_event = True
                    # Extract labels from following lines
                    j = i + 1
                    while j < len(lines) and j < i + 10:  # Look ahead up to 10 lines
                        next_line = lines[j].strip()
                        if not next_line or '**' in next_line or 'Sending' in next_line or 'My' in next_line:
                            break
                        # Match label format (e.g., "2.1.1" or "3.1.1.2")
                        if re.match(r'^[\d.]+$', next_line):
                            if current_time >= failure_time and (end_time is None or current_time <= end_time):
                                deleted_labels.append(next_line)
                        j += 1
                elif 'Received MESSAGE_TYPE_LABELS_LOST' in line_stripped:
                    is_delete_event = True
                elif 'Received MESSAGE_TYPE_MY_LABELS_DELETE' in line_stripped:
                    is_delete_event = True
                elif 'Received MESSAGE_TYPE_PUBLISH_IP_DELETE' in line_stripped:
                    is_delete_event = True

                if is_delete_event and current_time:
                    if current_time >= failure_time and (end_time is None or current_time <= end_time):
                        if first_delete_idx is None:          # <-- CHANGED: only set once
                            first_delete_idx = i
                            first_delete_ts = current_time

            if first_delete_idx is None:
                continue

            # Deduplicate labels
            seen = set()
            unique_labels = []
            for label in deleted_labels:
                if label not in seen:
                    seen.add(label)
                    unique_labels.append(label)
            deleted_labels = unique_labels

            # Find neighbor table AFTER first delete event
            post_delete_neighbors = None
            post_delete_neighbor_ts = None
            for i in range(first_delete_idx + 1, len(lines)):   # <-- CHANGED
                match = neighbor_table_pattern.search(lines[i])
                if match:
                    ts = float(match.group(1))
                    if end_time is not None and ts > end_time:
                        break
                    neighbors = set()
                    for j in range(i + 1, len(lines)):
                        nm = neighbor_entry_pattern.search(lines[j])
                        if nm:
                            neighbors.add(nm.group(1))
                        else:
                            break
                    post_delete_neighbors = neighbors
                    post_delete_neighbor_ts = ts
                    break

            # Find routing table AFTER first delete event
            post_delete_routing = None
            post_delete_routing_ts = None
            search_time = first_delete_ts                       # <-- CHANGED
            for i in range(first_delete_idx + 1, len(lines)):  # <-- CHANGED
                tm = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', lines[i])
                if tm:
                    search_time = float(tm.group(1))

                is_routing_table = False
                if 'Tier Address' in lines[i] and 'IP Address' in lines[i]:
                    is_routing_table = True
                elif 'Printing Tier Address to IP Adress mapping' in lines[i]:
                    is_routing_table = True

                if is_routing_table:
                    if search_time and end_time is not None and search_time > end_time:
                        break

                    entries = {}
                    j = i + 1
                    while j < len(lines):
                        entry_match = re.search(r'^([\d.]+)\s+([\d.]+/\d+)', lines[j])
                        if entry_match:
                            entries[entry_match.group(1)] = entry_match.group(2)
                            j += 1
                        elif lines[j].strip() == '':
                            j += 1
                        elif '**' in lines[j]:
                            break
                        else:
                            break

                    if entries:
                        post_delete_routing = entries
                        post_delete_routing_ts = search_time
                        break

            result[node_name] = {
                'delete_ts': first_delete_ts,      # <-- CHANGED
                'deleted_labels': deleted_labels,
                'neighbor_table': post_delete_neighbors,
                'neighbor_ts': post_delete_neighbor_ts,
                'routing_table': post_delete_routing,
                'routing_ts': post_delete_routing_ts,
            }

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return result

def calculate_if_direct_down_convergence(log_dir_path, end_time, time_buffer=1.0):
    global failure_time, failure_file, failing_node

    # Step 1: Get IF_DIRECT_DOWN timestamp
    failure_time, failure_file, failing_node = extract_if_direct_down_time(log_dir_path, end_time)
    if failure_time is None:
        print("Failed to extract IF_DIRECT_DOWN timestamp.")
        return

    print(f"\nFailure type: IF_DIRECT_DOWN")
    print(f"Failing node (auto-detected): {failing_node}")
    print(f"Extracted IF_DIRECT_DOWN timestamp: {failure_time}")
    print(f"From file: {failure_file}")
    print(f"END_TIME (stop time): {end_time}")
    print(f"Analysis window: [{failure_time:.6f}, {end_time:.6f}] ({end_time - failure_time:.2f} seconds)")

    # Step 2: Pre-failure states
    pre_failure_neighbors = get_pre_failure_neighbor_state(log_dir_path, failure_time, time_buffer)
    pre_failure_routing = get_pre_failure_routing_state(log_dir_path, failure_time, time_buffer)

    # Step 3: Post-failure neighbor state (record lost neighbors)
    post_failure_neighbors = get_post_delete_neighbor_state(log_dir_path, failure_time, end_time)
    print(f"\n===== Post-Failure Neighbor State (after delete processing) =====")
    for node, (ts, neighbors) in sorted(post_failure_neighbors.items()):
        pre_neighbors = pre_failure_neighbors.get(node, set())
        lost_neighbors = pre_neighbors - neighbors
        if lost_neighbors:
            print(f"{node} at {ts:.6f} - Lost neighbors: {sorted(list(lost_neighbors))}")

    # Step 4: Post-failure routing state (record lost entries)
    post_failure_routing = get_converged_post_failure_routing_state(log_dir_path, failure_time, pre_failure_routing, end_time)
    print(f"\n===== Post-Failure Routing State (within analysis window) =====")
    for node, (ts, entries) in sorted(post_failure_routing.items()):
        pre_entries = pre_failure_routing.get(node, {})
        lost_entries = set(pre_entries.keys()) - set(entries.keys())
        if lost_entries:
            print(f"{node} at {ts:.6f} - Lost entries: {sorted(list(lost_entries))}")

    # Step 5: State after delete messages (My Labels comparison)
    pre_failure_my_labels = get_pre_failure_my_labels_state(log_dir_path, failure_time)
    post_failure_my_labels = get_post_failure_my_labels_state(log_dir_path, failure_time, end_time)
    post_delete_state = get_post_delete_state(log_dir_path, failure_time, end_time)

    print(f"\n{'='*80}")
    print(f"  STATE AFTER DELETE MESSAGES (within analysis window)")
    print(f"{'='*80}")

    for node in sorted(set(list(pre_failure_my_labels.keys()) + list(post_failure_my_labels.keys()))):
        # Only show deleted labels if we have BOTH pre and post-failure data
        if node in pre_failure_my_labels and node in post_failure_my_labels:
            pre_labels = pre_failure_my_labels[node]
            post_labels = post_failure_my_labels[node]
            deleted_labels = pre_labels - post_labels

            if deleted_labels:
                print(f"\n--- {node} ---")
                print(f"  Deleted labels: {sorted(list(deleted_labels))}")

    # Step 5.5: Convergence time calculation — MUST come after Step 5
    first_delete_times = {
        node: state['delete_ts']
        for node, state in post_delete_state.items()
        if state['delete_ts'] is not None
    }

    if first_delete_times:
        last_first_delete_node = max(first_delete_times, key=first_delete_times.get)
        last_first_delete_ts = first_delete_times[last_first_delete_node]
        convergence_time = last_first_delete_ts - failure_time
    else:
        last_first_delete_node = None
        last_first_delete_ts = None
        convergence_time = None

    # Print convergence summary AFTER it's been computed
    print(f"\n===== Convergence Time =====")
    if convergence_time is not None:
        print(f"  IF_DIRECT_DOWN:                            {failure_time:.6f} ")
        print(f"  Last relevant delete (topology stable):   {last_first_delete_ts:.6f}  ")
        print(f"  Convergence time:                          {convergence_time:.6f}s")
    else:
        print(f"  IF_DIRECT_DOWN:                            {failure_time:.6f}  ")
        print(f"  Last relevant delete (topology stable):   N/A")
        print(f"  Convergence time:                          N/A")


def get_pre_failure_routing_ll_state(log_dir_path, failure_time, time_buffer=1.0):
    """Gets the last print_entries_LL routing table for each node just before failure.
    Returns {node_name: set_of_tier_addresses}."""
    pre_state = {}
    all_files = sorted(os.listdir(log_dir_path))

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if not os.path.isfile(file_path):
            continue
        node_name = extract_node_name(filename)

        try:
            with open(file_path, 'r') as f:
                content = f.read()
            tables = extract_routing_tables(content, node_name)
            last_entries = None
            for table in tables:
                if table['timestamp'] and table['timestamp'] < failure_time and table['entry_count'] > 0:
                    last_entries = set(table['entries'].keys())
            if last_entries is not None:
                pre_state[node_name] = last_entries
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    return pre_state


def get_post_delete_routing_ll_state(log_dir_path, failure_time, end_time=None):
    """Gets the first print_entries_LL routing table for each node AFTER the first
    delete event (same anchor logic as get_post_delete_state).
    Returns {node_name: set_of_tier_addresses}."""
    post_state = {}
    all_files = sorted(os.listdir(log_dir_path))

    delete_keywords = [
        'Removing Label', 'MESSAGE_TYPE_LABELS_LOST',
        'MESSAGE_TYPE_MY_LABELS_DELETE', 'Received MESSAGE_TYPE_PUBLISH_IP_DELETE',
        'Removing label', 'IF_DIRECT_DOWN'
    ]

    for filename in all_files:
        if not is_log_file(filename):
            continue
        file_path = os.path.join(log_dir_path, filename)
        if not os.path.isfile(file_path):
            continue
        node_name = extract_node_name(filename)

        try:
            lines = open(file_path).readlines()

            current_time = None
            first_delete_idx = None

            for i, line in enumerate(lines):
                line_s = line.strip()
                tm = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', line_s)
                if tm:
                    current_time = float(tm.group(1))
                ifd = re.search(r'IF_DIRECT_DOWN:([\d.]+)', line_s)
                if ifd:
                    current_time = float(ifd.group(1))

                if current_time and current_time >= failure_time and (end_time is None or current_time <= end_time):
                    for kw in delete_keywords:
                        if kw in line_s:
                            first_delete_idx = i
                            break
                    if first_delete_idx is not None:
                        break

            if first_delete_idx is None:
                continue

            # Find the first routing table printed after the delete event
            search_time = current_time
            for i in range(first_delete_idx + 1, len(lines)):
                tm = re.search(r'CURRENT_TIME[:\s]+([\d.Ee+]+)', lines[i])
                if tm:
                    search_time = float(tm.group(1))

                is_routing_table = False
                if 'Tier Address' in lines[i] and 'IP Address' in lines[i]:
                    is_routing_table = True
                elif 'Printing Tier Address to IP Adress mapping' in lines[i]:
                    is_routing_table = True

                if is_routing_table:
                    if search_time and end_time is not None and search_time > end_time:
                        break
                    entries = {}
                    j = i + 1
                    while j < len(lines):
                        em = re.search(r'^([\d.]+)\s+([\d.]+/\d+)', lines[j])
                        if em:
                            entries[em.group(1)] = em.group(2)
                            j += 1
                        elif lines[j].strip() == '':
                            j += 1
                        elif '**' in lines[j]:
                            break
                        else:
                            break
                    if entries:
                        post_state[node_name] = set(entries.keys())
                        break

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    return post_state


def calculate_churn(log_dir_path, failure_time, end_time=None, time_buffer=1.0):

    pre_failure_neighbors = get_pre_failure_neighbor_state(log_dir_path, failure_time, time_buffer)
    post_failure_state = get_post_delete_neighbor_state(log_dir_path, failure_time, end_time)
    post_failure_neighbors = {node: neighbors for node, (ts, neighbors) in post_failure_state.items()}

    # Routing LL state (covers C/D nodes that don't show neighbor churn but lose LL entries)
    pre_failure_routing_ll = get_pre_failure_routing_ll_state(log_dir_path, failure_time, time_buffer)
    post_failure_routing_ll = get_post_delete_routing_ll_state(log_dir_path, failure_time, end_time)

    print("="*100)
    print(" "*30 + "IF_DIRECT_DOWN CHURN ANALYSIS")
    print("="*100)
    print()
    
    failing_node_str = failing_node if 'failing_node' in globals() and failing_node else "UNKNOWN"
    print(f"Failure type: IF_DIRECT_DOWN")
    print(f"Failing node: {failing_node_str}")
    print(f"Using failure_time: {failure_time}")
    print(f"Using end_time: {end_time}")
    print(f"Analysis window: [{failure_time:.6f}, {end_time:.6f}]" if end_time else f"Analysis window: [{failure_time:.6f}, no limit]")
    print(f"Pre-failure nodes found: {len(pre_failure_neighbors)}")
    print(f"Post-failure nodes found: {len(post_failure_neighbors)}")
    print()

    churned_nodes = []
    unchanged_nodes = []
    node_changes = {}         # neighbor-level changes
    routing_ll_changes = {}   # routing LL-level changes

    all_nodes = sorted(set(
        list(pre_failure_neighbors.keys()) +
        list(post_failure_neighbors.keys()) +
        list(pre_failure_routing_ll.keys()) +
        list(post_failure_routing_ll.keys())
    ))

    for node in all_nodes:
        # --- Neighbor table diff ---
        pre_nb  = pre_failure_neighbors.get(node, set())
        post_nb = post_failure_neighbors.get(node, set())
        nb_removed = pre_nb - post_nb

        # --- Routing LL diff ---
        pre_ll  = pre_failure_routing_ll.get(node, set())
        post_ll = post_failure_routing_ll.get(node, set())
        ll_removed = pre_ll - post_ll

        has_nb_change = bool(nb_removed)
        has_ll_change = bool(ll_removed)

        if has_nb_change:
            node_changes[node] = {
                'removed': nb_removed,
                'pre_count':  len(pre_nb),
                'post_count': len(post_nb)
            }
        if has_ll_change:
            routing_ll_changes[node] = {
                'removed': ll_removed,
                'pre_count':  len(pre_ll),
                'post_count': len(post_ll)
            }

        if has_nb_change or has_ll_change:
            churned_nodes.append(node)

    # ---- Neighbor Table section ----
    print("===== Neighbor Table Changes Due to IF_DIRECT_DOWN Failure =====\n")

    no_data_nodes = []
    for node in all_nodes:
        if node in node_changes:
            changes = node_changes[node]
            if changes['removed']:
                print(f"{node}: Lost {len(changes['removed'])} neighbors: {sorted(list(changes['removed']))}")
            print()
        elif node not in post_failure_neighbors:
            no_data_nodes.append(node)

    # ---- Routing LL (print_entries_LL) section ----
    print("===== Routing Table (print_entries_LL) Changes Due to IF_DIRECT_DOWN Failure =====\n")

    for node in all_nodes:
        if node in routing_ll_changes:
            changes = routing_ll_changes[node]
            if changes['removed']:
                print(f"{node}: Lost {len(changes['removed'])} labels: {sorted(list(changes['removed']))}")
            print()

    # ---- Summary ----
    # Rebuild unchanged_nodes as those with no churn of any kind
    unchanged_nodes = [n for n in all_nodes if n not in churned_nodes and n not in no_data_nodes]

    total_nodes = len(all_nodes)
    churned_count = len(churned_nodes)
    unchanged_count = len(unchanged_nodes)
    no_data_count = len(no_data_nodes)
    churn_rate = (churned_count / total_nodes * 100) if total_nodes > 0 else 0

    print("="*100)
    print(" "*30 + "IF_DIRECT_DOWN CHURN SUMMARY")
    print("="*100)
    print(f"\nTotal nodes in network: {total_nodes}")
    print(f"Nodes that experienced churn: {churned_count}")
    print(f"  - Neighbor table churn: {len(node_changes)} node(s): {', '.join(sorted(node_changes.keys())) or 'none'}")
    print(f"  - Routing LL churn:     {len(routing_ll_changes)} node(s): {', '.join(sorted(routing_ll_changes.keys())) or 'none'}")
    if no_data_nodes:
        print(f"Nodes with no post-failure data in window: {no_data_count} ({', '.join(no_data_nodes)})")
    print()
    print(f"Churn Rate: {churned_count}/{total_nodes} = {churn_rate:.1f}%")
    print()

    if churned_nodes:
        print(f"Churned nodes: {', '.join(sorted(churned_nodes))}")

    return {
        'total_nodes': total_nodes,
        'churned_nodes': churned_count,
        'unchanged_nodes': unchanged_count,
        'churn_rate': churn_rate,
        'churned_node_list': churned_nodes,
        'unchanged_node_list': unchanged_nodes,
        'node_changes': node_changes,
        'routing_ll_changes': routing_ll_changes
    }
