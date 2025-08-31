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
        min_comment_id = current_res[0][0][6] if 6 in current_res[0][0] else None
        max_comment_id = current_res[0][-1][6] if 6 in current_res[0][-1] else None
        if min_comment_id is None or max_comment_id is None:
            return None

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

def load_all_oldests():
    for key in all_comments.keys():
        first_comment, first_comment_time = load_oldest_for_year(key)
        oldests[key] = (first_comment, first_comment_time)

    print(oldests)
    
oldests = {'3 years': ({2: 'R0chIDop', 3: '145380463', 4: '0', 7: '0', 10: '100', 9: '4 years', 6: '6654481'}, datetime(2025, 8, 31, 18, 42, 8, 43156, tzinfo=pytz.UTC)), 
           '2 years': ({2: 'bWl0aWNv', 3: '128978495', 4: '0', 7: '0', 10: '100', 9: '3 years', 6: '7361281'}, datetime(2025, 8, 31, 18, 46, 54, 548574, tzinfo=pytz.UTC)), 
           '4 years': ({2: 'SSBhYnNvbHV0ZWx5IGxvdmUgdGhlc2Ugb2xkICdnb29kJyBsZXZlbHMuIFRoZXNlIGNoYWxsZW5nZSB5b3VyIGJyYWluIGFuZCBhcmUgYWJzb2x1dGVseSBmdW4u', 3: '61751004', 4: '3', 7: '0', 10: '100', 9: '5 years', 6: '5849308'}, datetime(2025, 8, 31, 18, 49, 43, 345631, tzinfo=pytz.UTC)), 
           '7 years': ({2: 'RXo=', 3: '16267539', 4: '2', 7: '0', 10: '100', 9: '8 years', 6: '3734008'}, datetime(2025, 8, 31, 18, 50, 58, 383428, tzinfo=pytz.UTC)), 
           '8 years': ({2: 'aSBhZ3JlZQ==', 3: '19395079', 4: '0', 7: '0', 10: '0', 9: '9 years', 6: '2715694'}, datetime(2025, 8, 31, 18, 51, 51, 969094, tzinfo=pytz.UTC)), 
           '1 year': ({2: 'Y2FuIHdlIGtlZXAgdGhpcyBoYXJkIGRlbW9uPyBJIHdhbnQgdGhpcyB0byBiZSBteSBmaXJzdCA8Mw==', 3: '189664795', 4: '2', 7: '0', 10: '32', 9: '2 years', 6: '8067748'}, datetime(2025, 8, 31, 18, 57, 23, 855649, tzinfo=pytz.UTC)), 
           '11 years': (None, None), 
           '0 years ago': ({2: 'V0hZIFRFQU0gSEFYPjpbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbW1tbWyEhIQ==', 3: '253719506', 4: '0', 7: '0', 10: '64', 9: '1 year', 6: '9122342'}, datetime(2025, 8, 31, 19, 8, 29, 442247, tzinfo=pytz.UTC)), 
           '5 years': ({2: 'dGhlIG5hbWUgb2YgdGhpcyBsZXZlbCBpcyBob3cgbWFueSBhdHRlbXB0cyBJIHRvb2sgdG8gYmVhdCBpdA==', 3: '4986346', 4: '1', 7: '0', 10: '100', 9: '6 years', 6: '5138924'}, datetime(2025, 8, 31, 19, 15, 46, 38615, tzinfo=pytz.UTC)), 
           '9 years': ({2: 'dGhlIG9ubHkgc2ltaWxhcml0eSBvbiBkaXMgbGV2ZWwgdG8gYmFjayBpbiB0cmFjayBpcyB0aGUgbXVzaWMg', 3: '7280327', 4: '0', 7: '0', 10: '0', 9: '10 years', 6: '1480143'}, datetime(2025, 8, 31, 19, 17, 36, 771404, tzinfo=pytz.UTC)), 
           '6 years': ({2: 'dGltZSBhIHQgdCBhIGMgYw==', 3: '41487068', 4: '2', 7: '0', 10: '100', 9: '7 years', 6: '4502984'}, datetime(2025, 8, 31, 19, 21, 13, 158930, tzinfo=pytz.UTC)), 
           '10 years': (None, None)}

print(oldests)

def convert_oldests_to_record():
    timestamps = []
    for oldest in oldests:
        new_comment = oldests[oldest][0]
        if not new_comment: continue
        original_comment = all_comments[oldest][new_comment[6]]
        timestamps.append({
            "level_id": original_comment["1"],
            "comment_id": int(new_comment[6]),
            "timestamp": new_comment[9],
            "estimation_created": str(oldests[oldest][1])
        })
        
    json_set = {
        'endpoint': "GDHistory-Special",
        'task': "find_new_comments",
        'dates': timestamps
    }
    
    data_path = utils.get_data_path()
    filename = f"old_comments_{datetime.now()}.json"

    with open(f"{data_path}/Output/{filename}", "w") as output_file:
        json.dump(json_set, output_file)
        
convert_oldests_to_record()