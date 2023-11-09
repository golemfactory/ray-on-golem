import re
import sys

creating_re = re.compile(r".*] Creating ([0-9]+) nodes\.\.\..*")
created_re = re.compile(r".*] Creating ([0-9]+) nodes done.*")
terminating_re = re.compile(r".*] Terminating `[^`]+` node\.\.\..*")
terminated_re = re.compile(r".*] Terminating `[^`]+` node done.*")

creating_count = 0
created_count = 0
terminating_count = 0
terminated_count = 0

with open(sys.argv[1]) as file:
    for line in file:
        match = creating_re.match(line)
        if match:
            creating_count += int(match.groups()[0])

        match = created_re.match(line)
        if match:
            created_count += int(match.groups()[0])

        match = terminating_re.match(line)
        if match:
            terminating_count += 1

        match = terminated_re.match(line)
        if match:
            terminated_count += 1

errors = []
if creating_count != created_count:
    errors.append(
        f"Logs contains miss-matched logs at node creation level: started={creating_count} finished={created_count}"
    )

if terminating_count != terminated_count:
    errors.append(
        f"Logs contains miss-matched logs at node termination level: started={terminating_count} finished="
        f"{terminated_count}"
    )

if created_count != terminated_count:
    errors.append(
        f"Logs contains miss-matched logs between node creation and termination level: created={created_count} "
        f"terminated={terminated_count}"
    )

if errors:
    print("Errors:", file=sys.stderr)
    print("\n".join(errors), file=sys.stderr)
    exit(1)
else:
    print(f"Nodes: created={created_count} terminated={terminated_count}")
