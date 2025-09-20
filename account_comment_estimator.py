import json
import sys
import pytz
import utils
import os
from server_parsers import response_to_dict
from datetime import datetime

weeks_enabled = "--weeks" in sys.argv
months_enabled = "--months" in sys.argv or weeks_enabled
catchup_mode = "--catchup" in sys.argv

print(f"Weeks enabled: {weeks_enabled}, Months enabled: {months_enabled}, Catchup mode: {catchup_mode}")

sys.argv.remove("--weeks") if "--weeks" in sys.argv else None
sys.argv.remove("--months") if "--months" in sys.argv else None

comment_json_filename = sys.argv[1] if len(sys.argv) > 1 else f"comments_by_date_updated.json"

with open(f"{utils.get_data_path()}/{comment_json_filename}.json", "r") as f:
    all_comments = json.loads(f.read())

## Triangulate year limit
def get_comments_for_level(level_id, page):
    count = 10000
    response_text = utils.save_request('getGJAccountComments20', {"count": count, "type": 0, "page": page, "accountID": level_id} )
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
    print(f"- Loading comment {requested_id} on level {level_id}")
    print("-- Loading page ...", end="")

    min_page = 0
    current_res = get_comments_for_level(level_id, 0)
    max_page = current_res[1] - 1
    mid_page = 0

    while min_page <= max_page:
        min_comment_id = current_res[0][0][6] if 6 in current_res[0][0] else None
        max_comment_id = current_res[0][-1][6] if 6 in current_res[0][-1] else None
        if min_comment_id is None or max_comment_id is None:
            return None
        
        if not min_comment_id.isnumeric() or not max_comment_id.isnumeric():
            return None

        if int(min_comment_id) <= int(requested_id) <= int(max_comment_id):
            for comment in current_res[0]:
                if int(comment[6]) == int(requested_id):
                    print("")
                    return comment
            return None
        elif int(min_comment_id) > int(requested_id):
            min_page = mid_page + 1
        else:
            max_page = mid_page - 1
        mid_page = (min_page + max_page) // 2
        print(f"\r-- Loading page {mid_page}... ({min_page}, {max_page})...", end="")
        current_res = get_comments_for_level(level_id, mid_page)

def next_year_index(year):
    count = int(year.split(" ")[0]) + 1
    return f"{count} year{'s' if count != 1 else ''}"

def load_oldest_for_year(year):
    print(f"\033[1mLoading oldests for year {year}\033[0m")
    comments = sorted(all_comments[year].items(), key=lambda item: int(item[0]))
    comments_copy = comments[:]
    
    last_comment_current_year = None
    first_comment_next_year = None
    first_comment_next_year_time = None
    
    while len(comments_copy) > 0:
        if catchup_mode:
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
        else:
            # load first comment in array
            first_comment = load_updated_comment(comments_copy[0][1])
            if not first_comment:
                comments_copy.pop(0)
                continue

            if (first_comment[9] == year) or ("year" not in first_comment[9] and not (months_enabled and "month" in first_comment[9]) and not (weeks_enabled and "week" in first_comment[9])):
                return first_comment_next_year, first_comment_next_year_time
            else:
                comments_copy.pop(0)
                first_comment_next_year = first_comment
                first_comment_next_year_time = datetime.now(pytz.utc)

        print("- Finished,", last_comment_current_year, first_comment_next_year, len(comments_copy))
    return first_comment_next_year, first_comment_next_year_time

oldests = {}

def load_all_oldests():
    for key in all_comments.keys():
        if key.startswith("202"): continue
        first_comment, first_comment_time = load_oldest_for_year(key)
        oldests[key] = (first_comment, first_comment_time)

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
            "estimation_created": str(oldests[oldest][1]),
            "type": "account"
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
        
def move_oldests():
    for oldest in oldests:
        new_comment = oldests[oldest][0]
        if not new_comment: continue
        new_comment_id = new_comment[6]
        if not new_comment_id: continue
        
        target_bracket = new_comment[9]
        if not target_bracket in all_comments:
            print(f"- Creating new bracket {target_bracket}")
            all_comments[target_bracket] = {}
        copy = [*all_comments[oldest].items()]
        for comment_id, comment in copy:
            if int(comment["6"]) <= int(new_comment_id):
                all_comments[target_bracket][comment["6"]] = comment
                del all_comments[oldest][comment["6"]]
                
def save_all_comments():
    with open(f"{utils.get_data_path()}/{comment_json_filename}.json", "w") as f:
        json.dump(all_comments, f)
        
def remove_comments_from_levels_with_most_comments():
    level_ids = {}
    for year in all_comments.keys():
        comments = all_comments[year]
        for comment in comments:
            level_id = comments[comment]["1"]
            if level_id not in level_ids:
                level_ids[level_id] = 0
            level_ids[level_id] += 1
    #sort level_ids
    level_ids = dict(sorted(level_ids.items(), key=lambda item: item[1], reverse=True))
    
    for year in all_comments.keys():
        comments = all_comments[year]
        for comment in list(comments):
            level_id = comments[comment]["1"]
            if level_ids[level_id] > 20000:
                del comments[comment]

def limit_all_comments():
    for year in all_comments.keys():
        comments = all_comments[year]
        comments = dict(sorted(comments.items(), key=lambda x: int(x[0])))
        comment_limit = 12000
        comment_step = 10000
        
        if "month" in year:
            comment_limit = comment_limit // 12
            comment_step = comment_step // 12
        elif "week" in year:
            comment_limit = comment_limit // 52
            comment_step = comment_step // 52
        
        if len(comments) > comment_limit:
            step = len(comments) // comment_step
            all_comments[year] = {k: comments[k] for i, k in enumerate(comments) if i % step == 0}
            print(f"- Limited {year} to {len(all_comments[year])} comments")

remove_comments_from_levels_with_most_comments()
limit_all_comments()
load_all_oldests()
convert_oldests_to_record()
move_oldests()
save_all_comments()