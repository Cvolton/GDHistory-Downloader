import utils
import json
import pytz
import server_parsers
from datetime import datetime

def find_recent_account_comments():
    data_path = utils.get_data_path()

    with open(f"{data_path}/friend_request_estimator_timestamps.json", "r") as input_file:
        known_timestamps = json.load(input_file)

    timestamps = []
    
    upload_params = {
        "count": 10000
    }
 
    filename = f"{data_path}/friend_request_estimator_accounts.json"
    with open(filename, "r") as input_file:
        account_ids = json.load(input_file)
    for account_id, values in account_ids.items():
        upload_params["accountID"] = account_id
        upload_params["gjp2"] = values["gjp2"]
        for i in range(0,2):
            upload_params["getSent"] = i
            response = utils.save_request('getGJFriendRequests20', upload_params)
            estimation_created = str(datetime.now(pytz.utc))
            if response:
                response_data = response.split('#')[0].split('|')
                for request in response_data:
                    info = server_parsers.response_to_dict(request, ':')
                    if 37 not in info or 32 not in info: continue
                    if info[32] not in known_timestamps or known_timestamps[info[32]] != info[37]:
                        timestamps.append({
                            "level_id": 0,
                            "comment_id": int(info[32]),
                            "timestamp": info[37],
                            "estimation_created": str(estimation_created),
                            "type": "friend_request"
                        })

                    known_timestamps[info[32]] = info[37]
    with open(f"{data_path}/friend_request_estimator_timestamps.json", "w") as output_file:
        json.dump(known_timestamps, output_file)
    if timestamps:
        json_set = {
            'endpoint': "GDHistory-Special",
            'task': "find_new_comments",
            'dates': timestamps
        }
        filename = f"new_friend_requests_{datetime.now()}.json"

        print(timestamps)
        with open(f"{data_path}/Output/{filename}", "w") as output_file:
            json.dump(json_set, output_file)

find_recent_account_comments()