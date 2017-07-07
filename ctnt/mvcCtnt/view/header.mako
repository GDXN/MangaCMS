
<%inherit file="/view/base.mako"/>

<%block name="head">

	${utilities.headerBase()}
	<script>

		function searchMUForItem(formId)
		{

			var form=document.getElementById(formId);
			form.submit();
		}

		${utilities.mouseOverJs('showTT')}
	</script>

	<script type="text/javascript" src="/js/jquery-2.1.0.min.js"></script>
	<script type="text/javascript" src="/js/jquery.waypoints.js"></script>
	<meta name="viewport" content="width=1024" />

	<%block name="title"><title>this is some header content</title></%block>

</%block>
