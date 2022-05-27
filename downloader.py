import utils
import special_tasks
import sys

if "--special" in sys.argv:
	sys.argv.remove("--special")
	if "id_range" in sys.argv:
		sys.argv.remove("id_range")
		special_tasks.get_id_range_task(int(sys.argv[1]), int(sys.argv[2]))

else:
	for arg in sys.argv[1:]:
		utils.process_task_group(arg)

print("Done")