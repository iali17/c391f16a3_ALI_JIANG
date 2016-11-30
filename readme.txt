Imran Ali, Chen Jiang

Question 2:
	This gets the airports and checks if it has a location first
	then a city it serves, then a city. This order was intentional
	it gets the most airports with the right city. Even still 
	for some reason some of the cities like "Yellowknife" do not
	have the schema:City in one if its rdf:type. So I don't know
	how to get those.

Question 6:
	Please use tab-size 8 to be able to see the table as intended.

Question 8:
	Assume all the line ending parameters like "." , ";" and "," are
		all alone (eg. "blah ." instead of "blah.")
	Assume that floats and decimals are the same (they are except
		for precision)
	All the datatypes declared eg(^^xsd:date) are of that data type
		they are not converted to text.

Question 9:
	Assume all the line ending parameters like "." , ";" and "," are
		all alone (eg. "blah ." instead of "blah.")
	Assume inside prefix a space is between ":" and Url. (eg. PREFIX: <URL> instead of PREFIX:<URL>)	

Compilation Instructions:
	Because we used python we do not need to compile the code. 
	But we are using python3.
	To run q8 please use:
		python3 q8.py <database file> <RDF input file>
	To run q9 please use:
		python3 q9.py <database file> <SPARQL input file>

Libraries used:
	sys
	sqlite3

Collaborations:
	Aaron Liu and Taylor Arnett