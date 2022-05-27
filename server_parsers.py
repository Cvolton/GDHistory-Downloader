def response_to_dict(response, separator):
	if response == "":
		return False

	result = {}
	i = 0
	last_key = 0
	for item in response.split(separator):
		if i % 2 == 0:
			last_key = int(item)
		else:
			result[last_key] = item
		i += 1
	return result