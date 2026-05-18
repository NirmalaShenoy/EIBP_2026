/*
 *  sendAndFwd.h
 *
 *  Contains default variables and include statements
 *  used by send_MPLRCtrl.c, send_MPLRData.c, fwd_MPLRData.c and fwd_MPLRDecapsulation.c
 *
 *  Created on: Mar 06, 2015
 *  Updated on: Sep 09, 2015
 *      Author: Tejas Padliya - tsp3859@rit.edu
 */

#ifndef SEND_H_
#define SEND_H_

#include <arpa/inet.h>
#include <linux/if_packet.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <net/if.h>
#include <netinet/ether.h>


// Destination MAC address (Presently broadcast address)
#define MY_DEST_MAC0	0xFF
#define MY_DEST_MAC1	0xFF
#define MY_DEST_MAC2	0xFF
#define MY_DEST_MAC3	0xFF
#define MY_DEST_MAC4	0xFF
#define MY_DEST_MAC5	0xFF

// Source Ethernet interface
#define DEFAULT_INTERFACE	"eth0"
#define DEFAULT_PAYLOAD		"Default PayLoad"

// Define Message type fields
#define MESSAGE_TYPE_CTRL  1
#define MESSAGE_TYPE_DATA  2
#define MESSAGE_TYPE_ENDNW 5
#define MESSAGE_TYPE_AUTOLABEL  6


// Types newly added for auto assignment of labels
#define MESSAGE_TYPE_JOIN  				7
#define MESSAGE_TYPE_LABELS_AVAILABLE  	8
#define MESSAGE_TYPE_LABELS_ACCEPTED  	9
#define MESSAGE_TYPE_MY_LABELS_ADD 10
#define MESSAGE_TYPE_MY_LABELS_DELETE 11
#define MESSAGE_TYPE_REQUEST_IP_RESOLVE 12
#define MESSAGE_TYPE_RESPONSE_IP_RESOLVE 13
#define MESSAGE_TYPE_LABELS_LOST 14
#define MESSAGE_TYPE_PUBLISH_IP_DELETE 15
#define MESSAGE_TYPE_PUBLISH_IP_ADD 16

#define MESSAGE_TYPE_ENDNW_ADD	1
#define MESSAGE_TYPE_ENDNW_REMOVE	2
#define MESSAGE_TYPE_ENDNW_UPDATE	3
#define MESSAGE_TYPE_ENDNW_REMOVE_ADDR  4 


// Allocating size to different containers
#define HEADER_SIZE			14

#define MAX_CTRL_FRAME_SIZE		1024
#define MAX_CTRL_PAYLD_SIZE		1000

#define MAX_DATA_FRAME_SIZE		1524
#define MAX_DATA_PAYLD_SIZE	    1510

#define MAX_TIER_ADDR_SIZE		20

#endif
