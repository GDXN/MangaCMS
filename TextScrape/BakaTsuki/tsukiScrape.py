
import TextScrape.SqlBase

# Double inheritance funkyness to allow subclass to override __tablename__ properly
# If we have TextScrape.SqlBase.PageRow inherit from TextScrape.SqlBase.Base, the
# Base funkyness captures the parent-class tablename and bind to it or something,
# so when it's overridden, the linkage fails.
class TsukiRow(TextScrape.SqlBase.PageRow, TextScrape.SqlBase.Base):
	__tablename__ = 'tsuki_pages'

class TsukiScrape(TextScrape.SqlBase.TextScraper):
	rowClass = TsukiRow
	loggerPath = 'Main.Tsuki'
	pluginName = 'TsukiScrape'





if __name__ == '__main__':
	print("Wat")
	row = TsukiRow()
	print(row)
	scrp = TsukiScrape()
	scrp.printSchema()
	print(scrp.session.dirty)

	t1 = TsukiRow(url='Wat?', title='Wat?', series='Wat?', contents='Wat?')
	t2 = TsukiRow(url='Lol?', title='Lol?', series='Lol?', contents='Lol?')
	t3 = TsukiRow(url='er?', title='er?', series='er?', contents='er?')
	t4 = TsukiRow(url='coas?', title='coas?', series='coas?', contents='coas?')
	t5 = TsukiRow(url='ter?', title='ter?', series='ter?', contents='ter?')

	# scrp.session.add_all([t1, t2, t3])
	# scrp.session.add(t4)
	# scrp.session.add(t5)
	# scrp.session.commit()

	print(scrp.session.dirty)
	print('Columns = ', scrp.columns)
	print(scrp.session.query(TsukiRow).filter_by(title='Wat?').first())
	print(scrp.session.dirty)
