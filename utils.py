import json
import os
import requests
import time

from dotenv import load_dotenv
from datetime import datetime

class RequestResult:
	def __init__(self, request_data, response_text, endpoint):
		self.request_data = request_data
		self.response_text = response_text
		self.endpoint = endpoint
		self.created = datetime.now()

def get_data_path():
	load_dotenv()

	return os.getenv('DATA_PATH', 'data')

def get_request_delay():
	load_dotenv()

	return int(os.getenv('REQUEST_DELAY', 5))

def get_source_interface():
	load_dotenv()

	return os.getenv('SOURCE_INTERFACE', False)

#adapted from https://stackoverflow.com/questions/48996494/send-http-request-through-specific-network-interface
def session_for_src_addr(addr: str) -> requests.Session:
	"""
	Create `Session` which will bind to the specified local address
	rather than auto-selecting it.
	"""
	session = requests.Session()
	for prefix in ('http://', 'https://'):
		session.get_adapter(prefix).init_poolmanager(
			# those are default values from HTTPAdapter's constructor
			connections=requests.adapters.DEFAULT_POOLSIZE,
			maxsize=requests.adapters.DEFAULT_POOLSIZE,
			# This should be a tuple of (address, port). Port 0 means auto-selection.
			source_address=(addr, 0),
		)

	return session

def send_request(endpoint, data):
	data_path = get_data_path()
	session = session_for_src_addr(get_source_interface())

	mandatory_data = {
		"gameVersion": "21",
		"binaryVersion": "35",
		"gdw": "0",
		"secret": "Wmfd2893gb7"
	}

	data |= mandatory_data 

	headers = {'User-Agent': ''}

	response = session.post(f"http://www.boomlings.com/database/{endpoint}.php", data=data, headers=headers)

	return RequestResult(data, response.text, endpoint)

def process_task_group(id):
	data_path = get_data_path()
	request_delay = get_request_delay()

	directory = f"{data_path}/TaskGroups/{id}"

	for filename in os.listdir(directory):
		print(f"Processing task {filename}")
		with open(f"{directory}/{filename}", "r") as json_file:
			task = json.load(json_file)

			print(task)

			if 'startingPage' in task and 'endingPage' in task:
				for i in range(task['startingPage'], task['endingPage']):
					print(f"Page {i}")
					response = save_request(task['endpoint'], task['parameters'] | {"page": i} )
					if response is False:
						print("done")
						break
					time.sleep(request_delay)
			elif 'levelList' in task:
				for levelID in task['levelList']:
					print(f"levelID {levelID}")
					response = save_request(task['endpoint'], task['parameters'] | {"levelID": levelID} )
			else:
				response = save_request(task['endpoint'], task['parameters'])

def create_output_file(request_result):
	data_path = get_data_path()

	response_json = {
		"created": str(request_result.created),
		"unprocessed_post_parameters": request_result.request_data,
		"endpoint": request_result.endpoint,
		"raw_output": request_result.response_text
	}

	filename = f"{str(request_result.created)}.json"

	with open(f"{data_path}/Output/{filename}", "w") as output_file:
		json.dump(response_json, output_file)

	#print(response_json)

def save_request(endpoint, data):
	response = send_request(endpoint, data)
	create_output_file(response)
	return response.response_text[:2] != '-1'