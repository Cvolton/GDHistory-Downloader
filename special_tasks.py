import utils
import server_parsers

import time

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