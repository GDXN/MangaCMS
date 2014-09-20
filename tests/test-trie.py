
items = ["Accel World:Updates", "Accel World:Volume SS1", "Accel World:Volume SS1 Chapter 1",
"Accel World:Volume SS1 Chapter 2", "Accel World:Volume SS1 Chapter 3", "Accel World:Volume SS1 Chapter 4",
"Accel World:Volume SS1 Chapter 5", "Accel World:Volume SS1 Illustrations", "Ancient Magic Arc",
"Ancient Magic Arc:Updates", "Ancient Magic Arc Volume 1: Chapter 1", "Ancient Magic Arc Volume 1: Chapter 2",
"Ancient Magic Arc Volume 1: Prologue", "Anniversary no Kuni no Alice", "A Simple Survey", "Audio Recordings", "Baccano"]

import pprint

def compress_trie(key, childIn):
	if len(childIn) == 1:
		kidKey = list(childIn.keys())[0]
		if isinstance(childIn[kidKey], dict):
			key += kidKey
			return compress_trie(key, childIn[kidKey])
		return key, childIn
	else:
		for kidKey in list(childIn.keys()):
			if isinstance(childIn[kidKey], dict):
				retKey, retDict = compress_trie(kidKey, childIn[kidKey])
				childIn[retKey] = retDict
				if kidKey != retKey:
					del childIn[kidKey]
		return key, childIn

def build_trie(iterable, getkey=lambda x: x):
	base = {}

	scan = [[getkey(tmp).lower(), tmp] for tmp in iterable]
	for key, item in scan:

		floating_dict = base
		for letter in key:
			floating_dict = floating_dict.setdefault(letter, {})
		floating_dict[key] = item

	compress_trie('', base)

	pp = pprint.PrettyPrinter(indent=1)
	pp.pprint(base)

def test():
	build_trie(items)


if __name__ == "__main__":

	test()

