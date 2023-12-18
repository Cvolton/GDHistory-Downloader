import utils
import server_parsers

import base64
import time
import math
import pytz
import json
from datetime import datetime

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

	dates = {
		recent_id: {
			"timestamp": f"0 years ago",
			"estimation_created": str(datetime.now(pytz.utc))
		}
	}

	#Step 2: find the level
	for i in range(0, years):
		lowest_point = 0
		highest_point = recent_id

		lowest_point_str = ""
		highest_point_str = ""

		last_lowest_point = -1
		last_highest_point = -1

		while last_lowest_point != lowest_point or last_highest_point != highest_point:
			level_id = lowest_point + math.floor((highest_point - lowest_point) / 2)

			response_text = False
			while response_text is False:
				ids = []
				for j in range(level_id, level_id+100):
					ids.append(str(j))
				if not ids:
					return

				request_str = ",".join(ids)
				response_text = utils.save_request('getGJLevels21', {"type": 19, "str": request_str} )
				if response_text is False:
					level_id = level_id + 100

			first_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[0], ':')
			level_id = int(first_level[1])

			response_text = utils.save_request('downloadGJLevel22', {'levelID': level_id})
			full_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[0], ':')
			date = full_level[28]

			print(level_id)
			print(date)

			last_lowest_point = lowest_point
			last_highest_point = highest_point

			if "year" not in date:
				date = "0 years"

			if int(date.split(' ')[0]) > i:
				lowest_point = level_id
				lowest_point_str = date
			else:
				highest_point = level_id
				highest_point_str = date

			print(f"Searching: {i}\nLowest point: {lowest_point} ({lowest_point_str})\nHighest point: {highest_point} ({highest_point_str})")

		dates[lowest_point] = {
			"timestamp": f"{i+1} years ago",
			"estimation_created": str(datetime.now(pytz.utc))
		}
		

	print(dates)

	json_set = {
		'endpoint': "GDHistory-Special",
		'task': "find_cutoffs",
		'dates': dates
	}

	data_path = utils.get_data_path()
	filename = f"ids_{datetime.now()}.json"

	with open(f"{data_path}/Output/{filename}", "w") as output_file:
		json.dump(json_set, output_file)

def generate_rated_sheet():
	page = 0
	print("levelID,levelName,description,version,userID,rating,ratingSum,difficulty name,downloads,audioTrack,gameVersion,likes,length,demon,stars,featureScore,auto,original,twoPlayer,customSong,coins,verifiedCoins,starsRequested,epic,demonDifficulty,objects")
	while True:
		response_text = utils.save_request('getGJLevels21', {"type": 4, "star": 1, "page": page} )

		if response_text is None:
			break

		if not response_text.startswith('1:'):
			continue

		levels = response_text.split('#')[0].split('|')
		for level in levels:
			data = server_parsers.response_to_dict(level, ":")
			print(f"{data[1]},{data[2]},\"{data[3]}\",{data[5]},{data[6]},{data[8]},{data[9]},{data[10]},{data[12]},{data[13]},{data[14]},{data[15]},{data[17]},{data[18]},{data[19]},{data[25]},{data[30]},{data[31]},{data[35]},{data[37]},{data[38]},{data[39]},{data[42]},{data[43]},{data[45]}")

		page = page + 1

def generate_leaderboard_sheet():
	account_id = 4759274
	#1:ViPriN:2:1078150:13:150:17:3556:6:1165:9:8:10:8:11:39:14:7:15:2:16:2795:3:33535:52:18:8:281:46:31198:4:1123:7:2795
	print("username,userID,coins,userCoins,rank,icon,col1,col2,iconType,special,accountID,stars,moons,cp,diamonds,demons,udid")
	while True:
		response_text = utils.save_request('getGJScores20', {"type": "relative", "count": 100, "accountID": account_id, "udid": "amongus"} )
		previous_account_id = account_id

		if response_text is None:
			break

		if not response_text.startswith('1:'):
			continue

		users = response_text.split('#')[0].split('|')
		for user in users:
			data = server_parsers.response_to_dict(user, ":")
			if data:
				print(f"{data[1]},{data[2]},\"{data[13]}\",{data[17]},{data[6]},{data[9]},{data[10]},{data[11]},{data[14]},{data[15]},{data[16]},{data[3]},{data[52]},{data[8]},{data[46]},{data[4]},{data[7] if 7 in data else None}")
				account_id = data[16]

		if account_id == previous_account_id: break


def do_mod_sheet_pass(params, dont_switch=False):
	page = 0
	sheet_text = "levelID,levelName,description,version,userID,rating,ratingSum,downloads,audioTrack,gameVersion,likes,length,demon,stars,featureScore,auto,original,twoPlayer,customSong,coins,verifiedCoins,starsRequested,epic,demonDifficulty,objects"
	while True:
		page_object = {"page": page}
		final_params = params | page_object

		response_text = utils.save_request('getGJLevels21', final_params)

		if not response_text:
			break

		if not response_text.startswith('1:'):
			continue

		levels = response_text.split('#')[0].split('|')
		for level in levels:
			data = server_parsers.response_to_dict(level, ":")
			sheet_text = (f"{sheet_text}\n{data[1]},{data[2]},\"{data[3]}\",{data[5]},{data[6]},{data[8]},{data[9]},{data[10]},{data[12]},{data[13]},{data[14]},{data[15]},{data[17]},{data[18]},{data[19]},{data[25]},{data[30]},{data[31]},{data[35]},{data[37]},{data[38]},{data[39]},{data[42]},{data[43]},{data[45]}")

		print(f"Loaded {final_params}")

		page = page + 1

		if dont_switch:
			break

	return sheet_text

def save_sheet(filename, sheet_pass):
	data_path = utils.get_data_path()
	with open(f"{data_path}/{filename}", "w") as output_file:
		output_file.write(sheet_pass)

def save_pass(filename, params, dont_switch=False):
	save_sheet(filename, do_mod_sheet_pass(params, dont_switch))

def generate_mod_sheet():
	"""save_pass("mod_-3_nostar.csv", {"type": 8, "star": 0, "diff": -3, "accountID": 71})
	#save_pass("mod_-3_star.csv", {"type": 8, "star": 1, "diff": -3, "accountID": 71})
	save_pass("mod_-2_nostar.csv", {"type": 8, "star": 0, "diff": -2, "accountID": 71})
	#save_pass("mod_-2_star.csv", {"type": 8, "star": 1, "diff": -2, "accountID": 71})
	save_pass("mod_-1_nostar.csv", {"type": 8, "star": 0, "diff": -1, "accountID": 71})
	#save_pass("mod_-1_star.csv", {"type": 8, "star": 1, "diff": -1, "accountID": 71})
	save_pass("mod_nostar.csv", {"type": 8, "star": 0, "accountID": 71})
	save_pass("mod_star.csv", {"type": 8, "star": 1, "accountID": 71})"""
	#save_pass("type24.csv", {"type": 24}, True)
	save_pass("gdw_featured.csv", {"type": 17})