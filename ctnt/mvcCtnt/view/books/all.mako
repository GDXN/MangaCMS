
<%inherit file="/view/base.mako"/>

<%namespace name="db"        file="/model/books/all_books.mako"/>

<%block name="body_content">

	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>All Books</h2>
				${db.get_all_books()}

			</div>

		</div>
	</div>
</%block>