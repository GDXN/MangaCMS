## -*- coding: utf-8 -*-
<!DOCTYPE html>



<%

path = []
while 1:
	item = request.path_info_pop()
	if item == None:
		break
	path.append(item)

print(path)

%>
