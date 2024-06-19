import re
import sys

creating_re = re.compile(r"^.*] Starting `[^`]+` node\.\.\..*$")
created_re = re.compile(r"^.*] Starting `[^`]+` node done.*$")
terminating_re = re.compile(r"^.*] Stopping `[^`]+` node\.\.\..*$")
terminated_re = re.compile(r"^.*] Stopping `[^`]+` node done.*$")

creating_count = 0
created_count = 0
terminating_count = 0
terminated_count = 0

with open(sys.argv[1]) as file:
    for line in file:
        match = creating_re.match(line)
        if match:
            creating_count += 1

        match = created_re.match(line)
        if match:
            created_count += 1

        match = terminating_re.match(line)
        if match:
            terminating_count += 1

        match = terminated_re.match(line)
        if match:
            terminated_count += 1

errors = []
if terminating_count != terminated_count:
    errors.append(
        f"Logs contains miss-matched logs at node termination level: started={terminating_count} finished="
        f"{terminated_count}"
    )

if creating_count != terminated_count:
    errors.append(f"Logs contains miss-matched logs between node creating and termination level!")

if not created_count:
    errors.append("No completed node creation entries found in log file!")

min_creating = int(sys.argv[2])
if creating_count < min_creating:
    errors.append(f"Node creation is below `{min_creating}`")

print(f"Nodes: {creating_count=} {created_count=} {terminating_count=} {terminated_count=}")

if errors:
    print("Errors:", file=sys.stderr)
    print("\n".join(errors), file=sys.stderr)
    exit(1)
