
import TextScrape.SiteArchiver

class BlogspotScrape(TextScrape.SiteArchiver.SiteArchiver):



	# Any url containing any of the words in the `badwords` list will be ignored.
	_badwords = set([
				"/manga/",
				"/recruitment/",
				"wpmp_switcher=mobile",
				"account/begin_password_reset",
				"/comment-page-",

				# Why do people think they need a fucking comment system?
				'/?replytocom=',
				'#comments',
				'/comments/',

				# Mask out the PDFs
				"-online-pdf-viewer/",

				# Who the fuck shares shit like this anyways?
				"?share=",
				'wp-login.php',
				'/feeds/'

				])

	fileDomains = set(['bp.blogspot.com'])

	_decompose = [

		{'class' : 'widget-content'},
		{'class' : 'titlewrapper'},
		{'class' : 'title'},
		{'class' : 'post-footer'},
		{'class' : 'post-footer-line'},
		{'class' : 'cap-bottom'},
		{'class' : 'header-outer'},
		{'class' : 'column-right-outer'},
		{'class' : 'column-left-outer'},
		{'class' : 'widget-item-control'},
		{'class' : 'fauxcolumn-right-outer'},
		{'class' : 'fauxcolumn-left-outer'},
		{'id'    : 'LinkList1'},

	]

	_decomposeBefore = [
		{'class' : 'footer-outer'},
		{'class' : 'feed-links'},
		{'class' : 'post-feeds'},
		{'class' : 'comments'},
	]


