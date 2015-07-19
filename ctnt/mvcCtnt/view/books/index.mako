
<%inherit file="/view/base.mako"/>


<%block name="body_content">

	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>Search!</h2>


				<form action="/m/books/search-b/b" method="get">
					Title Search<input type="text" name="q"><input type="submit" value="Submit">
				</form>
			</div>

		</div>
	</div>
</%block>