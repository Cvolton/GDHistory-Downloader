import hashlib
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

def find_recent_account_comments():
	timestamps = []
    
	upload_params = {
		"cType": 1,
		"comment": "Q3ZvbHRvbiBHTUQgdGVzdA=="
	}
 
	data_path = utils.get_data_path()
	filename = f"{data_path}/account_comment_estimator_accounts.json"
	with open(filename, "r") as input_file:
		account_ids = json.load(input_file)
		for account_id, values in account_ids.items():
			upload_params["accountID"] = account_id
			upload_params["gjp2"] = values["gjp2"]
			upload_params["userName"] = values["userName"]
			chk = f"{upload_params['userName']}{upload_params['comment']}001"
			chk_salt = "xPT6iUrtws0J"
			hl = hashlib.sha1()
			hl.update(f"{chk}{chk_salt}".encode('utf-8'))
			chk_sha1 = hl.hexdigest()
			upload_params["chk"] = server_parsers.robtop_xor(chk_sha1, "29481")
			response = utils.save_request('uploadGJAccComment20', upload_params)
			estimation_created = str(datetime.now(pytz.utc))
			if response: 
				timestamps.append({
					"level_id": account_id,
					"comment_id": response,
					"timestamp": "0 years ago",
					"estimation_created": estimation_created,
					"type": "account"
				})
    
				delete_res = None
				i = 0
				while not delete_res and i < 20:
					delete_params = {
						**values,
						"accountID": account_id,
						"commentID": response,
						"targetAccountID": account_id
					}
					delete_res = utils.save_request('deleteGJAccComment20', delete_params)
					i += 1

	print(timestamps)
	json_set = {
		'endpoint': "GDHistory-Special",
		'task': "find_new_comments",
		'dates': timestamps
	}

	data_path = utils.get_data_path()
	filename = f"new_acc_comments_{datetime.now()}.json"

	with open(f"{data_path}/Output/{filename}", "w") as output_file:
		json.dump(json_set, output_file)

def find_recent_comments():
	request_delay = utils.get_request_delay()
	
	#Step 0: define ID ranges
	# range start : best level
	ranges = {
		0: 13519,
		170001: 341613,
		3200001: 10565740,
		29550001: 34085027,
		35000001: 43908596,
		53000001: 56199846,
		-2: 57436521,
		63214001: 72956745,
		81395001: 89886591,
		90000001: 90475473,
		100000001: 104187415,
		110000001: 119544028,
  		124421501: 126242564
	}
	
	timestamps = []
 
	bests = list(ranges.values())
	#TODO: check current daily

	#Step 1: load comments for each best level
	for best in bests:
		print(f"Loading comments for level {best}")
		response_text = utils.save_request('getGJComments21', {"levelID": best, "count": 100, "mode": 0, "page": 0} )
		estimation_created = str(datetime.now(pytz.utc))
		all_comments = response_text.split('|')
		for comment in all_comments:
			comment_info = server_parsers.response_to_dict(comment.split(':')[0], '~')
			timestamp = comment_info[9]
			if not "seconds" in timestamp and not "minutes" in timestamp: continue
			timestamps.append({
				"level_id": best,
				"comment_id": int(comment_info[6]),
				"timestamp": timestamp,
				"estimation_created": estimation_created
			})
		
	json_set = {
		'endpoint': "GDHistory-Special",
		'task': "find_new_comments",
		'dates': timestamps
	}

	data_path = utils.get_data_path()
	filename = f"new_comments_{datetime.now()}.json"

	with open(f"{data_path}/Output/{filename}", "w") as output_file:
		json.dump(json_set, output_file)

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

def generate_lists_megaresponse():
	page = 0

	all_parts = {}

	while True:
		print(f"Page {page}")
		response_text = utils.save_request('getGJLevelLists', {"type": 4, "star": 1, "page": page, "count": 2000} )

		if response_text is None or response_text == False:
			break

		if not response_text.startswith('1:'):
			continue

		parts = response_text.split('#')
		if len(parts) < 4:
			continue
			
		for i, part in enumerate(parts):
			if not i in all_parts:
				all_parts[i] = []
			all_parts[i].append(part)

		page = page + 1

	parts_json = {
		"content": "|".join(all_parts[0]) + "#" + "|".join(all_parts[1]) + "#9999:0:10#"
	}

	with open(utils.get_other_env_var("LISTS_MEGA_RESPONSE_FILE"), "w") as output_file:
		json.dump(parts_json, output_file)


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

