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
filterList = []

numerics = [">=","<=","!=","=",">","<"]

subQueries = []

def main():
	# argv check and acquire files
	if len(sys.argv) != 3:
		print("Usage: python3 q9.py <database file> <SPARQL input file>")
		sys.exit()
	dbfile = sys.argv[1]
	queryfile = sys.argv[2]
	readQueryFile(queryfile)
	if ('*' in varList):
		getVariables()
	executeQuery(dbfile)
    
def readQueryFile(queryfile):
	infile = open(queryfile,"r")
	query = infile.read()
	infile.close()
	# reformat query string
	query = query.replace("WHERE","\nWHERE\n").replace("SELECT","SELECT\n").replace(", ",",").replace("FILTER","FILTER ").replace("<http","	<http")
	for numeric in numerics:
		query = query.replace(" "+numeric,numeric)
		query = query.replace(numeric+" ",numeric)
	
	query = query.strip().split()
	if ("}" not in query):
		print('Error, } missing')
		sys.exit()
	
	extractQuery(query)
    
def extractQuery(query):
	# flag
	extractPrefix = False
	extractSelect = False
	extractWhere = False    
	
	#filterNo = 1	# filter No.
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
				print('Error, { missing')
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
				if ("?" not in query[index]):
					print('Error, variable syntax error')
					sys.exit()	    		    
				var = query[index]#.replace("?","")
				varList.append(var)
			
		elif (extractWhere):
			if (query[index] == "."):
				index += 1
			# end of where
			if (query[index] == "}"):
				extractWhere = False
			# filter case
			elif (query[index].upper() == "FILTER"):
				#filterStr = "@"+str(filterNo)
				#filterNo += 1
				#filterDict[filterStr] = processFilter(query[index + 1])
				#subjList.append(filterStr)  # adding filterStr to indicate execution order
				#predList.append(filterStr)
				#objList.append(filterStr)
				filterList.append(processFilter(query[index + 1]))
				index += 2
			# subj, pred, obj
			else:
				subj = query[index]
				pred = query[index + 1]
				obj = query[index + 2]
				
				subj = processObject(subj)
				pred = processObject(pred)
				obj = processObject(obj)
				
				formSubQuery(subj,pred,obj)

				subjList.append(subj)
				predList.append(pred)
				objList.append(obj)

				index += 3
		
		else:
			index += 1
	    
# helper function
# process url tag
def processURLTag(url):
	# remove "<>" token from url
	return url[url.index("<") + 1 : url.index(">")]

# process where scenario
def processObject(object):
	# var
	if ("?" in object):
		#var = object.replace("?","")
		if object in varList:
			return object
		elif "*" in varList:
			return object
		else:
			print('Error, undefined variable '+object+"!")
			sys.exit()	
	# predicate
	elif (":" in object):
		i = object.index(":")
		tag = object[:i]
		obj = object[i+1:]
		if tag in prefix.keys():
			return prefix[tag]+obj
		else:
			print('Error, prefix not found!')
			sys.exit()	    
    # literals
	else:
		return object

# process REGEX
# eg: 
# (regex(?team,"Barcelona"))
# ['team', '"Barcelona"']
# (?price<=30.5) .
# ['price', '30.5', '<=']
def processFilter(filter):
	# REGEX
	if ("REGEX" in filter.upper()):
		regexList = []
		startIndex = filter.upper().index("REGEX") + 6
		endIndex = filter.index(')')
		tokenList = filter[startIndex:endIndex].split(",")
		for object in tokenList:
			regexList.append(processObject(object))
		return regexList
	# numeric
	else:
		filter = filter.replace("(","").replace(")","")
		if "<=" in filter:
			operator = "<="
			adder = 2
		elif ">=" in filter:
			operator = ">="
			adder = 2
		elif "<" in filter:
			operator = "<"
			adder = 1
		elif ">" in filter:
			operator = ">"
			adder = 1
		elif "!=" in filter:
			operator = "!="
			adder = 2
		elif "=" in filter:
			operator = "="
			adder = 1
		i = filter.index(operator)
		comparer = processObject(filter[:i])
		compared = processObject(filter[i+adder:])
		
		return [comparer,compared,operator]


