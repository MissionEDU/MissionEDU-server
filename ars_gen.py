#!/usr/bin/env python

import json
import os
import sys

def build_function(method):
	udf = method["code"]+"\n"
	udf += "Value "+method["name"]+"_gen("


	udf+="Value in){\n"

	if method["return_type"] == "void":
		udf+="    "+method["name"]+"("

		if method["param_type"] == "int":
			udf+="in.get_int());\n"
		elif method["param_type"] == "double":
			udf+="in.get_double());\n"
		elif method["param_type"] == "bool":
			udf+="in.get_bool());\n"
		else:
			udf+=");\n"

		udf+="    return Value();\n"
	else:
		udf+="    return Value("+method["name"]+"("

		if method["param_type"] == "int":
			udf+="in.get_int())"
		elif method["param_type"] == "double":
			udf+="in.get_double())"
		elif method["param_type"] == "bool":
			udf+="in.get_bool())"
		else:
			udf+=")"
		udf+=");\n"

	udf+="}\n"
	return udf

def build_ars(cdf):
	cdef_file = open('ars/cdef/'+cdf, 'r')
	cdef = json.loads(cdef_file.read())

	template_file = open('ars/build/template.cpp', 'r')
	template = template_file.read()

	udf_file = open('ars/build/udf.h', 'w+')
	ars_file = open('ars/ars.cpp', 'w+')

	udf = '#include "types.h"\n'

	for include in cdef["build"]["include"]["libraries"]:
		udf += "#include "+include+"\n"

	function_setup = ""

	for method in cdef["methods"]:
		udf+=build_function(method)
		function_setup+='function_map["'+method["name"]+'"] = '+method["name"]+"_gen;"

	user_includes = ""


	template = template.replace("<USER_FUNCTION_SETUP>", function_setup)
	template = template.replace("<USER_INCLUDES>", user_includes)

	udf_file.write(udf);
	ars_file.write(template)

	bo = cdef["build"] #build option
	udf_file.close()
	ars_file.close()
	os.system("cd ars && "+bo["compiler"]+" -o ars.o ars.cpp "+bo["arguments"])
	os.system("mv ars/ars.o ars.o")
	#os.system("rm ars/ars.cpp && rm ars/build/udf.h") DEACTIVATED FOR DEBUGGING 