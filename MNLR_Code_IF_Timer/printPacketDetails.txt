/*
 * printPacketDetails.h
 *
 *  Created on: Sep 09, 2015
 *      Author: tsp3859
 */

#ifndef PRINTPACKETDETAILS_H_

extern int enableLogScreen;
	// TODO
	// Implement generic parser in two parts
		// a. print IP Packet
		// b. print MPLR Packet

void printIPPacketDetails(unsigned char ipPacket[], int nIPSize) {
	// TODO // Modernize
	int j = 0;
	// Recent changes below removed -14
	for (; j < nIPSize; j++) {

//	printf("TEST: %d  \n", ipHeadWithPayload[j]);
		if(enableLogScreen)
			printf("IP Content : %02x  \n", ipPacket[j] & 0xff);

	}

	if(enableLogScreen)
		printf("\n");

	u_int8_t ipVHL;

	memcpy(&ipVHL, ipPacket, 1);

	if(enableLogScreen){
		printf("          IPVHL d : %d \n", ipVHL);
		printf("        IPVHL 02x : %02x \n", ipVHL);
	}

	// TODO
	// Fix length
	int ipVersion = ipVHL / 10;
	int ipheaderLength = ipVersion * (ipVHL % 10);
	int protoType = (signed char) ipPacket[9];

	if (protoType == 1){
		if(enableLogScreen)
			printf("  Protocol Type : ICMP \n");

	}
	else if (protoType == 2){
		if(enableLogScreen)
			printf("  Protocol Type : IGMP \n");

	}
	else if (protoType == 6){
		if(enableLogScreen)
			printf("  Protocol Type : TCP \n");

	}
	else if (protoType == 17){
		if(enableLogScreen)
			printf("  Protocol Type : UDP \n");

	}
	else if (protoType == 91){
		if(enableLogScreen)
			printf("  Protocol Type : LARP \n");

	}
	else if (protoType == 54){
		if(enableLogScreen)
			printf("  Protocol Type : NARP \n");

	}
	else{
		if(enableLogScreen)
			printf("  Protocol Type : OTHER \n");

	}

	unsigned char ipSourceTemp[20];
	sprintf(ipSourceTemp, "%u.%u.%u.%u", ipPacket[12], ipPacket[13],
			ipPacket[14], ipPacket[15]);

	unsigned char ipDestTemp[20];
	sprintf(ipDestTemp, "%u.%u.%u.%u", ipPacket[16], ipPacket[17], ipPacket[18],
			ipPacket[19]);

	if(enableLogScreen){
		printf("       IP Source : %s  \n", ipSourceTemp);
		printf("  IP Destination : %s  \n", ipDestTemp);
	}

}

void printMPLRPacketDetails(unsigned char mplrPacket[], int nSize) {

	// TODO // Modernize
  	int j = 0;
	for (; j < nSize - 14; j++) {

		if(enableLogScreen)
			printf("Content : %02x  \n", mplrPacket[j] & 0xff);

	}

	if(enableLogScreen)
		printf("\n");	

}



#endif /* PRINTPACKETDETAILS_H_ */
