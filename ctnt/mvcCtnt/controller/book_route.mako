

<%namespace name="ut" file="../model/utilities.mako"/>
<%namespace name="book_view" file="../view/books/book_view.mako"/>

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
	<%include file="../view/books/index.mako"/>

% elif route_root == 'all':
	<%include file="../view/books/all.mako"/>

% elif route_root == 'view':
	<%

	title = "Lolercoaster"
	content = "bwuh?"

	base = ut.getUrlParam("base_url")
	render = ut.getUrlParam("render_url")

	%>
	% if base:
		<%include
			file="../view/books/book_view.mako"
			args="title=title, content=base"
			/>
	% elif render:
		<%include
			file="../view/books/book_view.mako"
			args="title=title, content=render"
			/>
	% else:
		<%include
			file="../view/books/book_404.mako"
			/>
	% endif

% else:
	Invalid book route: '${route_root}'!
% endif

