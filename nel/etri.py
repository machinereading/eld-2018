import json
import pprint
import socket
import struct
from functools import reduce
from nel.crowdsourcing_preprocessor import candidates
from nel.dataset_changer import change_to_conll, change_to_tsv

def getETRI(text):
	# print(text)
	host = '143.248.135.146'
	port = 33344
	
	ADDR = (host, port)
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		clientSocket.connect(ADDR)
	except Exception as e:
		return None
	try:
		clientSocket.sendall(str.encode(text))
		#clientSocket.sendall(text.encode('unicode-escape'))
		#clientSocket.sendall(text.encode('utf-8'))
		buffer = bytearray()
		while True:
			data = clientSocket.recv(1024)
			if not data:
				break
			buffer.extend(data)
		result = json.loads(buffer.decode(encoding='utf-8'))

		return result
	except Exception as e:
		return None

def find_ne_pos(j):
	def find_in_wsd(wsd, ind):
		for item in wsd:
			if item["begin"] == ind or item["end"] == ind:
				return item
		# print(wsd)
		raise IndexError(ind)
	original_text = reduce(lambda x, y: x+y, list(map(lambda z: z["text"], j["sentence"])))
	# print(original_text)
	j["NE"] = []
	try:
		for v in j["sentence"]:
			sentence = v["text"]
			# for morph in v["WSD"]:
			# 	charind = lastcharind
			# 	byteind = lastbyteind
			# 	for char in sentence[lastcharind:]:
			# 		if byteind == morph["position"]:
			# 			lastcharind = charind
			# 			lastbyteind = byteind
			# 			morph["charind"] = charind
			# 			break
			# 		print(char, byteind)
			# 		byteind += len(char.encode())

			# 		charind += 1
			# 	if charind != lastcharind:
			# 		raise Exception("No position found")
			# print(len(v["NE"]))
			for ne in v["NE"]:
				morph_start = find_in_wsd(v["WSD"],ne["begin"])
				# morph_end = find_in_wsd(v["WSD"],ne["end"])
				byte_start = morph_start["position"]
				# print(ne["text"], byte_start)
				# byte_end = morph_end["position"]+sum(list(map(lambda char: len(char.encode()), morph_end["text"])))
				byteind = 0
				charind = 0
				for char in original_text:
					if byteind == byte_start:
						ne["char_start"] = charind
						ne["char_end"] = charind + len(ne["text"])
						j["NE"].append(ne)
						break
					byteind += len(char.encode())
					charind += 1
				else:
					raise Exception("No char pos found: %s" % ne["text"])
			j["original_text"] = original_text
	except Exception:
		return None
	# print(len(j["NE"]))
	return j

def etri_ne_pos(j):
	def find_in_wsd(wsd, ind):
		for item in wsd:
			if item["begin"] == ind or item["end"] == ind:
				return item
		# print(wsd)
		raise IndexError(ind)

	original_text = reduce(lambda x, y: x+y, list(map(lambda z: z["text"], j["sentences"])))
	# print(original_text)
	j["NE"] = []
	try:
		for v in j["sentences"]:
			sentence = v["text"]
			for ne in v["NE"]:
				morph_start = find_in_wsd(v["WSD"],ne["begin"])
				# morph_end = find_in_wsd(v["WSD"],ne["end"])
				byte_start = morph_start["position"]
				# print(ne["text"], byte_start)
				# byte_end = morph_end["position"]+sum(list(map(lambda char: len(char.encode()), morph_end["text"])))
				byteind = 0
				charind = 0
				for char in original_text:
					if byteind == byte_start:
						ne["char_start"] = charind
						ne["char_end"] = charind + len(ne["text"])
						j["NE"].append(ne)
						break
					byteind += len(char.encode())
					charind += 1
				else:
					raise Exception("No char pos found: %s" % ne["text"])
			j["original_text"] = original_text
	except Exception:
		return None
	# print(len(j["NE"]))
	return j

def is_not_korean(char):
	return not (0xAC00 <= ord(char) <= 0xD7A3)

