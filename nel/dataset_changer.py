import json
import os
import pickle
from konlpy.tag import Okt

# FILTER_EMPTYCAND = False
okt = Okt()
dbpedia_prefix = "ko.dbpedia.org/resource/"

# with open("unk_entity_calc.pickle", "rb") as f:
# 	ent_dict = pickle.load(f)
with open("wiki_entity_cooccur.pickle", "rb") as f:
	ent_form = pickle.load(f)
ent_form = ent_form.keys()
with open("redirects.pickle", "rb") as f:
	redirects = pickle.load(f)

def overlap(ent1, ent2):
	s1 = ent1["start_offset"]
	e1 = ent1["end_offset"]
	s2 = ent2["start_offset"]
	e2 = ent2["end_offset"]
	return s1 <= s2 < e1 or s1 < e2 <= e1

def morph_split(morph_pos, links):
	result = []
	morph, pos = morph_pos
	for link in links:
		ne, en, sp, ep = link
		if sp <= pos < ep or pos <= sp < pos+len(morph):
			if pos < sp:
				m1 = morph[:sp-pos]
				m2 = morph[sp-pos:min(len(morph), ep-pos)] # 반[중국]적 과 같은 경우
				m3 = morph[ep-pos:] if ep < pos+len(morph) else None
				result.append([m1, None])
				result.append([m2, link])
				if m3 is not None:
					result += morph_split((m3, pos+len(m1)+len(m2)), links)
				break
			elif pos + len(morph) > ep:
				# print(morph, "/", en)
				m1 = morph[:ep-pos]
				m2 = morph[ep-pos:]
				result.append([m1, link])
				result += morph_split((m2, pos+len(m1)), links)
				break
			else:
				result.append([morph, link])
				break
	else:
		result.append([morph, None])
	return result

def change_to_conll(js, filter_emptycand=False):
	result = []
	result.append("-DOCSTART- (%s" % js["fileName"] if "fileName" in js else "TEMPVAL")
	# print_flag = js["fileName"] in ["샤오미"]
	print_flag = False
	links = []
	for entity in js["entities"]:
		redirected_entity = redirects[entity["keyword"]] if entity["keyword"] in redirects else entity["keyword"]
		if redirected_entity not in ent_form and redirected_entity != "NOT_IN_CANDIDATE":
			continue
		if filter_emptycand and redirected_entity == "NOT_IN_CANDIDATE":
			continue
		links.append((entity["text"], entity["keyword"], entity["start_offset"], entity["end_offset"]))

	filter_entity = set([])
	for i1 in links:
		if i1 in filter_entity: continue
		for i2 in links:
			if i1 == i2: continue
			if i1[2] <= i2[2] < i1[3] or i1[2] < i2[3] <= i1[3]:
				# overlaps
				shorter = i1 if i1[3] - i1[2] <= i2[3] - i2[2] else i2
				filter_entity.add(shorter)
	links = list(filter(lambda x: x not in filter_entity, links))
	# for ne in j["addLabel"]:
	# 	links.append((ne["keyword"], ne["candidates"][ne["answer"]]["entity"] if "candidates" in ne and ne["answer"] >= 0 else ne["keyword"].replace(" ", "_"), ne["startPosition"], ne["endPosition"]))
	# for wikilink in j["entities"]:
	# 	links.append((wikilink["surface"], wikilink["keyword"], wikilink["st"], wikilink["en"]))
	sentence = js["text"]
	for char in "  ":
		sentence.replace(char, " ")
	morphs = okt.morphs(sentence)
	inds = []
	last_char_ind = 0
	for item in morphs:
		ind = sentence.find(item, last_char_ind) 
		inds.append(ind)
		last_char_ind = ind+len(item)
	assert(len(morphs) == len(inds))
	last_link = None
	for morph, pos in zip(morphs, inds):
		# if "\n" in morph: continue
		# print(morph, pos)
		
		added = False
		for m, link in morph_split((morph, pos), links):
			
			if link is None:
				result.append(m)
				last_link = None
				continue
			last_label = result[-1][1] if len(result) > 0 and type(result[-1]) is not str else "O"

			# last_en = result[-1][3] if len(result) > 0 and type(result[-1]) is not str else ""
			# last_sf = result[-1][2] if len(result) > 0 and type(result[-1]) is not str else ""
			bi = "I" if last_label != "O" and last_link is not None and link == last_link else "B"
			if print_flag: print(morph,m,link, last_label, last_link, bi)
			ne, en, sp, ep = link
			last_link = link
			result.append([m, bi, ne, en, "%s%s" % (dbpedia_prefix, en), "000", "000"])
		# for ne, en, sp, ep in links:
		# 	if sp <= pos < ep or pos <= sp < pos+len(morph):
		# 		if pos < sp:
		# 			print(morph, ne)
		# 			m1 = morph[:sp-pos]
		# 			m2 = morph[sp-pos:min(len(morph), ep-pos)] # 반[중국]적 과 같은 경우
		# 			m3 = morph[ep-pos:] if ep < pos+len(morph) else None
		# 			print(m1, m2, m3)
		# 			result.append(m1)
		# 			result.append([m2, "B", ne, en, "%s%s" % (dbpedia_prefix, en), "000", "000"])
		# 			if m3 is not None:
		# 				result.append(m3)
		# 			last_link = (sp, ep)
		# 			break
		# 		elif pos + len(morph) > ep:
		# 			# print(morph, "/", en)
		# 			m1 = morph[:ep-pos]
		# 			m2 = morph[ep-pos:]
		# 			result.append([m1, "I" if last_label != "O" and last_link is not None and sp == last_link[0] else "B", ne, en, "%s%s" % (dbpedia_prefix, en), "000", "000"])
		# 			result.append(m2)
		# 			last_link = None
		# 			break
		# 		else:
		# 			result.append([morph, "I" if last_label != "O" and last_link is not None and sp == last_link[0] else "B", ne, en, "%s%s" % (dbpedia_prefix, en), "000", "000"])
		# 			last_link = (sp, ep)
		# 			break
		# else:
		# 	result.append(morph)

	# dot_index = []
	# i = 0
	# pm = 0
	# for item in result:
	# 	i += 1
	# 	if item[0] == ".":
	# 		dot_index.append(i)
	# i = 0
	# for item in dot_index:
	# 	result = result[:item+i]+[""]+result[item+i:]
	# 	i += 1

	result = list(map(lambda x: x if type(x) is str else "\t".join(x), result))
	if result[-1] in ["", "\n"]:
		result = result[:-1]
	return "\n".join(result)


