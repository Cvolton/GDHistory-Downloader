import sys
import json
import utils

comment_json_filename = sys.argv[1] if len(sys.argv) > 1 else f"comments_by_date_updated.json"

with open(f"{utils.get_data_path()}/{comment_json_filename}.json", "r") as f:
    all_comments = json.loads(f.read())

def bracket_to_number(bracket):
    parts = bracket.split(' ')
    number = int(parts[0])
    if len(parts) > 1:
        if parts[1].startswith('week'):
            number *= 7
        elif parts[1].startswith('month'):
            number *= 30
        elif parts[1].startswith('year'):
            number *= 365
    return number

def verify_brackets():
    sorted_all_comments = reversed(sorted(all_comments.items(), key=lambda item: bracket_to_number(item[0])))
    last_bracket_min = 0
    last_bracket_max = 0
    last_bracket = None

    for date_bracket, comments in sorted_all_comments:
        sorted_comments = sorted(comments.items(), key=lambda item: int(item[1]["6"]))
        
        if len(sorted_comments) > 0:
            current_bracket_min = int(sorted_comments[0][1]["6"])
            current_bracket_max = int(sorted_comments[-1][1]["6"])
        else:
            continue

        print(f"Bracket {date_bracket} has {len(sorted_comments)} comments, from {current_bracket_min} to {current_bracket_max}")
        # check for overlap
        if last_bracket_max >= current_bracket_min:
            print(f"Overlap detected between brackets {last_bracket_min}-{last_bracket_max} and {current_bracket_min}-{current_bracket_max}")
            # move everything thats >= current_bracket_min from the previous bracket to this one
            # copy comments.items() to avoid modifying the dict while iterating
            for comment_id, comment in [*all_comments[last_bracket].items()]:
                if int(comment["6"]) > current_bracket_min:
                    print(f" - Moving comment {comment['6']} from bracket {last_bracket} to {date_bracket}")
                    all_comments[date_bracket][comment_id] = comment
                    del all_comments[last_bracket][comment_id]

        last_bracket_min = current_bracket_min
        last_bracket_max = current_bracket_max
        last_bracket = date_bracket
        
verify_brackets()
print("-----------")
verify_brackets()

with open(f"{utils.get_data_path()}/{comment_json_filename}.json", "w") as f:
    json.dump(all_comments, f)