def change_into_crowdsourcing_form(_arg=None, text=None, file=None):
	if _arg is not None or not ((text is None) ^ (file is None)):
		raise Exception
	print("in ETRI")
	if text:
		if type(text) is str:
			text = [text]
	else:
		text = []
		for line in file.readlines():
			text.append(line.strip())
	result = []
	ind = 0
	print("start for loop")
	for t in text:
		j = find_ne_pos(getETRI(t))
		if j is None:
			print(t)
			continue
		cs_form = {}
		cs_form["text"] = j["original_text"]
		cs_form["entities"] = []
		cs_form["fileName"] = "%d" % ind
		for item in j["NE"]:
			skip_flag = False
			for prefix in ["QT", "DT"]:
				if item["type"].startswith(prefix): skip_flag = True
			if item["type"] in ["CV_RELATION", "TM_DIRECTION"] or skip_flag: continue
			
			if all(list(map(is_not_korean, item["text"]))): continue

			cs_form["entities"].append({
				"text": item["text"],
				"candidates": candidates(item["text"]),
				"keyword": "NOT_IN_CANDIDATE",
				"start_offset": item["char_start"],
				"end_offset": item["char_end"],
				"ne_type": item["type"], 
				"type": "ETRI"
				})
		result.append(cs_form)
		ind += 1
	return result

def etri_into_crowdsourcing_form(data):

	result = []
	ind = 0
	data = [
		{
			"sentences": data
		}
	]
	for d in data:
		j = etri_ne_pos(d)
		if j is None:
			print(d)
			continue
		cs_form = {}
		cs_form["text"] = j["original_text"]
		cs_form["entities"] = []
		cs_form["fileName"] = "%d" % ind
		for item in j["NE"]:
			skip_flag = False
			for prefix in ["QT", "DT"]:
				if item["type"].startswith(prefix): skip_flag = True
			if item["type"] in ["CV_RELATION", "TM_DIRECTION"] or skip_flag: continue
			
			if all(list(map(is_not_korean, item["text"]))): continue

			cs_form["entities"].append({
				"text": item["text"],
				"candidates": candidates(item["text"]),
				"keyword": "NOT_IN_CANDIDATE",
				"start_offset": item["char_start"],
				"end_offset": item["char_end"],
				"ne_type": item["type"], 
				"type": "ETRI"
				})
		result.append(cs_form)
		ind += 1
	return result


def make_text_into_conll(text):
	r = change_into_crowdsourcing_form(text=text)
	# with open("tta.json", "w", encoding="UTF8") as jf:
	# 	json.dump(r, jf, ensure_ascii=False, indent="\t")
	with open("data/generated/test_train_data/tta.conll", "w", encoding="UTF8") as conllf, open("data/generated/test_train_data/tta.tsv", "w", encoding="UTF8") as tsvf:
		for item in r:
			conllf.write(change_to_conll(item)+"\n\n")
			for cand in change_to_tsv(item):
				tsvf.write(cand+"\n")

	return r


def etri_into_conll(data):
	r = etri_into_crowdsourcing_form(data)
	# with open("tta.json", "w", encoding="UTF8") as jf:
	# 	json.dump(r, jf, ensure_ascii=False, indent="\t")
	with open("data/generated/test_train_data/tta.conll", "w", encoding="UTF8") as conllf, open("data/generated/test_train_data/tta.tsv", "w", encoding="UTF8") as tsvf:
		for item in r:
			conllf.write(change_to_conll(item)+"\n\n")
			for cand in change_to_tsv(item):
				tsvf.write(cand+"\n")

	return r


def main():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("--text", type=str)
	parser.add_argument("--file", type=str)
	args = parser.parse_args()

	if args.text is not None:
		r = change_into_crowdsourcing_form(text=args.text)
		with open("data/generated/test_train_data/tta.conll", "w", encoding="UTF8") as conllf, open("data/generated/test_train_data/tta.tsv", "w", encoding="UTF8") as tsvf:
			for item in r:
				conllf.write(change_to_conll(item)+"\n\n")
				for cand in change_to_tsv(item):
					tsvf.write(cand+"\n")
	print("ETRI module")
	with open("tta_plain.txt", encoding="UTF8") as f:
		r = change_into_crowdsourcing_form(file=f)
	print("writing file")
	with open("tta.json", "w", encoding="UTF8") as jf:
		json.dump(r, jf, ensure_ascii=False, indent="\t")
	with open("data/generated/test_train_data/tta.conll", "w", encoding="UTF8") as conllf, open("data/generated/test_train_data/tta.tsv", "w", encoding="UTF8") as tsvf:
		for item in r:
			conllf.write(change_to_conll(item)+"\n\n")
			for cand in change_to_tsv(item):
				tsvf.write(cand+"\n")


# main()
# x = find_ne_pos(getETRI("스티브 잡스는 애플의 창업자이다. 스티브 잡스는 미국에서 태어났다."))
# print(x["sentence"][0]["NE"])
# with open("a.json", "w", encoding="utf-8") as f:
# 	json.dump(x, f, ensure_ascii=False, indent="\t")
