#include <iostream>
#include <string>
#include <map>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>

#include "build/udf.h"
#include "build/types.h"

<USER_INCLUDES>

#define SOCK_PATH "uds_socket"

bool running = true;

int sock, t, len, i;
struct sockaddr_un remote;
char str[2048];

using namespace std;

map<string, UserFunction> function_map;

string trim(const string& str)
{
    size_t first = str.find_first_not_of(' ');
    if (string::npos == first)
    {
        return str;
    }
    size_t last = str.find_last_not_of(' ');
    return str.substr(first, (last - first + 1));
}
bool stob(std::string const &string) { 
    return string == "true";
}

void send_msg(const char* msg){
    int lenghtOfMsg = strlen(msg);

    char* message = (char*)malloc(2048);
    strcpy(message, msg);
    for(i=lenghtOfMsg; i<2048; i++){
        message[i] = ' ';
    }
    message[2048] = '\0';
    if (send(sock, message, lenghtOfMsg, 0) == -1) {
        perror("send_error");
        running = false;
    }
    free(message);
    message = 0;
}

string receive_msg(){
    if ((t=recv(sock, str, 2048, 0)) > 0) {
        str[t] = '\0';
        return trim(std::string(str));
    } else {
        if (t < 0) perror("recv");
        else running = false;
    }
    return "";
}

void setup() {
	//function_map["drive_forward"] = drive_forward_gen;
	<USER_FUNCTION_SETUP>
}

int main() {
    setup();

	if ((sock = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
        perror("socket");
        exit(1);
    }

    remote.sun_family = AF_UNIX;
    strcpy(remote.sun_path, SOCK_PATH);
    len = strlen(remote.sun_path) + sizeof(remote.sun_family) + 1;
    if (connect(sock, (struct sockaddr *)&remote, len) == -1) {
        perror("connect");
        exit(1);
    }

	while(running) {
		string cmd = receive_msg();
        if (cmd == "shutdown") {
            running = false;
        } else {
            try { 
                string type = receive_msg();
                Value v;

                if (type == "int") {
                    v = (function_map[cmd](Value(stoi(receive_msg()))));
                } else if (type == "double") {
                    v = (function_map[cmd](Value(stod(receive_msg()))));
                } else if (type == "bool") {
                    v = (function_map[cmd](Value(stob(receive_msg()))));
                } else {
                    v = (function_map[cmd](Value()));
                }

                if(v.get_type() == integer){
                    send_msg((to_string(v.get_int())).c_str());
                }
                if(v.get_type() == doubleprec){
                    send_msg((to_string(v.get_double())).c_str());
                }
                if(v.get_type() == boolean){
                    send_msg(v.get_bool() ? "true" : "false");
                }
                if(v.get_type() == voided){
                    send_msg("executed");
                }
            } catch (const std::exception& e) {
                send_msg("failed");
            }
        }
        //sendMsg(msg);
	}
}