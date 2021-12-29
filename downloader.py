import utils
import sys

for arg in sys.argv[1:]:
	utils.process_task_group(arg)

print("Done")