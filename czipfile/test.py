
import pyximport
pyximport.install()
import czipfile as zipfile

def pr(val):
	print("Val", val, type(val))

def go():
	print("WAT?")
	list(map(pr, b"watttt"))
	old_zfp = zipfile.ZipFile("/media/Storage/Scripts/MangaCMS/czipfile/325.zip", "r")
	old_zfp.setpassword(b"www.mangababy.com")
	fileNs = old_zfp.namelist()
	files = []

	for fileInfo in fileNs:

		fctnt = old_zfp.open(fileInfo).read()
		files.append((fileInfo, fctnt))

	loop = 0
	for fileN, fctnt in files:
		print("fileN, %s, fctnt, %s" % (fileN, len(fctnt)))
		with open("(2)" + fileN, "wb") as fp:
			fp.write(fctnt)

if __name__ == "__main__":
	go()

