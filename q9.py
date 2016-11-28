# q9
import sys
import sqlite3

# global variables
prefix = {}
varList	= []	# select variables

subjList = []	# subject
predList = []	# predicate
objList	= []	# object
filterDict = {}	# filter

def main():
	# argv check and acquire files
	if len(sys.argv) != 3:
		print("Usage: python3 q8.py <database file> <SPARQL input file>")
		sys.exit()
	dbfile = sys.argv[1]
	queryfile = sys.argv[2]
	readQueryFile(queryfile)

def readQueryFile(queryfile):
	infile = open(queryfile,"r")
	query = infile.read()
	infile.close()
	# reformat query string
	query = query.replace("WHERE","\nWHERE\n").replace("SELECT","SELECT\n").replace(", ",",").replace("FILTER","FILTER ")
	print(query)
	query = query.strip().split()
	print(query)
	extractQuery(query)
	print(prefix)
	print(varList)
	
def extractQuery(query):
	# flag
	extractPrefix = False
	extractSelect = False
	extractWhere = False    
	
	index = 0
	
	while (index < len(query) - 1):
		# judging what to extract
		# prefix
		if (query[index].upper() == "PREFIX"):
			extractPrefix = True
		# select
		elif (query[index].upper() == "SELECT"):
			if (query[index + 1].upper() == "WHERE"):
				print('Error, no parameter for SELECT!')
				sys.exit()
			extractSelect = True
		# where
		elif (query[index].upper() == "WHERE"):
			extractWhere = True
			if (query[index + 1] != "{"):
				print('Error, format error for WHERE')
				sys.exit()	    
			index += 2	# jump over "{"
	
		# extraction loop
		if (extractPrefix):
			type = query[index + 1].replace(":","")
			url = processURLTag(query[index + 2])
			prefix[type] = url
			
			index += 3
			extractPrefix = False
		
		elif (extractSelect):
			index += 1
			if (query[index].upper() == "WHERE"):
				extractSelect = False
			elif (query[index].upper() == "*"):
				varList.append("*")
				extractSelect = False
				index += 1
			else:
				var = query[index].replace("?","")
				varList.append(var)
		elif (extractWhere):
			if (query[index] == "."):
				index += 1
			# end of where

			if (query[index] == "}"):
				extractWhere = False
	    	# filter case
			elif (query[index].upper() == "FILTER"):
				filterStr = "filter_"+str(filterNo)
				filterNo += 1
				filterDict[filterStr] = query[index + 1]
				subjList.append(filterStr)  # adding filterStr to indicate execution order
				predList.append(filterStr)
				objList.append(filterStr)
				index += 2
				# subj, pred, obj
			else:
				subj = query[index]
				pred = query[index + 1]
				obj = query[index + 2]
				
				subjList.append(subj)
				predList.append(pred)
				objList.append(obj)
				index += 3

		else:
			index += 1
		
		
	
def processURLTag(url):
	# remove "<>" token from url
	return url[url.index("<") + 1 : url.index(">")]
	
if __name__ == '__main__':
	main()