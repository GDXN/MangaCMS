
<%inherit file="/view/base.mako"/>


<%block name="body_content">

	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>Search!</h2>


				<form action="/m/books/search" method="get">
					Title Search<input type="text" name="q"><input type="submit" value="Submit">
				</form>

				<form action="/m/books/view" method="get">
					View address<input type="text" name="base_url"><input type="submit" value="Submit">
				</form>
			</div>

		</div>
	</div>
</%block>


RequestProxy that either fetches from remote, or returns local cache.
