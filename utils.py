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

def send_request(endpoint, data):
	data_path = get_data_path()

	mandatory_data = {
		"gameVersion": "21",
		"binaryVersion": "35",
		"gdw": "0",
		"secret": "Wmfd2893gb7"
	}

	data |= mandatory_data 

	headers = {'User-Agent': ''}

	response = requests.post(f"http://www.boomlings.com/database/{endpoint}.php", data=data, headers=headers)

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