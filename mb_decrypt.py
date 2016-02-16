

with open("fout_1.bin", "rb") as fp:
	cont = fp.read()

cont_o = bytes([b ^ 0x47 for b in cont])

with open("fout_1.jpg", "wb") as fp:
	fp.write(cont_o)