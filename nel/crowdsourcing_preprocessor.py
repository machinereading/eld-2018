import pickle
import pymysql
conn = pymysql.connect(host='kbox.kaist.ac.kr', port=3142, user='root', password='swrcswrc',
						   db='KoreanWordNet2', charset='utf8', autocommit=True)
curs=conn.cursor()
debug_str = ""
def get_document_name_from_id(doc_id):
	SQL = "select convert(Wiki_page_title using utf8) from Wiki_Document_TBL where Wiki_page_id=%s" % doc_id
	curs.execute(SQL)
	row = curs.fetchall()
	return row[0][0]

with open("wiki_entity_calc.pickle", "rb") as f:
	ent_dict = pickle.load(f)
with open("redirects.pickle", "rb") as f:
	redirects = pickle.load(f)

def candidates(word):
	candidates = ent_dict[word] if word in ent_dict else {}
	cand_list = {}
	for cand_name, cand_score in sorted(candidates.items(), key=lambda x: -x[1][0]):
		# print(cand_name, cand_score)
		cand_name = redirects[cand_name] if cand_name in redirects else cand_name
		if (cand_name in cand_list and cand_list[cand_name] < cand_score) or cand_name not in cand_list:
			cand_list[cand_name] = cand_score
	# answer = redirects[answer] if answer in redirects else answer
	# if answer is not None and answer not in cand_list:
	# 	cand_list[answer] = (, 0)
	# print("-----------------")
	return cand_list

def merge_entity(j):
	global debug_str
	entities = []
	if "data" in j:
		j = j["data"]
	j["plainText"] = j["plainText"].replace('\\"', '"')
	for item in j["addLabel"]:
		surface = j["plainText"][item["startPosition"]:item["endPosition"]]
		skip = False
		for char in "[]":
			if char in surface:
				skip = True # 범위 잘못 잡은 경우
		if surface == "line":
			skip = True
		if skip: continue
		generated_candidates = candidates(surface)
		if "candidates" not in item:
			candidate = generated_candidates
			
			# keyword = str(item["keyword"]).replace(" ", "_")
			# keyword = candidate[keyword] if keyword in candidate else "NOT_IN_CANDIDATE"
			keyword = "NOT_IN_CANDIDATE"
		else:
			# for cand in item["candidates"]:
			# 	if cand["entity"] not in generated_candidates:
			# 		generated_candidates[cand["entity"]] = (0,0)
			candidate = generated_candidates
			gold_ind = item["selected"] if "selected" in item else item["answer"]
			if gold_ind == -2:
				continue
			keyword = item["candidates"][gold_ind]["entity"] if gold_ind > -1 else "NOT_IN_CANDIDATE"
			
		entities.append({
			"text": str(surface),
			"candidates": candidate,
			"keyword": keyword,
			"start_offset": item["startPosition"],
			"end_offset": item["endPosition"],
			"type": "crowdsourcing"
			})

	for item in j["entities"]:
		ename = item["entityName"] if "entityName" in item else item["keyword"]
		candidate = candidates(item["text"])
		entities.append({
			"text": str(item["text"]),
			"candidates": candidate,
			"keyword": ename,
			"start": item["st"],
			"end_offset": item["en"],
			"type": "wikilink"
			})
	
	j["merged_entities"] = sorted(entities, key=lambda x: x["start"])
	for item in j["merged_entities"]:
		debug_str = ("merge_entity", j["plainText"][item["start"]:item["end_offset"]], item["surface"])
		if j["plainText"][item["start"]:item["end_offset"]] != item["text"]: 
			print(debug_str)
			print(j["plainText"])
		assert(j["plainText"][item["start"]:item["end_offset"]] == item["text"])
	return j

def remove_line_marker(j):
	global debug_str
	line_marker = "[.<line>.]"
	j["plainText"] = j["plainText"].replace('\\"', '"')
	text = j["plainText"]
	while True:
		try:
			ind = text.index(line_marker)
			text = text[:ind] + " " + text[ind+len(line_marker):]
			for item in j["merged_entities"]:
				if item["start"] > ind:
					item["start"] -= len(line_marker) - 1
					item["end_offset"] -= len(line_marker) - 1 # space 보정
		except ValueError:
			break

	j["plainText"] = text
	for item in j["merged_entities"]:
		debug_str = ("line_marker", j["plainText"][item["start"]:item["end_offset"]], item["surface"])
		if j["plainText"][item["start"]:item["end_offset"]] != item["text"]: print(debug_str)
		assert(j["plainText"][item["start"]:item["end_offset"]] == item["text"])
	return j

def merge_crowdsourcing_result(file_name, *js):
	global debug_str
	docs = list(map(lambda x: x["docID"], js))
	debug_str = "no match"
	assert(len(list(filter(lambda x: x == docs[0], docs))) == len(docs)) # docID가 모두 다 같은지 체크
	js = sorted(js, key=lambda x: x["parID"])
	result = {
		"docID": docs[0],
		"entities": [],
		"text": "",
		"fileName": file_name
	}
	for item in js:
		for entity in item["merged_entities"]:
			if result["text"] != "":
				entity["start"] += len(result["text"])
				entity["end_offset"] += len(result["text"])

			result["entities"].append(entity)
		result["text"] += item["plainText"] + "\n"


	for item in result["entities"]:
		debug_str = ("merge_crowdsourcing", result["text"][item["start"]:item["end_offset"]], item["surface"])
		if result["text"][item["start"]:item["end_offset"]] != item["surface"]: print(debug_str)
		assert(result["text"][item["start"]:item["end_offset"]] == item["surface"])

	return result

if __name__ == '__main__':
	import os, json
	train_main_dir = "raw_data/MTA01-2/"
	train_target_dir = "data/crowdsourcing/"
	gold_main_dir = "raw_data/elg/"
	gold_target_dir = "data/ko_golden/"

	dirs = [(train_main_dir, train_target_dir), (gold_main_dir, gold_target_dir)]
	for main_dir, target_dir in dirs:
		docs = {}
		fname = ""
		for item in os.listdir(main_dir):
			with open(main_dir+item, encoding="UTF8") as f:
				j = json.load(f)
			if "data" in j:
				j = j["data"]
			docid = j["docID"]
			parid = j["parID"]
			# _, docid, parid = item.split(".")[0].split("_")
			if docid not in docs:
				docs[docid] = {}
			docs[docid][parid] = item
		for k, v in docs.items():
			doc_name = get_document_name_from_id(k)
			try:
				processed_entities = []
				for _, fname in v.items():
					with open(main_dir+fname, encoding="UTF8") as f:
						processed_entities.append(remove_line_marker(merge_entity(json.load(f))))
				r = merge_crowdsourcing_result(doc_name, *processed_entities)
				with open(target_dir+doc_name+".json", "w", encoding="UTF8") as f:
					json.dump(r, f, ensure_ascii=False, indent="\t")
			except AssertionError as e:
				print(debug_str)
				print(fname, doc_name)