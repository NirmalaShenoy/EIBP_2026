/************************************************
 * updateEnvironment.c
 * Created on: Apr 13, 2015
 ************************************************/

#include <stdio.h>
#include <sys/types.h>
#include <netdb.h>
#include <netinet/if_ether.h>
#include <time.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/param.h>
#include <ifaddrs.h>
#include <netpacket/packet.h>
#include <net/ethernet.h>
#include <signal.h>
#include <ctype.h>

#include "genEnvironment.h"

extern int freqCount(char str[], char search);

int isEmulab = -1;
int envSet = -1;
int tierSet = -1;

char *ctrlIFName = NULL;
char *tierAddress = NULL;
char *ctrlIFAddrIP;

int setControlIF() {
	struct ifaddrs *ifaddr, *ifa;
	int family;
	if (getifaddrs(&ifaddr) == -1) {
		perror("ERROR: getifaddrs");
		exit(EXIT_FAILURE);
	}
	for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
		if (ifa->ifa_addr == NULL)
			continue;
		char ip[20];
		family = ifa->ifa_addr->sa_family;
		if (family == AF_INET) {
			if ((ifa->ifa_flags & IFF_LOOPBACK) == 0) {
				strcpy(ip, inet_ntoa(((struct sockaddr_in *) ifa->ifa_addr)->sin_addr));
				// printf("\tAddress: <%s>\n", ip);
				int charCount = freqCount(ip, '.');
				if (charCount > 0) {
					char *testForCtrlIF = strtok(ip, ".");
					// printf("Splitted: %s \n", testForCtrlIF);
					if (strlen(testForCtrlIF) == strlen(EMULAB_CTRL_IP)) {
							if (strncmp(testForCtrlIF, EMULAB_CTRL_IP, strlen(EMULAB_CTRL_IP)) == 0) {
							ctrlIFName= (char *) malloc(20);
							strcpy(ctrlIFName, ifa->ifa_name);
							ctrlIFAddrIP= (char *) malloc(20);
							strcpy(ctrlIFAddrIP, ip);
							isEmulab = 0;
							envSet = 0;
							//printf("Control interface: %s ip: %s:.. \n", ctrlIFName, testForCtrlIF);
							break;
						}
					}
				}
			}
		}
	}
	envSet=0;
	freeifaddrs(ifaddr);
	//printf("Exiting setControlIF - updateEnvironment.c \n");
	return 0;
}


int isEnvSet() {
	return envSet;
}

int isTierSet() {
	return tierSet;
}

int setTierInfo(char tierValue[]) { //function to set the tier address of the node. we are passing the tier label address(eg 2.1.2) as the argument.
	int tierLength=strlen(tierValue); //length of tier value is calculated
	tierAddress=(char *) malloc(tierLength); //allocate memory to tierAddress variable. 
	memset (tierAddress,'\0',tierLength); //set null character to the tierAddress
	strcpy(tierAddress,tierValue);//tierValue is copied to tierAddress
	tierSet=0;
	//printf("Default TierAddress in setTierInfo - updateEnvironment.c %s\n",tierAddress);
	return 0;
}

char* getTierInfo() {
	return tierAddress;
}

