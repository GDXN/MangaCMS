

if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()
		# for item in fl.getAllItems():
		# 	print(item)
		fl.go()
