## -*- coding: utf-8 -*-


<%include file="view/index.mako"/>

<%

path = []
while 1:
	item = request.path_info_pop()
	if item == None:
		break
	path.append(item)




route_root = path.pop(0)

# if route_root == '':
# 	route_index()






%>
