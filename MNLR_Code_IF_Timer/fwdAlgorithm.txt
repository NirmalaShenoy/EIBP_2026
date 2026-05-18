/*****************************************************************
 * fwdAlgorithm.c
 *  Created on: May 1, 2015
 ****************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "fwdAlgorithmHelper.h"
#include "boolean.h"
#include "tierUtils.h"

#define SUCCESS 0
#define ERROR 1

char *fwdInterface = NULL;
char *fwdTierAddr = NULL;
int fwdSet = -1;

extern boolean containsTierAddress(char testStr[20]);
extern int getTierValue(char strCheck[]);
extern boolean setByTierPartial(char inTier[20], boolean setFWDFields);
extern boolean setByTierOnly(char inTier[20], boolean setFWDFields);
extern boolean setByTierManually(char inTier[20], boolean setFWDFields);
extern int getUniqueChildIndex(char strCheck[]);
extern void findParntLongst(char* myTierAdd,char* parentTierAdd);
extern boolean isDestSubstringOfMyLabels(char* destLabel,char* myMatchedLabel);
extern boolean isMyLabelSubstringOfDest(char* destLabel,char* myMatchedLabel);
extern void printNeighbourTable(boolean isRemoved);
extern int  examineNeighbourTable(char* desTierAdd,char* longstMatchingNgbr);
extern int  examineNeighbourTable1(char* desTierAdd,char* longstMatchingNgbr, char* myLabel, int type);
extern int CheckAllDestinationLabels(char* dest);
extern void findChildLongst(char* desTierAdd,char* childTierAdd, char* myLabel);
extern int enableLogScreen;

int packetForwardAlgorithm(char currentTier[], char desTier[]);
boolean optimusForwardAlgorithm(char currentTier[], char desTier[]);
boolean algorithmOptimusG(char currentTier[], char desTier[], int tierValueCurrent);

//Functions created for util later to be moved - NS ???
void getUID(char* curUID,char* currentTier);
// void formNextUIDtoTransferInCase3B(char* nextTierAddress,char* currentTierAddress,boolean cond); not used 
//boolean checkIfDestUIDSubStringUID(char* destUID,char* myUID);


/*********************************************************************************
 * setNextTierToSendPacket(char[])
 * method to set the address of next node to send the packet
 * @param nodeAddress (char[]) - destination  node address
 * @return returnValue   (int) - algorithm return SUCCESS if it is able to else ERROR
 **************************************************************************/
 
int setNextTierToSendPacket(char* nodeAddress)
{
	int returnValue = ERROR;
	//sending the packet from the current node to the next node
	boolean checkFWDSet = setByTierOnly(nodeAddress, true);
	printf("\n***************************%s ****************************** Node Address %s", __FUNCTION__, nodeAddress); 
	if (checkFWDSet == true)
	{
		if(enableLogScreen)
			printf("\ncheckFWDSet == true , setting the fwdSet \n");
		fwdSet = SUCCESS; //to-do need of this variable ?
		returnValue = SUCCESS;
	} 
	else 
	{
		if(enableLogScreen)
			printf("\nERROR: Failed to set to the parent Tier Address\n");
		returnValue = ERROR;
		fwdSet = ERROR; //to-do need of this variable ?
	}
	return returnValue;

}

/******************************************************************************
 * getTierVal()
 * method to get the Tier value from the passed Tier address and return the same.
 * @return int [ the tier it belongs to]
 *******************************************************************************/
