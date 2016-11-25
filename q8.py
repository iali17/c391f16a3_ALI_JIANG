# Q8
import sys
import sqlite3
import re

# global variables
prefix = {}
data = []
allowedEnds = ['.', ';', ',']
        
def main():
  # argv check and acquire files
  if len(sys.argv) != 3:
    print("Usage: python3 q8.py <database file> <RDF input file>")
    sys.exit()

  dbfile = sys.argv[1]
  rdffile = sys.argv[2]
  readRDFFile(rdffile)
  for x in data:
  	print(x)
  #pushDB(dbfile)

def pushDB(dbfile):
	conn = sqlite3.connect(dbfile)
	c = conn.cursor()
	c.executemany('INSERT INTO data VALUES (?,?,?,?)', data)
	conn.commit()
	conn.close()

def readRDFFile(rdffile):
	subject = ""
	predicate = ""
	previousEnding = ""

	infile = open(rdffile)
	lines = infile.readlines()
	infile.close()

	lineNumber = 1
	for line in lines:
		line = line.strip()
		lineToken = line.split()
		if len(lineToken) == 0:
			lineNumber += 1
			continue
		if lineNumber == 1:
			previousEnding = "."

		if previousEnding not in allowedEnds:
			print "Syntax error, you did not end line", lineNumber, "correctly."
			sys.exit()

		subject,predicate,previousEnding = parseLine(lineToken, lineNumber, previousEnding, subject, predicate)

		if (previousEnding == "."):
			subject = ""
			predicate = ""
		elif previousEnding == ";":
			predicate = ""

		lineNumber += 1

	# print(prefix)
	# print(data)

def parseLine(lineToken, lineNumber, previousEnding, subject, predicate):
	object = ""
	literal = ""
	# acquire prefix in RDF file, save into prefix dictionary
	# eg: @prefix dbr:    <http://dbpedia.org/resource/> .	
	# key: dbr
	# value: http://dbpedia.org/resource/
	if lineToken[0] == "@prefix":
		type = lineToken[1].replace(":","")
		url = processURLTag(lineToken[2])
		prefix[type] = url
	# you are something we want to add to the database
	else:
		lineIndex = 0
		combine = False
		startIndex = -1
		endIndex = -1
		for part in lineToken:
			if ("#" in part) and ('<' not in part) and ('>' not in part):
				index = part.find('#') #find point where we comment
				part = part[:index] # everthing past this point is a comment
				lineToken = lineToken[:lineIndex] # everything else in this line is also a comment

			if ('"' in part) and (combine == False):
				startIndex = lineIndex
				combine = True
			elif (combine == True) and ('"' in part ) :
				endIndex = lineIndex
				combine = False
			
			if ('@' in part):
				print(lineToken)
				if('@en' in part):
					lineToken[lineIndex] = part.replace("@en", "")
				else:
					return subject, predicate, "."

			if (':' in part) and ("^^" not in part):
				processTag(part) # gets rid of the prefixes and replaces them with the value

			lineIndex += 1

		if (startIndex != -1) and (endIndex != -1):
			endIndex += 1
			textObj = " ".join(lineToken[startIndex:endIndex])
			lineToken = lineToken[:startIndex] + lineToken[endIndex:]
			if(textObj != ''):
				lineToken.insert(startIndex, textObj)

		if (len(lineToken) == 4):
			#print lineToken
			subject = lineToken[0]
			predicate = lineToken[1]
			object,literal = processObject(lineToken[2])
			data.append((subject,predicate,object,literal))
		elif (len(lineToken) == 3) and (previousEnding == ';'):
			#print lineToken
			if (subject == ""):
				print "Error, trying to assign a predicate without subject. Line", lineNumber
				sys.exit()
			predicate = lineToken[0]
			object,literal = processObject(lineToken[1])
			data.append((subject,predicate,object,literal))
		elif (len(lineToken) == 2) and (previousEnding == ','):
			#print lineToken
			if (subject == "") or (predicate == ""):
				print "Error, trying to assign an object without predicate/subject. Line", lineNumber
				sys.exit()
			object,literal = processObject(lineToken[0])
			data.append((subject,predicate,object,literal))
		else:
			print len(lineToken), previousEnding
			print lineToken
			print "Error, line", lineNumber
			sys.exit()

	return subject,predicate, lineToken[-1]



def processURLTag(url):
	# remove "<>" token from url
	return url[url.index("<") + 1 : url.index(">")]

# predicate handle
def processTag(tag):
	tag = tag.split(":")
	if tag[0] not in prefix:
		print "Error, you tried to use prefix", tag[0], "when you have not defined it."
		sys.exit()
	else:
		return prefix[tag[0]]+tag[1]

def processObject(objectToken):
	objectType = "text" # default value is text
	object = objectToken

	try:
		# floats are not ints, but ints are floats
		if(isinstance(int(objectToken), int)):
			objectType = "int"
	except ValueError:
		try:
			if(isinstance(float(objectToken), float)):
				objectToken = "float"
		except ValueError:
			if "http://" in objectToken:
				objectType = "url"
			elif "^^" in objectToken:
				objectToken = objectToken.split("^^")
				object = objectToken[0]
				objectType = processTag(objectToken[1])

	return object, objectType

  
if __name__ == '__main__':
  main()