#include "types.h"
int double_that(int number){return 2*number;}
Value double_that_gen(Value in){
    return Value(double_that(in.get_int()));
}
double tenth_that(double number){return number*0.1;}
Value tenth_that_gen(Value in){
    return Value(tenth_that(in.get_double()));
}
bool alternate_that(bool value){return !value;}
Value alternate_that_gen(Value in){
    return Value(alternate_that(in.get_bool()));
}
void just_do(){}
Value just_do_gen(Value in){
    just_do();
    return Value();
}
