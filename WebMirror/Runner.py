
if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()

from concurrent.futures import ProcessPoolExecutor
import WebMirror.rules
# import rpc

class Crawler(object):
	def __init__(self):

		rules = WebMirror.rules.load_rules()

		# with ProcessPoolExecutor(max_workers=self.threads) as executor:



if __name__ == "__main__":
	runner = Crawler()
	print(runner)

