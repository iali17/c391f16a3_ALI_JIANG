# Q8
import sys
import sqlite3

# global variables
prefix = {} # list for prefixes
data = [] # the data that will be pushed
allowedEnds = ['.', ';', ','] # all the endings allowed
base = "" # the base that will be used

# main function checks if we have specified 2 files
# assigns them and then reads files and pushes   
def main():
	# argv check and acquire files
	if len(sys.argv) != 3:
		print("Usage: python3 q8.py <database file> <RDF input file>")
		sys.exit()
	
	# assign the files
	dbfile = sys.argv[1] 
	rdffile = sys.argv[2]

	# read the files and store the data into the list
	readRDFFile(rdffile)

	# push to database
	pushDB(dbfile)

# pushes the data onto the database file provided
def pushDB(dbfile):
	conn = sqlite3.connect(dbfile) # connect to the sqlite3 db
	c = conn.cursor() # get the cursor

	# push all the data onto the database
	c.executemany('INSERT INTO data VALUES (?,?,?,?)', data)

	# once it completes, commit changes and close connection
	conn.commit()
	conn.close()

# reads the rdf file and stores the data on the
# data list to be pushed onto the database
def readRDFFile(rdffile):
	subject = ""
	predicate = ""
	previousEnding = ""
	fullLine = []

	# open the file, store all lines to and close the file
	infile = open(rdffile)
	lines = infile.readlines()
	infile.close()

	lineNumber = 1 # keeps track of what line we are on 
	# loop through the lines
	for line in lines:
		line = line.strip() # strip any useless spaces in front or behind
		if ("#" in line):
			index = line.find('#')
			# finds all the '#' rather than just the first
			while index != -1:
				left = line[:index] # get the left side of the comment
				right = line[index:] # get the right side of the comment

				# if it is not contained inside a url then everything else in 
				# this line is a comment
				if (('<' not in left) or ('>' not in right)) and (index != -1):
					line = line[:index]
				index = line.find('#',index+1) # find point where we comment

		# split the line by white space included '\t' and ' '
		lineToken = line.split()
		# empty line, skip
		if len(lineToken) == 0:
			lineNumber += 1
			continue
		# if its the first line assume the previous ending will be '.'
		if lineNumber == 1:
			previousEnding = "."

		# if the last thing in the line is not allowed then we assume its a multi-line
		if lineToken[-1] not in allowedEnds:
			# add the line token and go to next line
			fullLine += lineToken
			lineNumber += 1
			# if we reach the end of the file and you did not have an allowed ending
			# then error and exit
			if lineNumber == (len(lines) +1):
				print("Error, You did not end your last statement.")
				sys.exit()
			continue
		else:
			# else the full line is just the token
			fullLine += lineToken

		# call parse line. It returns the subject/predicate/and the previous ending
		subject,predicate,previousEnding = parseLine(fullLine, lineNumber, previousEnding, subject, predicate)

		# reset the full line
		fullLine = []

		# if the previous ending is a ".", we have a new subject and predicate
		if (previousEnding == "."):
			subject = ""
			predicate = ""
		# if the previous line ending is a ";" we have a new predicate
		elif previousEnding == ";":
			predicate = ""

		# increment line number
		lineNumber += 1

