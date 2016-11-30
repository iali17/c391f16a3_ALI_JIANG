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
filterList = [] # filter list

# list that has the variables allowed
numerics = [">=","<=","!=","=",">","<"]

# list of the queries that will be made to be sent to database
subQueries = []

# reads file , executes query and ends
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
    
# reads the query file and formates the query so that we can parse easier
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

# this extracts the query 
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
        # extracts the select clause	
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
		# extracts the where clause
		elif (extractWhere):
			if (query[index] == "."):
				index += 1
			# end of where
			if (query[index] == "}"):
				extractWhere = False
			# filter case
			elif (query[index].upper() == "FILTER"):
				filterList.append(processFilter(query[index + 1]))
				index += 2
			# subj, pred, obj
			else:
				subj = query[index]
				pred = query[index + 1]
				obj = query[index + 2]
				
                # gets the subject/predicate and the object
				subj = processObject(subj)
				pred = processObject(pred)
				obj = processObject(obj)
				
                # form the sub query based on the things
				formSubQuery(subj,pred,obj)

                # append to the global list
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

# forms the sub query and adds to the list of sub queries
def formSubQuery(subject,predicate,object):
    # create the sub query
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

    # add to the list
	subQueries.append(subQuery)

# checks if the object is a variable
def isVar(object):
	if (object[0] == "?"):
		return True
	else:
		return False

# forms the select based on what they have passed us and returns the query
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

	return subQuery

# forms the filter query
# its a wrapper on top of the list returned
def formFilterQuery(insideNest):
    # initialization of the final query
	finalQuery = "SELECT DISTINCT * FROM "
	finalQuery += " ("+insideNest+") "
	finalQuery += ") WHERE "

    # gets the query based on what filters they have specified
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

        # checks if you're the second last element
		if len(filterList) - 1 == index:
			isDone = True

        # if the len of filter is 2 then you have a text query,
        # so search the query with like
		if len(filter) == 2:
			if isDone:
				finalQuery += var + " like '%" + filter[1][1:-1] + "%' "
			else:
				finalQuery += var + " like '%" + filter[1][1:-1] + "%' and "
        # if the length of the filter is 3 then you have a numeric query
        # so check with the variables given
		elif len(filter) == 3:
			if isDone:
				finalQuery += var + " " + filter[2] + " " + filter[1] + ""
			else:
				finalQuery += var + " " + filter[2] + " " + filter[1] + " and "
		else:
			print("Error, you have formatted a filter wrong.")
			sys.exit()

		index += 1
    # add semi colon to the end
	finalQuery+= ";"

	return finalQuery

# executes the query
def executeQuery(dbfile):
    # get a connection and cursor the the database
	conn = sqlite3.connect(dbfile)
	c = conn.cursor()

    # the query
	finalQuery = ""
	insideNest = ""

    # add all the sub-queries
	i = 0
	while i < len(subQueries) - 1:
		insideNest += "( " + subQueries[i] + ") join " 
		i+=1
	insideNest += "( "+subQueries[-1] + " )"

    # this is the overall query
	finalQuery = "SELECT DISTINCT * FROM ("

    # if no filters just add the semicolon and you're
    # done with the query
	if len(filterList) == 0:
		finalQuery += insideNest
		finalQuery += ");"
	else:
        # else get the filters
		finalQuery += formFilterQuery(insideNest)

    # execute the query
	c.execute(finalQuery)
    # store the results to a list
	result = c.fetchall()

    # loop through the list and print 
	for res in result:
		for value in getUnique(res):
			print("|%-50s" % value , end = '')
	print()

	conn.close()

# gets unique values in the list
def getUnique(result):
	output = list()
	for res in result:
		if res not in output:
			output.append(res)
	return output

# gets all the variables from varList and 
# sees which list they are
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