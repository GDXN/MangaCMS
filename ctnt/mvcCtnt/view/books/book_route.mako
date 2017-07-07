

<%namespace name="ut" file="utilities.mako"/>

<%

path = []
while 1:
	item = request.path_info_pop()
	if item == None:
		break
	path.append(item)

if path:
	route_root = path.pop(0)
else:
	route_root = ''

print("Route_root:", route_root)

%>


% if route_root == '':
	<%include file="./index.mako"/>

% elif route_root == 'all':
	<%include file="./all.mako"/>

% elif route_root == 'view':
	<%

	%>
	<%include file="./all.mako"/>

% else:
	Invalid book route: '${route_root}'!
% endif

