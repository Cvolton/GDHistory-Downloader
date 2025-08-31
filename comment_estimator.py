import json

import pytz
import utils
import os
from server_parsers import response_to_dict
from datetime import datetime

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
    with open(f"{utils.get_data_path()}/all_comments.json", "w") as f:
        json.dump(comment_json[0], f)

    with open(f"{utils.get_data_path()}/comments_by_date.json", "w") as f:
        json.dump(comment_json[1], f)

    print_all_lengths_for_by_date(comment_json)

def print_all_lengths_for_by_date(comment_json):
    for date, comments in comment_json[1].items():
        print(f"Date: {date}, Number of Comments: {len(comments)}")

#save_comment_json()
with open(f"{utils.get_data_path()}/comments_by_date.json", "r") as f:
    all_comments = json.loads(f.read())

## Triangulate year limit
def get_comments_for_level(level_id, page):
    count = 100
    response_text = utils.save_request('getGJComments21', {"count": count, "type": 0, "page": page, "levelID": level_id} )
    if not response_text: return response_text
    
    comments = []
    response_text_parts = response_text.split('#')
    if len(response_text_parts) < 2: return None
    raw_comments = response_text_parts[0].split('|')
    for comment in raw_comments:
        comments.append(response_to_dict(comment.split(':')[0], '~'))
        
    #remove all comments where 6 is not set
    comments = [c for c in comments if 6 in c]
    comments.sort(key=lambda x: int(x[6]))
    comments_total = int(response_text_parts[1].split(':')[0])
    page_count = (comments_total + count - 1) // count
    
    if len(comments) < 1: return None
    
    return comments, page_count

def load_updated_comment(comment_data):
    # load comments on level
    # bisect page to find page with comment id we need
    requested_id = comment_data["6"]
    level_id = comment_data["1"]

    min_page = 0
    current_res = get_comments_for_level(level_id, 0)
    max_page = current_res[1] - 1
    mid_page = 0

    while min_page <= max_page:
        min_comment_id = current_res[0][0][6]
        max_comment_id = current_res[0][-1][6]
        if min_comment_id <= requested_id <= max_comment_id:
            for comment in current_res[0]:
                if comment[6] == requested_id:
                    return comment
            return None
        elif min_comment_id > requested_id:
            min_page = mid_page + 1
        else:
            max_page = mid_page - 1
        mid_page = (min_page + max_page) // 2
        current_res = get_comments_for_level(level_id, mid_page)

def next_year_index(year):
    count = int(year.split(" ")[0]) + 1
    return f"{count} year{'s' if count != 1 else ''}"

def load_oldest_for_year(year):
    comments = sorted(all_comments[year].items())
    comments_copy = comments[:]
    
    last_comment_current_year = None
    first_comment_next_year = None
    first_comment_next_year_time = None
    
    while len(comments_copy) > 0:
        # load comment from middle of array
        mid_index = len(comments_copy) // 2

        # at the bottom we have oldest comments
        # at the top we have newest comments
        mid_comment = load_updated_comment(comments_copy[mid_index][1])
        if not mid_comment:
            comments_copy.pop(mid_index)
            continue
        
        if "year" not in mid_comment[9] or mid_comment[9] == year:
            comments_copy = comments_copy[:mid_index]
            last_comment_current_year = mid_comment
        else:
            comments_copy = comments_copy[mid_index + 1:]
            first_comment_next_year = mid_comment
            first_comment_next_year_time = datetime.now(pytz.utc)

        print("Loading,", last_comment_current_year, first_comment_next_year, len(comments_copy))
    return first_comment_next_year, first_comment_next_year_time

oldests = {}
for key in all_comments.keys():
    first_comment, first_comment_time = load_oldest_for_year(key)
    oldests[key] = (first_comment, first_comment_time)
    
print(oldests)