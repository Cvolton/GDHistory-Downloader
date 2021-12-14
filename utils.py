import json
import os
import requests

from dotenv import load_dotenv

def get_data_path():
	load_dotenv()

	return os.getenv('DATA_PATH', 'data')

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

	return response.text

def process_task_group(id):
	data_path = get_data_path()

	directory = f"{data_path}/TaskGroups/{id}"

	for filename in os.listdir(directory):
		with open(f"{directory}/{filename}", "r") as json_file:
			task = json.load(json_file)

			print(task)

			response = send_request(task['endpoint'], task['parameters'])

			print(response)