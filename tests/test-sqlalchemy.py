
import sqlalchemy as sa
import sqlalchemy.ext.declarative as dec
import sqlalchemy.engine.url as saurl
import sqlalchemy.orm as saorm
import sqlalchemy.schema as sch
import settings
import abc

class ItemTable():
	__tablename__ = 'book_items'

	@abc.abstractproperty
	def _source_key(self):
		pass

	rowid    = sa.Column(sa.Integer, sa.Sequence('book_page_id_seq'), primary_key=True)
	src      = sa.Column(sa.String,  nullable=False, index=True, default=_source_key)
	dlState  = sa.Column(sa.Integer, nullable=False, index=True, default=0)
	url      = sa.Column(sa.String,  nullable=False, unique=True, index=True)
	title    = sa.Column(sa.String)
	series   = sa.Column(sa.String)
	contents = sa.Column(sa.String)
	istext   = sa.Column(sa.Boolean, index=True, nullable=False, default=True)
	mimetype = sa.Column(sa.String)
	fspath   = sa.Column(sa.String)

Base = dec.declarative_base(cls=ItemTable)

class TestItem(Base):
	_source_key = 'test'

	# Set the default value of `src`. Somehow, despite the fact that `self.src` is being set
	# to a string, it still works.
	def __init__(self, *args, **kwds):
		self.src = self._source_key
		print(self)
		print(type(self))
		print(super())
		print("IsInstance of ItemTable", isinstance(self, ItemTable))
		print("IsInstance of Table", isinstance(self, sch.Table))
		print("mro", TestItem.mro())
		super().__init__(*args, **kwds)



def test():
	test = TestItem()


	engine_conf = saurl.URL(drivername='postgresql',
							username = settings.DATABASE_USER,
							password = settings.DATABASE_PASS,
							database = settings.DATABASE_DB_NAME
							# host = settings.DATABASE_IP,
							)

	engine = sa.create_engine(engine_conf)
	sessionFactory = saorm.sessionmaker(bind=engine)


	session = sessionFactory()



if __name__ == "__main__":

	test()

