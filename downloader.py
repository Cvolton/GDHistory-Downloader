import utils
import special_tasks
import sys

if "--special" in sys.argv:
	sys.argv.remove("--special")
	if "id_range" in sys.argv:
		sys.argv.remove("id_range")
		special_tasks.get_id_range_task(int(sys.argv[1]), int(sys.argv[2]))
	if "find_cutoffs" in sys.argv:
		sys.argv.remove("find_cutoffs")
		special_tasks.find_cutoffs_for_today()
	if "rated_sheet" in sys.argv:
		sys.argv.remove("rated_sheet")
		special_tasks.generate_rated_sheet()
	if "mod_sheet" in sys.argv:
		sys.argv.remove("mod_sheet")
		special_tasks.generate_mod_sheet()
	if "user_sheet" in sys.argv:
		sys.argv.remove("user_sheet")
		special_tasks.generate_leaderboard_sheet()

else:
	for arg in sys.argv[1:]:
		utils.process_task_group(arg)

print("Done")