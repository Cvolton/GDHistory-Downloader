import sys
import json
import utils

comment_json_filename = sys.argv[1] if len(sys.argv) > 1 else f"comments_by_date_updated.json"

with open(f"{utils.get_data_path()}/{comment_json_filename}.json", "r") as f:
    all_comments = json.loads(f.read())
    
all_comments_flattened = {}
all_comments_remaster = {}
for date_bracket, comments in all_comments.items():
    for comment_id, comment in comments.items():
        all_comments_flattened[comment_id] = comment
        
for comment_id, comment in all_comments_flattened.items():
    date = comment["9"]
    if int(date.split(' ')[0]) > 2000:
        continue
    if "year" not in date:
        date = "0 years ago"
    if not all_comments_remaster.get(date):
        all_comments_remaster[date] = {}
    all_comments_remaster[date][comment_id] = comment
    
with open(f"{utils.get_data_path()}/{comment_json_filename}.json", "w") as f:
    json.dump(all_comments_remaster, f)