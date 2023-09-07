import re
import sys
from datetime import datetime

# Check if a filename argument is provided
if len(sys.argv) != 2:
    print("Usage: python torque_to_swf.py <torque_log_file>")
    sys.exit(1)

# Get the filename from the command-line argument
filename = sys.argv[1]

# Read the Torque log file
try:
    with open(filename, 'r') as file:
        torque_log = file.read()
except FileNotFoundError:
    print(f"File not found: {filename}")
    sys.exit(1)

# Define a function to extract key-value pairs from the log entry
def extract_key_value_pairs(entry):
    pairs = re.findall(r'(\w+)=(\S+)', entry)
    return dict(pairs)

# Split the Torque log into individual job entries
job_entries = torque_log.strip().split('\n')

# Initialize the job counter for SWF format
job_counter = 1

# Initialize dictionaries to store user and group mappings
user_mapping = {}

# Loop through job entries and convert to SWF format
swf_entries = []
#print("Job Number, Submit Time, Wait Time, Run Time, Number of Allocated Processors, Average CPU Time Used, Used Memory, Requested Number of Processors, Requested Time, Requested Memory, Status, User ID, Group ID, Executable Number, Queue Number, Partition Number, Preceding Job Number, Think Time from Preceding Job")
for job_entry in job_entries:
    log_parts = job_entry.split(';')

    if log_parts[1] != "E":
        continue
    #skip any that arent status E bc they wont have valid start/end times


    attributes = extract_key_value_pairs(log_parts[3])

    # Extract relevant fields with default values
    submit_time = int(datetime.strptime(log_parts[0], '%d/%m/%Y %H:%M:%S').timestamp())
    start_time = int(attributes.get('start', 0))
    end_time = int(attributes.get('end', 0))
    run_time = end_time - start_time #calc runtime

    num_allocated_processors = attributes.get('nodes', ':ppn=-1') #get initial value
    num_allocated_processors = -1 if '' not in num_allocated_processors else num_allocated_processors.split("=")[1] #if it doesnt exist set to -1
    num_allocated_processors = -1 if num_allocated_processors == -1 else int(re.findall(r"(^\d+)", num_allocated_processors)[0])#same as above, match for numeric value via regex
    total_cpu_time = int(attributes.get('cput', '-1'))
    avg_cpu_time_used = total_cpu_time / num_allocated_processors
    used_memory = int(attributes.get('mem', '-1kb').replace('kb', ''))
    requested_num_processors = num_allocated_processors
    requested_time = int(attributes.get('walltime', '24:00:00').split(':')[0]) * 3600 + int(attributes.get('walltime', '24:00:00').split(':')[1]) * 60 + int(attributes.get('walltime', '24:00:00').split(':')[2])
    status = int(attributes.get('Exit_status', '-1'))

    # Extract user and group values and map them to unique IDs
    user = attributes.get('user', '-1')
    group_id = '-1'

    if user in user_mapping:
        user_id = user_mapping[user]
    else:
        user_id = len(user_mapping) + 1
        user_mapping[user] = user_id


    # Construct the SWF entry with additional information
    swf_entry = f"{job_counter}\t{submit_time}\t-1\t{run_time}\t{num_allocated_processors}\t{avg_cpu_time_used}\t{used_memory}\t{requested_num_processors}\t{requested_time}\t{status}\t{user_id}\t{group_id}-1\t-1\t-1\t-1\t-1"
    swf_entries.append(swf_entry)
    #Job Number, Submit Time, Wait Time, Run Time, Number of Allocated Processors, Average CPU Time Used, Used Memory, Requested Number of Processors, Requested Time, Requested Memory, Status, User ID, Group ID, Executable Number, Queue Number, Partition Number, Preceding Job Number, Think Time from Preceding Job
    # Increment the job counter
    job_counter += 1
    

# Print the SWF entries
print(f"total amount of jobs ={job_counter - 1}")
for swf_entry in swf_entries:
    print(swf_entry)