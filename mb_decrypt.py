

with open("022.webp", "rb") as fp:
	cont = fp.read()

cont_o = bytes([b ^ 0x10 for b in cont])

with open("022_decr.webp", "wb") as fp:
	fp.write(cont_o)