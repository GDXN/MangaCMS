## -*- coding: utf-8 -*-




<%

route_root = request.path_info_pop()
## route_root = path.pop(0)

%>


% if route_root == '':
	<%include file="view/index.mako"/>

% elif route_root == 'books':
	<%include file="controller/book_route.mako"/>
% else:

	Invalid route: '${route_root}'!
% endif


