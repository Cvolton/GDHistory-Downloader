import utils
import server_parsers

def get_id_range_task(start, finish):
	print(f"[{start}/{finish}]")
	ids = []
	end = finish if finish < (start+100) else start+100
	for i in range(start, end):
		ids.append(str(i))
	if not ids:
		return
	request_str = ",".join(ids)
	response_text = utils.save_request('getGJLevels21', {"type": 19, "str": request_str} )

	new_start = 0
	if response_text is not False:
		last_level = server_parsers.response_to_dict(response_text.split('#')[0].split('|')[-1], ':')
		new_start = int(last_level[1]) + 1
	else:
		new_start = end
	get_id_range_task(new_start, finish)