def find_valid_udids():
	print("- Starting UDID job")
	with open(utils.get_other_env_var("UDID_FILE"), "r") as udid_file:
		udids = udid_file.read().split(";1 ")

	data_path = utils.get_data_path()
	with open(f"{data_path}/Output/udids_processed.txt", "r") as output_file:
		processed_udids = output_file.read().split("\n")

	udids = list(set(udids) - set(processed_udids))
	with open(f"{data_path}/Output/udids_processed.txt", "a") as output_file:
		print("- UDID job started")
		for udid in udids:
			response_text = utils.save_request('getGJScores20', {"udid": udid, "type": "relative"} )
			if response_text:
				output_file.write(f"{udid}\n")
				if response_text != "1:Thunu:2:1937634:13:43:17:33:6:1033354:9:28:10:12:11:10:14:1:15:2:16:3759046:3:501:52:161:8:0:46:629:4:4|1:ElgguZ:2:957286:13:52:17:37:6:1033355:9:98:10:37:11:11:14:0:15:2:16:3662740:3:501:52:559:8:0:46:536:4:1|1:RottenApple:2:1797243:13:47:17:81:6:1033356:9:3:10:12:11:3:14:5:15:0:16:2768405:3:501:52:17:8:0:46:994:4:1|1:MrTurtle25:2:1358606:13:50:17:11:6:1033357:9:22:10:15:11:12:14:0:15:2:16:1777889:3:501:52:1:8:0:46:0:4:4|1:ojs4848:2:618709:13:80:17:13:6:1033358:9:93:10:14:11:12:14:0:15:0:16:1178653:3:501:52:0:8:0:46:10:4:15|1:arozo2:2:1768343:13:21:17:0:6:1033359:9:4:10:7:11:3:14:1:15:0:16:922600:3:501:52:0:8:0:46:0:4:2|1:Rafael5900:2:1015011:13:125:17:81:6:1033360:9:3:10:3:11:21:14:6:15:0:16:741879:3:501:52:105:8:0:46:1254:4:6|1:tfitzp2:2:2398585:13:46:17:0:6:1033361:9:40:10:5:11:14:14:0:15:1:16:667108:3:501:52:0:8:0:46:0:4:3|1:Aidovolcano:2:789234:13:65:17:11:6:1033362:9:49:10:9:11:12:14:0:15:2:16:593393:3:501:52:458:8:0:46:0:4:3|1:s820kt7r:2:2071030:13:55:17:163:6:1033363:9:97:10:3:11:12:14:0:15:0:16:189803:3:501:52:131:8:0:46:1479:4:0|1:proojw123:2:488513:13:54:17:26:6:1033364:9:4:10:9:11:12:14:1:15:2:16:111053:3:501:52:59:8:0:46:0:4:3|1:florian23232:2:1157410:13:45:17:65:6:1033365:9:31:10:15:11:25:14:1:15:2:16:104479:3:501:52:218:8:0:46:2248:4:2|1:lostwheel:2:2209359:13:55:17:2:6:1033366:9:3:10:12:11:15:14:5:15:2:16:70907:3:501:52:0:8:0:46:173:4:3|1:Carrotmaster:2:250705:13:69:17:15:6:1033367:9:1:10:0:11:3:14:0:15:0:16:81:3:501:52:483:8:0:46:255:4:1|":
					print(f"UDID {udid} IS VALID!!!")
					with open(f"{data_path}/Output/valid_udids.txt", "a") as valid_file:
						valid_file.write(f"{udid}\n")
					output_file.flush()
				else:
					print(f"UDID {udid} IS INVALID")
			else:
				print(f"Couldn't get response for UDID {udid}")
			time.sleep(utils.get_request_delay())
