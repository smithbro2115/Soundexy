from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.analysis import StemmingAnalyzer, CharsetFilter, SpaceSeparatedTokenizer
from whoosh.support.charset import accent_map, charset_table_to_dict, default_charset
from whoosh import index as w_index, qparser, query as w_query, writing as w_writing, sorting
from whoosh.searching import ResultsPage
from Soundexy.Functionality.useful_utils import get_app_data_folder
from Soundexy.MetaData import MetaData


accent_map[95] = " "
field_analyzer = StemmingAnalyzer() | CharsetFilter(accent_map)


class SchemaModifiedWhileWriting(Exception):
	pass


class ResultSchema(SchemaClass):
	title = TEXT(field_boost=2.0, stored=True, analyzer=field_analyzer, sortable=True)
	file_name = TEXT(field_boost=2.0, stored=True, analyzer=field_analyzer, sortable=True)
	description = TEXT(stored=True, sortable=True)
	id = ID(stored=True, sortable=True, unique=True)
	artist = TEXT(stored=True, sortable=True)
	author = TEXT(stored=True, sortable=True)
	album = TEXT(stored=True, sortable=True)
	library = TEXT(stored=True, sortable=True)
	file_type = ID(stored=True, sortable=True)
	date_created = DATETIME(stored=True, sortable=True)
	path = ID(stored=True, unique=True, sortable=True)
	keywords = KEYWORD(analyzer=field_analyzer)
	album_image_path = STORED
	duration = NUMERIC(sortable=True, stored=True)
	channels = NUMERIC(sortable=True, stored=True)
	bit_rate = NUMERIC(sortable=True, stored=True)
	sample_rate = NUMERIC(sortable=True, stored=True)


class RemoteSchema(ResultSchema):
	site_name = TEXT(stored=True)
	preview_link = ID(stored=True)
	page_link = ID(stored=True)
	original_id = ID(stored=True)


def create_index(path, schema):
	return create_in(path, schema)


def open_index(path):
	try:
		return open_dir(path)
	except AttributeError:
		return open_dir(path)


def write_to_index(writer, **kwargs):
	try:
		writer.update_document(**kwargs)
	except UnknownFieldError:
		for key in kwargs.keys():
			try:
				writer.add_field(key, STORED)
			except FieldConfigurationError:
				pass
			except Exception:
				raise SchemaModifiedWhileWriting
		write_to_index(writer, **kwargs)


def save_index(writer):
	writer.commit()


def construct_query(index: w_index.FileIndex, query_string: str):
	parser = qparser.MultifieldParser(['title', 'file_name', 'description', 'author', 'library', 'album', 'artist'],
										schema=index.schema)
	parser.remove_plugin_class(qparser.WildcardPlugin)
	op = qparser.OperatorsPlugin(Not="-", Or=",")
	parser.replace_plugin(op)
	return parser.parse(query_string)


def search_index(index: w_index.FileIndex, query, limit=100000, sort_by=None, sort_reverse=False):
	sort = None
	if sort_by:
		sort = sorting.FieldFacet(sort_by)
	results = index.searcher().search(query, limit=limit, sortedby=sort)
	return results


def search_page(index: w_index.FileIndex, query, page_size=50, sort_by=None):
	page_number = 1
	while True:
		results = index.searcher().search_page(query, page_number, pagelen=page_size, sortedby=sort_by)
		page_number += 1
		yield results
		if results.is_last_page():
			break


def get_local_index(path):
	try:
		index = open_index(path)
	except w_index.EmptyIndexError:
		index = create_index(path, ResultSchema())
	return index


def get_headers(path):
	index = get_local_index(path)
	return index.schema.stored_names()


def make_document(path):
	try:
		return normalize_meta_dict(MetaData.get_meta_file(path).meta)
	except AttributeError:
		return None


def normalize_meta_dict(meta_dict):
	new_dict = {}
	for key, value in meta_dict.items():
		if isinstance(value, list):
			new_dict[key.replace(" ", "_")] = value[0]
		else:
			new_dict[key.replace(" ", "_")] = value
	return new_dict


# test_index = create_index(get_app_data_folder('index'), ResultSchema())
# test_index = get_local_index(get_app_data_folder('index/local'))
# print(test_index)
# test_writer = test_index.writer()
# write_to_index(test_writer, title="This is a test", path="C:\\Users\\Josh\\Documents\\Bad Legs1 In Hospital.mp3",
#                content="Hey this is a practice run")
# test_writer.commit()
# test_query = construct_query(test_index, "test")
# test_results = search_index(test_index, test_query)
# print(test_results[0])
