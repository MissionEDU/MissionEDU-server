#ifndef _TYPES_H
#define _TYPES_H

enum Types { integer, doubleprec, boolean, voided };

class Value {
private:
	int int_val_;
	double double_val_;
	bool bool_val_;
	Types mode_;
public:
	Value(int int_val) {
		int_val_ = int_val;
		mode_ = integer;
	}
	Value(double double_val) {
		double_val_ = double_val;
		mode_ = doubleprec;
	}
	Value(bool bool_val) {
		bool_val_ = bool_val;
		mode_ = boolean;
	}
	Value(void) {
		mode_ = voided;
	}
	Types get_type() {
		return mode_;
	}
	int get_int() {
		return int_val_;
	}
	double get_double() {
		return double_val_;
	}
	bool get_bool() {
		return bool_val_;
	}
};

typedef Value (*UserFunction)(Value);
#endif