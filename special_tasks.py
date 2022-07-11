import utils
import server_parsers

import time
import math

def get_id_range_task(start, finish):
	while True:
		request_delay = utils.get_request_delay()
		print(f"[{start}/{finish}]")
		ids = []
		end = finish if finish < (start+100) else start+100
		for i in range(start, end):
			ids.append(str(i))
		if not ids:
			return
		request_str = ",".join(ids)
		response_text = utils.save_request('getGJLevels21', {"type": 19, "str": request_str} )

		if response_text is not False:
			last_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[-1], ':')
			start = int(last_level[1]) + 1
		else:
			start = end
		time.sleep(request_delay)

def find_cutoffs_for_today():
	request_delay = utils.get_request_delay()

	#Step 0: get the amount of years to look for
	response_text = utils.save_request('downloadGJLevel22', {'levelID': 128})
	full_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[0], ':')
	date = full_level[28]
	years = int(date.split(' ')[0])
	print(years)

	#Step 1: get most recent level ID
	response_text = utils.save_request('getGJLevels21', {"type": 4} )
	first_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[0], ':')
	recent_id = int(first_level[1])

	response_text = utils.save_request('downloadGJLevel22', {'levelID': recent_id})
	full_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[0], ':')
	date = full_level[28]

	#Step 2: find the level
	for i in range(1, years+1):
		lowest_point = 0
		highest_point = recent_id

		lowest_point_str = ""
		highest_point_str = ""

		while True:
			level_id = lowest_point + math.floor((highest_point - lowest_point) / 2)

			ids = []
			for i in range(level_id, level_id+100):
				ids.append(str(i))
			if not ids:
				return

			request_str = ",".join(ids)
			response_text = utils.save_request('getGJLevels21', {"type": 19, "str": request_str} )
			first_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[0], ':')
			level_id = int(first_level[1])

			response_text = utils.save_request('downloadGJLevel22', {'levelID': level_id})
			full_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[0], ':')
			date = full_level[28]

			print(level_id)
			print(date)

			if "years" not in date:
				highest_point = level_id
				highest_point_str = date
			elif int(date.split(' ')[0]) > i:
				highest_point = level_id
				highest_point_str = date
			else:
				lowest_point = level_id
				lowest_point_str = date

			print(f"Lowest point: {lowest_point} ({lowest_point_str})\nHighest point: {highest_point} ({highest_point_str})")