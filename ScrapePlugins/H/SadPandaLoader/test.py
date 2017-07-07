
import webFunctions

def test():
	wg = webFunctions.WebGetRobust()
	print("Test fetching page:")
	print(wg.getpage('http://api.ipify.org?format=json'))

	print("Test complete")

