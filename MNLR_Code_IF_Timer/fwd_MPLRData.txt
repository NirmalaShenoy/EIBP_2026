#include "sendAndFwd.h"
#include <fcntl.h>
#include <unistd.h>

extern int enableLogScreen;
int dataFwd(char etherPort[20], unsigned char MPLRPacket[], int MPLRPacketSize) {
	int payLoad_Size = -1;
	int frame_Size = -1;
	int sockfd;
	struct ifreq if_idx;
	struct ifreq if_mac;
	int tx_len = 0;
	char ifName[IFNAMSIZ];
	int tempSizeTest = 14 + MPLRPacketSize;
	uint8_t header[HEADER_SIZE];

	strcpy(ifName, etherPort);
	payLoad_Size = MPLRPacketSize;
	frame_Size = HEADER_SIZE + payLoad_Size;

	unsigned char payLoad[payLoad_Size];
	memcpy(payLoad, MPLRPacket, payLoad_Size);

	uint8_t frame[frame_Size];
	memset(frame, '\0', frame_Size);

	struct ether_header *eh = (struct ether_header *) header;
	struct sockaddr_ll socket_address;
	
	if ((sockfd = socket(AF_PACKET, SOCK_RAW, IPPROTO_RAW)) == -1) {
		perror("ERROR: Socket Error");
	}

	memset(&if_idx, 0, sizeof(struct ifreq));
	strncpy(if_idx.ifr_name, ifName, IFNAMSIZ - 1);
	if (ioctl(sockfd, SIOCGIFINDEX, &if_idx) < 0)
		perror("ERROR: SIOCGIFINDEX - Misprint Compatibility");

	memset(&if_mac, 0, sizeof(struct ifreq));
	strncpy(if_mac.ifr_name, ifName, IFNAMSIZ - 1);
	if (ioctl(sockfd, SIOCGIFHWADDR, &if_mac) < 0)
		perror(
				"ERROR: SIOCGIFHWADDR - Either interface is not correct or disconnected");

	memset(header, 0, HEADER_SIZE);

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
	tx_len += sizeof(struct ether_header);

	memcpy(frame, header, 14); // Copying header to frame

	memcpy(frame + 14, payLoad, payLoad_Size); // Copying the payload to the frame

	//printf(
	//		"TEST: FWDC - Frame: %02x:%02x:%02x:%02x:%02x:%02x  %02x:%02x:%02x:%02x:%02x:%02x  %02x:%02x %02x:\n",
	//		frame[0], frame[1], frame[2], frame[3], frame[4], frame[5],
	//		frame[6], frame[7], frame[8], frame[9], frame[10], frame[11],
	//		frame[12], frame[13], frame[14]);
	
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
	if (sendto(sockfd, frame, tx_len + payLoad_Size, 0,
			(struct sockaddr*) &socket_address, sizeof(struct sockaddr_ll)) < 0)
		if(enableLogScreen)
			printf("ERROR: Send failed\n");

	close(sockfd);
	return 0;
}
