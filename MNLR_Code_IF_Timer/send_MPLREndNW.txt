#include "sendAndFwd.h"
#include <fcntl.h>
#include <unistd.h>

extern int enableLogScreen;

/***********************************
 * mainSend(char[],char[])
 * method to send MSG TYPE V (Encapsulated IP Message)
 * @param etherPort (char[]) - interface to send on
 * @param inPayLoad (char[]) - payLoad to be sent
 * @return status (int) - method return value
 ***************************************************************/
int endNetworkSend(char etherPort[], uint8_t *inPayload, int payloadLen) {
	printf("\n\n********************%s**********************", __FUNCTION__);
	printf("\nSending on: %s\n", etherPort);
	int payLoad_Size = -1;
	int frame_Size = -1;
	int sockfd;
	struct ifreq if_idx;
	struct ifreq if_mac;
	char ifName[IFNAMSIZ];
	//printf("\nbefore segfault\n");
	strcpy(ifName, etherPort);
	//printf("\nafter segfault\n");
	frame_Size = HEADER_SIZE + payloadLen;
	
	uint8_t frame[frame_Size]; // creating frame
	struct ether_header *eh = (struct ether_header*) calloc(1,
			sizeof(struct ether_header));
	struct sockaddr_ll socket_address;
	// Open RAW socket to send on
	if ((sockfd = socket(AF_PACKET, SOCK_RAW, IPPROTO_RAW)) == -1) {
		perror("ERROR: Socket Error\n");
	}
	memset(&if_idx, 0, sizeof(struct ifreq));
	strncpy(if_idx.ifr_name, ifName, IFNAMSIZ - 1);
	if (ioctl(sockfd, SIOCGIFINDEX, &if_idx) < 0)
		perror("ERROR: SIOCGIFINDEX - Misprint Compatibility\n");
	memset(&if_mac, 0, sizeof(struct ifreq));
	strncpy(if_mac.ifr_name, ifName, IFNAMSIZ - 1);
	if (ioctl(sockfd, SIOCGIFHWADDR, &if_mac) < 0)
		perror(
				"ERROR: SIOCGIFHWADDR - Either interface is not correct or disconnected\n");
	/*
	 *  Ethernet Header - 14 bytes
	 *  6 bytes - Source MAC Address
	 *  6 bytes - Destination MAC Address
	 *  2 bytes - EtherType
	 */
	eh->ether_shost[0] = ((uint8_t *) &if_mac.ifr_hwaddr.sa_data)[0];
	eh->ether_shost[1] = ((uint8_t *) &if_mac.ifr_hwaddr.sa_data)[1];
	eh->ether_shost[2] = ((uint8_t *) &if_mac.ifr_hwaddr.sa_data)[2];
	eh->ether_shost[3] = ((uint8_t *) &if_mac.ifr_hwaddr.sa_data)[3];
	eh->ether_shost[4] = ((uint8_t *) &if_mac.ifr_hwaddr.sa_data)[4];
	eh->ether_shost[5] = ((uint8_t *) &if_mac.ifr_hwaddr.sa_data)[5];

	eh->ether_dhost[0] = MY_DEST_MAC0;
	eh->ether_dhost[1] = MY_DEST_MAC1;
	eh->ether_dhost[2] = MY_DEST_MAC2;
	eh->ether_dhost[3] = MY_DEST_MAC3;
	eh->ether_dhost[4] = MY_DEST_MAC4;
	eh->ether_dhost[5] = MY_DEST_MAC5;
	eh->ether_type = htons(0x8850);
	memcpy(frame, eh, sizeof(struct ether_header)); // Copying header to frame
	// Copying Payload (No. of tier addr + x times (tier addr length + tier addr) )
	memcpy(frame + sizeof(struct ether_header), inPayload, payloadLen);
	socket_address.sll_ifindex = if_idx.ifr_ifindex; // Index of the network device
	socket_address.sll_halen = ETH_ALEN; // Address length - 6 bytes
	// Destination MAC Address
	socket_address.sll_addr[0] = MY_DEST_MAC0;
	socket_address.sll_addr[1] = MY_DEST_MAC1;
	socket_address.sll_addr[2] = MY_DEST_MAC2;
	socket_address.sll_addr[3] = MY_DEST_MAC3;
	socket_address.sll_addr[4] = MY_DEST_MAC4;
	socket_address.sll_addr[5] = MY_DEST_MAC5;
	// Send packet
	if (sendto(sockfd, frame, frame_Size, 0, (struct sockaddr*) &socket_address,
			sizeof(struct sockaddr_ll)) < 0)
		if(enableLogScreen)
			printf("ERROR: Send failed\n");
	free(eh);
	close(sockfd);
	return 0;
}
