import json
import os
import sys
from server_parsers import response_to_dict
import utils

comment_json_filename = sys.argv[1] if len(sys.argv) > 1 else f"comments_by_date_updated.json"

def generate_comment_json():
    all_comments = {}
    comments_by_date = {}
    location = f"{utils.get_data_path()}/Output/"
    for filename in os.listdir(location):
        if filename.endswith(".json"):
            with open(os.path.join(location, filename), "r") as f:
                data = json.load(f)
                if data["endpoint"] != "getGJComments21": continue
                comments = data["raw_output"].split('#')[0].split('|')
                for comment in comments:
                    comment_data = response_to_dict(comment.split(':')[0], '~')
                    if not comment_data: continue
                    if not 6 in comment_data: continue
                    if not 9 in comment_data: continue
                    if comment_data[6] in (13519,55520,61757): continue
                    comment_data[1] = data["unprocessed_post_parameters"]["levelID"]
                    all_comments[int(comment_data[6])] = comment_data
                    parsed_date = comment_data[9] if "year" in comment_data[9] else "0 years ago"
                    comments_by_date.setdefault(parsed_date, {})[int(comment_data[6])] = comment_data
    return all_comments, comments_by_date

def save_comment_json():
    comment_json = generate_comment_json()
    with open(f"{utils.get_data_path()}/all_comments_{comment_json_filename}.json", "w") as f:
        json.dump(comment_json[0], f)

    with open(f"{utils.get_data_path()}/{comment_json_filename}.json", "w") as f:
        json.dump(comment_json[1], f)

    print_all_lengths_for_by_date(comment_json)

def print_all_lengths_for_by_date(comment_json):
    for date, comments in comment_json[1].items():
        print(f"Date: {date}, Number of Comments: {len(comments)}")

save_comment_json()