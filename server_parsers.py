import base64

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

def robtop_xor(string, key):
    key = str(key)
    data = bytearray(string.encode('windows-1252'))
    for i in range(len(data)):
        data[i] ^= ord(key[i % len(key)])
    return base64.b64encode(data, altchars=b'-_').decode('utf-8')
