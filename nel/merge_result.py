def merge_item(j, result_file):
	if type(j) is not list:
		j = [j]
	result = {}
	result_file.readline()
	target_name = ""
	target_json = None
	ind = 0
	for line in result_file.readlines():
		# print(line)
		l = line.strip().split("\t")
		if len(l) == 1:
			target_name = l[0].split(" ")[0]
			# print(target_name)
			result[target_name] = []
			ind = 0
			for item in j:
				if item["fileName"] == target_name:
					target_json = item
					for item in target_json["entities"]:
						del item["candidates"]
						del item["keyword"]
					break
			else:
				raise Exception("No such file name: %s" % target_name)
			continue
		# print(len(target_json["entities"]), ind)

		# del target_json["entities"][ind]["candidates"]
		target_json["entities"][ind]["entity"] = l[2]
		target_json["entities"][ind]["score"] = float(l[3])
		target_json["entities"][ind]["confidence"] = float(l[4])
		ind += 1
	return j


if __name__ == '__main__':
	print("merge result")
	import json
	with open("test_result_marking.txt", encoding="UTF8") as result_file, open("tta.json", encoding="UTF8") as j, open("tta_merged.json", "w", encoding="UTF8") as wf:
		jj = json.load(j)
		json.dump(merge_item(jj, result_file), wf, ensure_ascii=False, indent="\t")