int getTierVal(char* tierAdd)
{
	int i = 0;
	char tierValInString[20];
	int tier = -1;
	memset(tierValInString,'\0',20);
	while(tierAdd[i] != '.')
	{
		tierValInString[i] = tierAdd[i];
		i++;
	}
	tier = atoi(tierValInString);
	return tier;
}

 
 /*******************************************************************
 * packetForwardAlgorithm(char[],char[])
 * method to perform packet forwarding
 * @param currentTier (char[]) - current tier address
 * @param desTier     (char[]) - destination tier address
 * @return returnValue   (int) - algorithm return value (-1/0/1)
 *******************************************************************/
 int packetForwardAlgorithm(char myTierAdd[], char desTierAdd[]) 
{
	if(enableLogScreen)
		printf("\n\n********************%s********************\n", __FUNCTION__);
	int returnValue = ERROR;	
	// Case:1 If( Destination Label == My Label )
	int chkDestLbl = ERROR;
	//check whether the packet reached the destination by checking all the labels of the node
	chkDestLbl = CheckAllDestinationLabels(desTierAdd);
	if (chkDestLbl == SUCCESS) {
		// Case:1 Current Tier  = Destination Tier
		if (enableLogScreen){
			printf("\nCase:1 [TRUE] My Label [%s] = Destination Label [%s] \n", myTierAdd, desTierAdd);
		}
		boolean checkIfFWDSet =setByTierManually(desTierAdd,true);// Change the function name to give a relevant one so we know what it does.

		if (checkIfFWDSet == true)
		{
			if(enableLogScreen)
				printf("\nPacket sent to the ipnode successfully"); 
			fwdSet = SUCCESS; //*******************  check the use of this varaiable
			returnValue = SUCCESS;
		}
		else
		{
			if(enableLogScreen)
				printf("\nCase:1:ERROR: Failed to set FWD Tier Address\n");
			fwdSet = ERROR;
			returnValue = ERROR;
		}
	}
	else 
	{
		if(enableLogScreen)
			printf("\nCase:1 [NOT TRUE] Destination label [%s] not in my label list \n",desTierAdd);
		// Check for Case 2 : if Destinaton label is in my neighbour table
		if (containsTierAddress(desTierAdd) == true)
		{
			// Case2 : Destinaton label is in my neighbour table
			if(enableLogScreen)
				printf("\nCase:2 [TRUE] Destinaton label is in my neighbour table \n");
			//Forward Packet to the port curresponding  to the Destination label
			returnValue = setNextTierToSendPacket(desTierAdd); // Change the name of the function.
		}
		else
		{
			if(enableLogScreen)
 				printf("\nCase:2 [NOT TRUE] Destinaton label is in my neighbour table \n");
			int myTierValue =  getTierVal(myTierAdd);
			int destTierValue = getTierVal(desTierAdd);	
			//Case 3 : If ( (My Tier Value ==  Destination Tier Value)  && (Tier Value !=1) ) 
            //printf("outsie loop",myTierValue,destTierValue,myTierAdd,desTierAdd);  
			if( (myTierValue == destTierValue) && (myTierValue != 1)) 
			{
				printf("coming inside the loop");
				if(enableLogScreen)
					printf("\nCase:3 [TRUE] My Tier Value ==  Destination Tier Value && Tier Value !=1 \n");
                int doesNTentryMatchDest = 0;
				char parentTierAdd[20];
				memset(parentTierAdd,'\0',20);
				char longstMatchingNgbr[20];
				memset(longstMatchingNgbr,'\0',20);

				if(enableLogScreen)
 					printf("\nFinding a common parent by checking if there is a longest substring match in between the destination label [%s] and my neighbor table labels\n",desTierAdd);
				//success if there is a longest substring match between the neighbor table entries and destination tier address
				doesNTentryMatchDest = examineNeighbourTable(desTierAdd,longstMatchingNgbr); // make change in the funciton, check only for parent nodes.
                if(doesNTentryMatchDest == SUCCESS){
					returnValue = setNextTierToSendPacket(longstMatchingNgbr);
                }
                else {
                    char *parentTierAddress;
                    char tempMyTierAddress[20];
                    memcpy(tempMyTierAddress, myTierAdd, strlen(myTierAdd) + 1);
                    if (enableLogScreen)
                        printf("\nNo common parent found.\nGenerating parent label from my label = %s to forward the packet to. \n", tempMyTierAddress);
                     parentTierAddress = getParent(tempMyTierAddress, '.');
                    if (enableLogScreen)
                        printf("\nGenerated parent label is [%s]\n", parentTierAddress);            	
                    returnValue = setNextTierToSendPacket(parentTierAddress);
                }
			}
			else
			{
			//Case4 and 5: if my tv is not equal to dest. tv
				if(enableLogScreen)
					printf("Case:3 [NOT TRUE] My Tier Value =  Destination Tier Value && Tier Value !=1 \n");
				printf("My Tier address: %s \n",myTierAdd);
				printf("Destination Tier address: %s \n",desTierAdd);
				printf("My Tier value: %d \n",myTierValue);
				printf("Destination Tier value: %d \n",destTierValue);
				char destUID[20];
				char myUID[20];
				getUID(myUID,myTierAdd);
				getUID(destUID,desTierAdd);
				if(myTierValue != destTierValue)
				{
					//case 4
					if(myTierValue > destTierValue)
					{
						if(enableLogScreen)
							printf("\nCase:4 [TRUE] My Tier Value !=  Destination Tier Value && My TV > Dest. TV");
						if(enableLogScreen)
							printf("\nChecking if the destination UID is a substring of any of my UIDs");
						char myMatchedLabel[20];
						memset(myMatchedLabel,'\0',20);
						boolean check = isDestSubstringOfMyLabels(desTierAdd,myMatchedLabel);
						if(check == true)
						{	
							if(enableLogScreen){
								printf("\nisDestSubstringOfMyLabels = TRUE\nDestination label [%s] is a substring of my label [%s]. Hence it is either my parent or grandparent.",desTierAdd,myMatchedLabel);
							}
							if(enableLogScreen){
								printf("\nGet the parent of my label [%s] to forward the packet to",myMatchedLabel);
							}
							char *parentTierAddress;
							char tempMyTierAddress[20];
		                    memcpy(tempMyTierAddress, myMatchedLabel, strlen(myMatchedLabel) + 1);
		                    parentTierAddress = getParent(tempMyTierAddress, '.');
		                    if (enableLogScreen)
		                        printf("\nForwarding the packet to parent: [%s]\n", parentTierAddress);
							printf("\n 1st setNextTierToSendPacket %s",parentTierAddress);
		                    returnValue = setNextTierToSendPacket(parentTierAddress);
						}
						else
						{
							if(enableLogScreen)
								printf("\nisDestSubstringOfMyLabels = FALSE\nDestination label is NOT a substring of my label.");
							char longstMatchingNgbr[20];
							memset(longstMatchingNgbr,'\0',20);
							int isDestUIDSubNeigbUID = examineNeighbourTable(desTierAdd,longstMatchingNgbr);
							if(isDestUIDSubNeigbUID != SUCCESS){
								if(enableLogScreen)
									printf("\nDestination label not a substring of any neighbour.");
								char parentTierAdd[20];
								memset(parentTierAdd,'\0',20);
								printf("\nfindParntLongst 1st");
								findParntLongst(myTierAdd,parentTierAdd);  // NS this is the only other - THIS HAS TO BE FIXED
								strcpy(longstMatchingNgbr,parentTierAdd);
								if(enableLogScreen)
									printf("\nSending the packet to parent: %s\n",parentTierAdd);
							}
							else{
								if(enableLogScreen)
									printf("\nSending the packet to the longest matching neighbour %s",longstMatchingNgbr);

							}
							printf("\n 2nd setNextTierToSendPacket %s",longstMatchingNgbr);
							returnValue = setNextTierToSendPacket(longstMatchingNgbr);
						}
					}
					//case 5
					else 
					{//NSCase5
						if(enableLogScreen)
							printf("\nCase:4 [NOT TRUE] My Tier Value !=  Destination Tier Value && My TV > Dest. TV\nCase:5 [TRUE] My Tier Value !=  Destination Tier Value && My TV < Dest. TV");	
						if(enableLogScreen)
							printf("\nChecking if any of my lables is a substring of the destination label");
						char myMatchedLabel[20];
						memset(myMatchedLabel,'\0',20); 
						boolean check = isMyLabelSubstringOfDest(desTierAdd,myMatchedLabel); //NS defined in helloList.h
						//check will return the address in myMatchedLabel and check will be set to true
						// NS TO DO - later will have to check for all destination labels
						if(check == true)
						{	
							if(enableLogScreen)
								printf("\nisMyLabelSubstringOfDest = TRUE\nMy label [%s] is a substring of Destination label [%s]", myMatchedLabel, desTierAdd);
							if(enableLogScreen)
								printf("\nThis means destination node is my child or grand child.");
							char childTierAdd[20];
							memset(childTierAdd,'\0',20);
							findChildLongst(desTierAdd,childTierAdd,myMatchedLabel); // return my label in myMathcedlabel that is an exact match?
							// NS dont we alreayd have it? childTierAdd contains the closest match
							if(enableLogScreen){
								printf("\nSending the packet to longest matching child: %s\n",childTierAdd);
							}

							returnValue = setNextTierToSendPacket(childTierAdd); //NS to check further - confusing 4-4-20
						}
						else  // I am not a proper parent of the destination - check neigbors 
						{
							if(enableLogScreen)
   								printf("\nisMyLabelSubstringOfDest = FALSE\nMy label is NOT a substring of Destination label [%s]\nExamining the Neighbor table to check if any of the neighbor is substring of the destination label.", desTierAdd);
							
							char longstMatchingNgbr[20];
							memset(longstMatchingNgbr,'\0',20);
							int isDestUIDSubNeigbUID = examineNeighbourTable(desTierAdd,longstMatchingNgbr); //NS in helloList.h
							/*
							examine neighbor table will work with one of my tieraddr 
							NS made change on 4-11-2020
							compare my tier to destination tier - NS set the type to 1 
							will only check mt neighbor is less then the dest. label, which will always be the Case
							set type 
							*/
							// NS the last entry i.e. 'type' should be based on the my current tier address.
							if(isDestUIDSubNeigbUID != SUCCESS){ // no match with my neighbor - send to my parent
								char parentTierAdd[20];
								memset(parentTierAdd,'\0',20);
								printf("\nfindParntLongst 2nd");
								findParntLongst(myTierAdd,parentTierAdd);
								/* passing myTierAdd and excepting function to return parentTierAdd */
								strcpy(longstMatchingNgbr,parentTierAdd);
								if(enableLogScreen){
		                        	printf("\nNO neighbor is a substring of the destination label\nForwarding the packet to my parent: %s %s !\n",longstMatchingNgbr,myTierAdd);
		                    	}
							}
							else{
								if(enableLogScreen){
		                        	printf("\nSending the packet to longest matching neighbour: %s \n",longstMatchingNgbr);
		                    	}
   							}
	                        returnValue = setNextTierToSendPacket(longstMatchingNgbr);
						}
					}	//NS case5
				}
			}
		}		
	}
	if(enableLogScreen)
		printf("\n\n%s:Exit , returnValue = %d \n",__FUNCTION__,returnValue);
	return returnValue;
}

/**************************************************************************
 * getUID()
 * method to get the UID from the current Tier address and store it in curUID.
 * @return none
 ***************************************************************************/
void getUID(char* curUID,char* currentTier){
	int i = 0;
	////Truncate and store the truncated part as the Tier value the UID's of both the current and the destination
	while(currentTier[i] != '.'){
		i++;
	}
	i = i+1;
	int k = 0;
	while(currentTier[i] != '\0'){
			curUID[k] = currentTier[i];
			i++;
			k++;
	}
	curUID[k] = '\0';
}

/****************************************************************
 * isFWDFieldsSet()
 * method to check whether forwarding fields are set or not
 * @return fwdSet  (int)- forwarding field status
 ***************************************************************/
int isFWDFieldsSet() {
	return fwdSet;
}