# parse the line and return the subject/predicate/line ending if we have one
def parseLine(lineToken, lineNumber, previousEnding, subject, predicate):
	global base # use the global base variable
	object = ""
	literal = ""
	combinePart = ""

	# acquire prefix in RDF file, save into prefix dictionary
	# eg: @prefix dbr:    <http://dbpedia.org/resource/> .	
	# key: dbr:
	# value: http://dbpedia.org/resource/
	if (lineToken[0] == "@prefix") or (lineToken[0] == "PREFIX"):
		url = processURLTag(lineToken[2])
		prefix[lineToken[1]] = url
	# if it is a base then we assign the base var to it 
	elif (lineToken[0] == "@base") or (lineToken[0] == "BASE"):
		url = processURLTag(lineToken[1])
		base = url
	# you are something we want to add to the database
	else:
		# local variables 
		lineIndex = 0
		combine = False
		startIndex = -1
		endIndex = -1

		# loop through each part in the line
		for part in lineToken:
			# if you a uri
			if ('<' in part) and ('>' in part):
				# check if they have assigned a type
				if ("^^" in part) :
					# get all the data before you assign the type
					index = part.find('<') 
					# change the line to the correct format
					lineToken[lineIndex] = part[:index] + processURLTag(part)
				else:
					# if you're not a url we assume you are trying to use a base
					if "http://" not in part:
						# if base is not defined print error, exit
						if (base == ""):
							print("Trying to use a base when you have not defined one. Line", lineNumber)
							sys.exit()
						# else change the line
						lineToken[lineIndex] = base + processURLTag(part)
					# you are a url so process it
					else:
						lineToken[lineIndex] = processURLTag(part)

			# combining lines, we check if you have wrote a peice of text that needs to be
			# combines (eg.a slogan with spaces would get split up). This part finds the
			# start of the index.
			if (('"' in part) or ("'''" in part) or ("'" in part)) and (combine == False):
				index = part.find('"')
				index2 = part.find("'''")
				index3 = part.find("'")

				# if the index is not found then make it infinity
				# to make sure that it wont be found
				if (index == -1) :
					index = float("inf")
				if (index2 == -1):
					index2 = float("inf")
				if (index3 == -1):
					index3 = float("inf")

				# find out which quotation is the first and use it as a indicate when to end
				if (index < index2) and (index < index3):
					combinePart = '"'
				elif (index2 < index) and (index2 < index3):
					combinePart = "'''"
				else:
					combinePart = "'"

				# save the start index and set flag to true
				startIndex = lineIndex
				combine = True
			# if flag is true and you've found the combine part again then this is the end
			elif (combine == True) and (combinePart in part):
				endIndex = lineIndex
				combine = False
			
			# if we we find something that is prefixed and its not a type or link 
			if (':' in part) and ("^^" not in part) and ("http" not in part):
				lineToken[lineIndex] = processTag(part) # gets rid of the prefixes and replaces them with the value

			lineIndex += 1 # update line index

		# if you have found a start and end index then combine those lines
		if (startIndex != -1) and (endIndex != -1):	
			endIndex += 1
			textObj = " ".join(lineToken[startIndex:endIndex]) # join them together on a space
			lineToken = lineToken[:startIndex] + lineToken[endIndex:] # remove those indexes from the line
			if(textObj != ''): # if its not an empty line
				lineToken.insert(startIndex, textObj) # insert it back where it was

		# if you have 4 objects and the previous ending was a period
		if ((len(lineToken) == 4)and (previousEnding == ".")):
			subject = lineToken[0] # assign subject
			predicate = lineToken[1] # assign predicate
			object,literal = processObject(lineToken[2]) # assign object and type
			if object: # if there is an object
				data.append((subject,predicate,object,literal)) # then add to list
		# if you have 3 objects and the previous ending was a semi-colon
		elif (len(lineToken) == 3) and (previousEnding == ';'):
			if (subject == ""): # error checking
				print("Error, trying to assign a predicate without subject. Line", lineNumber)
				sys.exit()
			# assign the predicate and object/literal
			predicate = lineToken[0]
			object,literal = processObject(lineToken[1])
			# if object is not none then add to data
			if object:
				data.append((subject,predicate,object,literal))
		# if you have 2 objects and the previous ending was a comma
		elif (len(lineToken) == 2) and (previousEnding == ','):
			# error checking
			if (subject == "") or (predicate == ""):
				print("Error, trying to assign an object without predicate/subject. Line", lineNumber)
				sys.exit()
			# assign the object and literal
			object,literal = processObject(lineToken[0])
			# if object exists then add to the data
			if object:
				data.append((subject,predicate,object,literal))
		else:
			# Catch all error, usually ends up here if you have not ended a line and so
			# we assume its a multi-line and if it has too many arguments it ends up here
			print(lineToken)
			print("Error, line", lineNumber)
			print("Either too many arguments or too little arguments given in this line.")
			print("Please check if you have ended all your lines correctly.")
			sys.exit()
	# if we dont exit we return the subject/predicate and the line ending
	return subject,predicate, lineToken[-1]

# remove "<>" token from url
def processURLTag(url):
	return url[url.index("<") + 1 : url.index(">")]

# processes the prefixes
def processTag(tag):
	tag = tag.split(":") # split on semi-colon
	tag[0] += ":" # add the semi-colon back on
	if tag[0] == "_:": # if its a blank node
		return tag[0] + tag[1] # return the whole thing as object
	# if the prefix is not in the list then error, because it hasn't been defined
	if tag[0] not in prefix:
		print("Error, you tried to use prefix", tag[0], "when you have not defined it.")
		sys.exit()
	else:
		# else return the object
		return prefix[tag[0]]+tag[1]

# processes the object, returns the object and the type
def processObject(objectToken):
	objectType = "text" # default value is text

	# remove all the non english tags
	if ('@' in objectToken):
		if('@en' in objectToken):
			objectToken = objectToken.replace("@en", "")
		else:
			return None, None

	object = objectToken

	# trying to figure out type
	try:
		# floats are not ints, but ints are floats
		if(isinstance(int(objectToken), int)): # check if int
			objectType = "int"
	except ValueError: # if not int
		try:
			if(isinstance(float(objectToken), float)): # check if float
				objectType = "float"
		except ValueError: # if not float and int
			# check if it a type has been defined
			if "^^" in objectToken:
				# if it has then split it and get the right type
				objectToken = objectToken.split("^^")
				object = objectToken[0]
				if ("http://" in objectToken[1]):
					objectType = objectToken[1]
				else:
					objectType = processTag(objectToken[1])
	# else its a text

	# return the object and type
	return object, objectType

# when program is run, call main() as the main function
if __name__ == '__main__':
  main()
