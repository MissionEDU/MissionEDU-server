#include "types.h"
void drive_forward(int distance){}
Value drive_forward_gen(Value distance){
	drive_forward(distance.get_int());
	return  Value();
}

int double_that(int in){return in*2;}
Value double_that_gen(Value in){
	return  Value(double_that(in.get_int()));
}