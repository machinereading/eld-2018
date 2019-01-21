import json

kbox_uri = "http://kbox.kaist.ac.kr/resource/"
types = {}
print("loading types")
with open("kb_ref/tsv_instance_types_ko.ttl", encoding="UTF8") as f1:
	for line in f1.readlines():
		s, p, o, _ = line.strip().split("\t")
		s = s.strip("<>").replace("http://ko.dbpedia.org/resource/", "")
		if s not in types:
			types[s] = set([])
		types[s].add(o.strip("<>"))
with open("kb_ref/tsv_instance_types_transitive_ko.ttl", encoding="UTF8") as f2:
	for line in f2.readlines():
		s, p, o, _ = line.strip().split("\t")
		s = s.strip("<>").replace("http://ko.dbpedia.org/resource/", "")
		if s not in types:
			types[s] = set([])
		types[s].add(o.strip("<>"))
# i = 0
# for k, v in types.items():
# 	i += 1
# 	print(k, v)
# 	if i > 10: break
print("Done!")

print("loading english uris")
uris = {}
with open("kb_ref/tsv_interlanguage_links_ko.ttl", encoding="UTF8") as f:
	for line in f.readlines():
		s, p, o, _ = line.strip().split("\t")
		s = s.strip("<>").replace("http://ko.dbpedia.org/resource/", "")
		if "http://dbpedia.org" in o:
			uris[s] = o.strip("<>").replace("http://dbpedia.org/resource/", "")
			# print(s, uris[s])


def postprocess(j):
	for sentence in j:
		for entity in sentence["entities"]:
			entity_text = entity["entity"]
			if entity_text == "NIL":
				dark_entity = "_" + "_".join(entity["text"].split())
				entity["uri"] = kbox_uri + dark_entity
			else:
				entity["uri"] = kbox_uri + entity_text
			entity["type"] = list(types[entity_text]) if entity_text in types else []
			entity["en_entity"] = uris[entity_text] if entity_text in uris else ""
			del entity["entity"]
	return j

if __name__ == '__main__':
	with open("tta_merged.json", encoding="UTF8") as f, open("tta_final_result.json", "w", encoding="UTF8") as wf:
		json.dump(postprocess(json.load(f)), wf, ensure_ascii=False, indent="\t")