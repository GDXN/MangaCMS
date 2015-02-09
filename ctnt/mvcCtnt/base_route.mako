## -*- coding: utf-8 -*-




<%

path = []
while 1:
	item = request.path_info_pop()
	if item == None:
		break
	path.append(item)

route_root = path.pop(0)

%>


% if route_root == '':
	<%include file="view/index.mako"/>
% else:
	Invalid route!
% endif