def formSubQuery(subject,predicate,object):

	subQuery =""
	subQuery += formSelect(subject, predicate,object)

	# 7 cases to form query:
	# only one var
	if ((isVar(subject)) and (not isVar(predicate)) and (not isVar(object))):
		subQuery += " WHERE predicate = '"+predicate+"' AND object = '"+object+"'"

	elif ((not isVar(subject)) and (isVar(predicate)) and (not isVar(object))):
		subQuery += " WHERE subject = '"+subject+"' AND object = '"+object+"'"

	elif ((not isVar(subject)) and (not isVar(predicate)) and (isVar(object))):
		subQuery += " WHERE subject = '"+subject+"' AND predicate = '"+predicate+"'"

	# 2 vars
	elif ((not isVar(subject)) and (isVar(predicate)) and (isVar(object))):
		subQuery += " WHERE subject = '"+subject+"' "

	elif ((isVar(subject)) and (not isVar(predicate)) and (isVar(object))):
		subQuery += " WHERE predicate = '"+predicate + "' "

	elif ((isVar(subject)) and (isVar(predicate)) and (not isVar(object))):
		subQuery += " WHERE object = '"+object+"' "

	# 3 vars
	elif ((isVar(subject)) and (isVar(predicate)) and (isVar(object))):
		subQuery += " "

	subQueries.append(subQuery)

def isVar(object):
	if (object[0] == "?"):
		return True
	else:
		return False

def formSelect(subject,predicate,object):
	subList = []
	if subject[0] == "?":
		subList.append("subject")
	if predicate[0] == "?":
		subList.append("predicate")
	if object[0] == "?":
		subList.append("object")


	subQuery = "SELECT DISTINCT "

	subQuery += ','.join(subList) + " "
	subQuery += "FROM data "


	# i = 0
	# while i < len(subjList) - 1:
	# 	subQueries.append(subQuery)
	# 	i += 1
	return subQuery

def formFilterQuery(insideNest):
	#filterList = [['?title', ' "web"'],['?price', ' 3', '>']]
	#select part
	finalQuery = "SELECT DISTINCT * FROM "
	# else:
	# finalQuery = "SELECT DISTINCT "
	# for var in varList:
	# 	finalQuery += var+" "
	# finalQuery += "FROM "

	finalQuery += " ("+insideNest+") "
	finalQuery += ") WHERE "

	isDone = False
	index = 0
	for filter in filterList:
		if filter[0] in subjList:
			var = "subject"
		elif filter[0] in predList:
			var = "predicate"
		elif filter[0] in objList:
			var = "object"
		else:
			print("Error, you entered an invalid variable as a filter.")
			sys.exit()

		if len(filterList) - 1 == index:
			isDone = True

		if len(filter) == 2:
			if isDone:
				finalQuery += var + " like '%" + filter[1][1:-1] + "%' "
			else:
				finalQuery += var + " like '%" + filter[1][1:-1] + "%' and "
		elif len(filter) == 3:
			if isDone:
				finalQuery += var + " " + filter[2] + " " + filter[1] + ""
			else:
				finalQuery += var + " " + filter[2] + " " + filter[1] + " and "
		else:
			print("Error, you have formatted a filter wrong.")
			sys.exit()

		index += 1
	finalQuery+= ";"

	return finalQuery

def executeQuery(dbfile):
	conn = sqlite3.connect(dbfile)
	c = conn.cursor()
	finalQuery = ""
	insideNest = ""

	i = 0
	while i < len(subQueries) - 1:
		insideNest += "( " + subQueries[i] + ") join " 
		i+=1
	insideNest += "( "+subQueries[-1] + " )"

	finalQuery = "SELECT DISTINCT * FROM ("

	if len(filterList) == 0:
		finalQuery += insideNest
		finalQuery += ");"
	else:
		finalQuery += formFilterQuery(insideNest)

	c.execute(finalQuery)
	result = c.fetchall()

	for res in result:
		for value in getUnique(res):
			print("|%-50s" % value , end = '')
	print()

	conn.close()

def getUnique(result):
	output = list()
	for res in result:
		if res not in output:
			output.append(res)
	return output

def getVariables():
	global varList
	varList = []
	for s in subjList:
		if s[0] == "?":
			varList.append("subject")

	for p in predList:
		if p[0] == "?":
			varList.append("predicate")

	for o in objList:
		if o[0] == "?":
			varList.append("object")

	varList = list(set(varList))
if __name__ == '__main__':
	main()