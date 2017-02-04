#include <iostream>
#include <string>
#include <map>

#include "udf.h"
#include "types.h"

using namespace std;

map<string, UserFunction> function_map;

void setup() {
	function_map["drive_forward"] = drive_forward_gen;
}

int main() {
	function_map["double_that"] = double_that_gen;
	cout << (function_map["double_that"](Value(2))).get_int() << endl;
}