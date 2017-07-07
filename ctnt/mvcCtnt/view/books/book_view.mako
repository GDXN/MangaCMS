
<%inherit file="/view/base.mako"/>


<%block name="body_content">
	<%
	title   = pageargs['title']
	content = pageargs['content']
	%>
	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>View</h2>
				${title}
				<br>
				${content}

			</div>

		</div>
	</div>
</%block>