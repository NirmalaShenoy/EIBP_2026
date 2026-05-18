/***********************************************
 * genEnvironment.h
 *  Created on: Aug 19, 2015
 *  Updated on: Sep 09, 2015
 ******************************************************/

#ifndef GENENVIRONMENT_H_
#define GENENVIRONMENT_H_

#define EMULAB_CTRL_IP "155"
#define MAX_MISSED_MSG 3
#define MSG_SEND_PERIOD 10

#include<stdlib.h>
#include<string.h>

extern int isEmulab;
extern int envSet;
extern int tierSet;
extern char *ctrlIFName;
extern char *tierAddress;
extern char *primaryTierAddress;
extern char *ctrlIFAddrIP;
extern char envName[20];

#endif