def get_context_words(text, pos, direction, maximum_context=30):
	# text = text.replace("[.<line>.]", "")
	result = []
	ind = pos
	buf = ""
	text = text.replace("\n", " ")
	while len(result) < maximum_context and ind > 0 and ind < len(text)-1:
		ind += direction
		if text[ind] == " ":
			if len(buf) > 0:
				buf = buf[::direction]
				result.append(buf[:])
				buf = ""
			continue
		buf += text[ind]
	if len(buf) > 0:
		result.append(buf[::direction])
	if len(result) == 0:
		return "EMPTYCTXT"
	result = " ".join(result[::direction])
	# print(result)
	return result


def change_to_tsv(j, filter_emptycand=False):
	# print(fname)
	result = []
	text = j["text"]
	fname = j["fileName"]
	entity_to_text = lambda x: ",".join(["0", "0", x["entity"]])# 0을 entity id로 바꿔야 함
	entities = j["entities"]
	filter_entity = []
	for i1 in entities:
		if i1 in filter_entity: continue
		for i2 in entities:
			if i1 == i2: continue
			if overlap(i1, i2):
				# overlaps
				shorter = i1 if i1["end_offset"] - i1["start_offset"] <= i2["end_offset"] - i2["start_offset"] else i2
				filter_entity.append(shorter)
	entities = list(filter(lambda x: x not in filter_entity, entities))
	for entity in entities:
		redirected_entity = redirects[entity["keyword"]] if entity["keyword"] in redirects else entity["keyword"]
		if redirected_entity not in ent_form and redirected_entity != "NOT_IN_CANDIDATE":
			continue
		if filter_emptycand and redirected_entity == "NOT_IN_CANDIDATE":
			continue
		candidate_list = entity["candidates"]
		sp = entity["start_offset"]
		ep = entity["end_offset"]
		f = [fname, fname, entity["text"], get_context_words(text, sp, -1), get_context_words(text, ep, 1), "CANDIDATES"]
		gold_ind = -1
		gold_sent = ""
		ind = 0
		cand_list = []
		for cand_name, cand_score in sorted(candidate_list.items(), key=lambda x: -x[1][0]):
			cand_list.append((redirects[cand_name] if cand_name in redirects else cand_name, cand_score))
		# cand_list.append(("#UNK#", ent_dict["#UNK#"]))
		if redirected_entity == "NOT_IN_CANDIDATE": redirected_entity = "#UNK#"
		for cand_name, cand_score in cand_list:
			# print(cand_score)
			f.append(",".join([str(cand_score[1]), str(cand_score[0]), cand_name]))
			if cand_name == redirected_entity:
				gold_ind = ind
				gold_sent = f[-1]
			ind += 1
		if len(cand_list) == 0:
			f.append("EMPTYCAND")
		f.append("GE:")
		f.append("%d,%s" %(gold_ind, gold_sent) if gold_ind != -1 else "-1")
		result.append("\t".join(f))
	return result


main_dir = "data/crowdsourcing/"
gold_dir = "data/ko_golden/"
target_dir = "data/generated/test_train_data/"
if __name__ == '__main__':
	docs = {}
	doc_name = {}
	c = 0
	train = [open(target_dir+"cs_train.conll", "w", encoding="UTF8"), open(target_dir+"cs_train.tsv", "w", encoding="UTF8")]
	dev = [open(target_dir+"cs_dev.conll", "w", encoding="UTF8"), open(target_dir+"cs_dev.tsv", "w", encoding="UTF8")]
	test = [open(target_dir+"cs_test.conll", "w", encoding="UTF8"), open(target_dir+"cs_test.tsv", "w", encoding="UTF8")]
	target = [train] * 9 + [dev]
	# target = [test] * 10
	for item in os.listdir(main_dir):
		c += 1
		flag = False
		with open(main_dir+item, encoding="UTF8") as f:
			j = json.load(f)
			x = target[c % 10]
			x[0].write(change_to_conll(j, flag)+"\n\n")
			# break
			fname = item.split(".")[0].split("_")[-1]
			for item in change_to_tsv(j, flag):
				x[1].write(item+"\n")
	for item in os.listdir(gold_dir):
		with open(gold_dir+item, encoding="UTF8") as f:
			# print(gold_dir+item)
			j = json.load(f)
			test[0].write(change_to_conll(j)+"\n\n")
			for item in change_to_tsv(j):
				test[1].write(item+"\n")
	for a, b in [train, dev, test]:
	# for a, b in [test]:
		a.close()
		b.close()