
import importlib.machinery
import os.path

# Horrible hackery to do python imports by absolute filesystem-path
# Returns an imported instance of the file pointed to by `pythonFile`,
# or False if the file does not exist.
# Imports do not change the current working directory, so if the file
# you're importing itself has imports relative to where it is located,
# those imports will fail.

def absImport(pythonFile):
	#split the file we want to import into the path and fileName
	root, fileN = os.path.split(pythonFile)

	# strip the ".py" extension, since we only want the modulename
	fileN = fileN.rstrip(".py")

	# Look for the "spec" used to import the named module.
	# The "spec" contains the information needed to actually load the module
	spec = importlib.machinery.PathFinder.find_spec(fileN, path=[root])

	# If the module wasn't found, return false
	if not spec:
		return False

	# Otherwise, load the found module, and return it
	module = spec.loader.load_module()
	return module


if __name__ == "__main__":
	module = absImport("/media/Storage/Scripts/Deduper/dbApi.py")
	if module:
		# Loaded module object:
		print("ret = ", module)

		# Load a class from the module:
		thing = module.DbApi()
		print("Loaded class", thing)