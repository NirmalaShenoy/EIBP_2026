/*
 * tierUtils.h
 *
 *  Created on: Apr 28, 2015
 *      Author: tsp3859
 */

#ifndef TIERUTILS_H_
#define TIERUTILS_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>

#include "boolean.h"

char *getParent(char *str, char ch);
char *getParentExcludeT(char *str, char ch, int fDot);
char *getParentExcludeTU(char *str, char ch, int fDot, int lDot);
char *getChild(char *str);
char *getTrunk(char *str);

boolean containsSubString(char strValue[], char testString[]);
boolean equalsIgnoreCase(char strA[], char strB[]);
boolean equals(char strA[], char strB[]);



// int trimAndDelNewLine();
int modifyLine(char strA[], char strB[]);
int freqCount(char strCheck[], char search);
int findOccurenceAt(char strValue[], char testString[]);
int getFirstDotPosition(char strCheck[]);
int getLastDotPosition(char strCheck[]);
int getTierValue(char strCheck[]);
int toInt(char str[], int inLength);
int toIntByIndex(char str[], int inPos);
int getUniqueChildIndex(char strCheck[]);

void toString(char str[], int num);
void getStringByDot(char strCheck[], int dotPosition, char dotString[]);
void getStringByPositionAndLength(char strOrig[], char strMod[], int fromPos, int lengthReq);

extern int enableLogScreen;

/**
 * getTierValue(char[])
 *
 * method to get tier value of a tier address
 *
 * @param strCheck (char[]) - tier address
 *
 * @return returnVal (int) - tier value
 */
int getTierValue(char strCheck[]) {

	int returnVal = -1;

	int i;
	for (i = 0; strCheck[i] != '\0'; i++) {

		if (strCheck[i] == '.') {

			returnVal = toInt(strCheck, i);
			break;
		}
	}

	return returnVal;
}

/**
 * getUniqueChildIndex(char[])
 *
 * method to get unique child value (UC)
 *
 * @param strCheck (char[]) - tier address
 *
 * @return returnVal (int) - uniqueChild value
 */
int getUniqueChildIndex(char strCheck[]) {

	int returnVal = -1;

	int i;
	for (i = strlen(strCheck); i > 0; i--) {

		if (strCheck[i] == '.') {

			returnVal = toIntByIndex(strCheck, i);
			break;
		}
	}

	return returnVal;
}

/**
 * getFirstDotPosition(char[])
 *
 * method to get position of first dot in tier address
 *
 * @param strCheck (char[]) - tier address
 *
 * @return returnVal (int) - first dot position
 */
int getFirstDotPosition(char strCheck[]) {

	int returnVal = -1;

	int i;
	for (i = 0; strCheck[i] != '\0'; i++) {
		if (strCheck[i] == '.') {
			returnVal = i;
			break;
		}
	}

	return returnVal;
}

/**
 * getLastDotPosition(char[])
 *
 * method to get position of last dot in tier address
 *
 * @param strCheck (char[]) - tier address
 *
 * @return returnVal (int) - last dot position
 */
int getLastDotPosition(char strCheck[]) {

	int returnVal = -1;

	int i;
	for (i = strlen(strCheck); i > 0; i--) {
		if (strCheck[i] == '.') {
			returnVal = i;
			break;
		}
	}

	return returnVal;
}

/**
 * getParentExcludeTU(char*,char, int, int)
 *
 * method to get parent middle label excluding tier and unique child value
 *
 * @param str (char*) - tier address
 * @param ch (char)   - field separator
 * @param fDot (int)  - first dot position
 * @param lDot (int)  - last dot position
 *
 * @return str (char*)- parent field excluding tier and unique child value
 */
char *getParentExcludeTU(char *str, char ch, int fDot, int lDot) {

	int position = 0;

	char *from, *to;
	from = to = str;

	if (from[0] == '1') {
		if (from[1] == '.') {
			return from;
		}
	}

	while (*from) {

		if ((position < fDot)) {

			from++;
			position++;
		} else {

			if (position > lDot) {

				position++;
				break;
			} else {

				*to++ = *from++;
				position++;

			}
		}
	}
	*to = '\0';

	return str;
}

/**
 * getParentExcludeTU(char*,char, int)
 *
 * method to get parent middle label excluding tier value
 *
 * @param str (char*) - tier address
 * @param ch (char)   - field separator
 * @param fDot (int)  - first dot position
 *
 * @return str (char*)- parent field excluding tier value
 */
char *getParentExcludeT(char *str, char ch, int fDot) {

	int position = 0;

	char *from, *to;
	from = to = str;

	if (from[0] == '1') {
		if (from[1] == '.') {
			return from;
		}
	}

	while (*from) {

		if ((position < fDot)) {

			from++;
			position++;
		} else {
			*to++ = *from++;
			position++;

		}
	}

	*to = '\0';

	return str;
}

/**
 * getParent(char*,char)
 *
 * method to get tier address of a parent of a node
 *
 * @param str (char*) - tier address
 * @param ch (char)   - field separator
 *
 * @return str (char*)- parent tier address
 */
char* getParent(char* str, char ch) {

	char *from = NULL;
	from = str;

	if (from[0] == '1') {
		if (from[1] == '.') {
			return from;
		}
	}

	int tierVal = getTierValue(str);

	char *realParent = (char*) malloc(20);
	memset(realParent, '\0', 20);
	char tierParenttest[10];
	memset(tierParenttest, '\0', 10);

	toString(tierParenttest, tierVal - 1);

	strcpy(realParent, tierParenttest);

	int j = 0;
	for (; j < tierVal - 1; j++) {

		char subStr[10];
		memset(subStr, '\0', 10);
		getStringByDot(str, j + 1, subStr);		
		// if(enableLogScreen)
		// 	printf("4t - substr in for %s\n", subStr);
		strcat(realParent, ".");
		strcat(realParent, subStr);

	}
	if(enableLogScreen)
		printf("%s: Returning the following parent label: %s\n",__FUNCTION__,realParent);

	memset(str, '\0', strlen(str));
	return realParent;

}

/**
 * getChild(char*)
 *
 * method to get child node tier address
 *
 * @param str (char*)   - tier address of a current node
 * @param in (int)      - length of string
 * @param order (int)   - to skip certain position of dot
 *
 * @return num (int)    - integer representation of a string
 */

char *getChild(char *str) {

	// to be implemented - store all child in a separate list

	return NULL;
}

/*
 int freqCount(char strCheck[], char search) {

 int i, count = 0;
 for (i = 0; strCheck[i] != '\0'; ++i) {
 if (strCheck[i] == search)
 count++;
 }
 return count;
 }
 */

/**
 * toInt(char*, int)
 *
 * method to convert string to integer using length
 *
 * @param str (char*)     - string
 * @param inLength (int)  - length of input string (desired length from start)
 *
 * @return num (int)      - integer representation of a string
 */

int toInt(char str[], int inLength) {
	int len = inLength;
	int i, num = 0;

    for (i = 0; i < len; i++) {
        num = num + ((str[len - (i + 1)] - '0') * pow(10, i));
    }
    return num;
}

/**
 * toIntByIndex(char*, int)
 *
 * method to convert string to integer using position
 *
 * @param str (char*)   - string
 * @param inPos (int)   - position of input string to start convert from
 *
 * @return num (int)    - integer representation of a string
 */
int toIntByIndex(char str[], int inPos) {
	int len = inPos;
	int i, num = 0;


		// to skip last dot
		len = len + 1;
		int j = -1;
		for (i = len; i < strlen(str); i++) {
			j++;

			num = num + ((str[strlen(str) - (j + 1)] - '0') * pow(10, j));
		}

		return num;


}

/**
 * toString(char*, int)
 *
 * method to convert integer to string
 *
 * @param str (char*)   - string holder
 * @param num (int)     - integer to be converted
 *
 * @return str (char*)  - string representation of an integer
 *
 */
void toString(char str[], int num) {
	int i, rem, len = 0, n;

	n = num;
	while (n != 0) {
		len++;
		n /= 10;
	}
	for (i = 0; i < len; i++) {
		rem = num % 10;
		num = num / 10;
		str[len - (i + 1)] = rem + '0';
	}
	str[len] = '\0';
}

/**
 * containsSubString(char[], char[])
 *
 * method to check whether string is present in another string or not
 *
 * @param strValue  (char[])   - string value
 * @param testString (char[])  - testString for substring
 *
 * @return check (boolean)     - true or false
 *
 */
boolean containsSubString(char strValue[], char testString[]) {

	boolean check = false;

	if (strstr(strValue, testString) != NULL) {
		check = true;
	}

	return check;
}

/**
 * findOccurenceAt(char[], char[])
 *
 * method to find first occurrence position of a substring in another string
 *
 * @param strValue  (char[])   - string value
 * @param testString (char[])  - testString for substring
 *
 * @return posOccured (int)    - position of occurrence
 *
 */
int findOccurenceAt(char strValue[], char testString[]) {

	int posOccured = -1;


	 char *pfound=strstr(strValue, testString);
	 if(pfound!= NULL) {

		  posOccured= (int) (pfound - strValue);
	}

	return posOccured;
}

/**
 * getStringByDot(char[], int, char[])
 *
 * method to get string after specified dot position till next dot is reached
 *
 * @param strCheck  (char[])   - original string value
 * @param dotPosition (int)    - dotPosition
 * @param dotString (char[])   - copied string upto dot position specified by dotPosition
 *
 */
void getStringByDot(char strCheck[], int dotPosition, char dotString[]) {

	int dotCounter = 0;

	int i;
	int j = 0;
	for (i = 0; strCheck[i] != '\0'; i++) {

		if (dotCounter == dotPosition) {

			if (strCheck[i] == '.') {
				break;
			}

			dotString[j] = strCheck[i];
			j++;
		}

		if (strCheck[i] == '.') {
			dotCounter++;
		}

		if (dotCounter > dotPosition) {
			break;
		}
	}

}

/**
 * getStringByPositionAndLength(char[], char[], int, int)
 *
 * method to get string upto length from the position specified
 *
 * @param strOrig  (char[])   - original string value
 * @param strMod   (char[])   - copied string upto length from the specified position
 * @param fromPos  (int)      - starting position
 * @param lengthReq (int)     - required length
 */
void getStringByPositionAndLength(char strOrig[], char strMod[], int fromPos, int lengthReq) {

	if ((fromPos + lengthReq) < strlen(strOrig)) {

		int i = 0;
		int lengthCounter = 0;
		int j = 0;
		for (i = 0; strOrig[i] != '\0'; i++) {

			if ((i >= fromPos) && (lengthCounter < lengthReq)) {

				strMod[j] = strOrig[i];
				j++;
				lengthCounter++;
			}

		}
		strMod[j] = '\0';

	} else {
		if(enableLogScreen)
			printf("ERROR: getStringByLengthAndPos() - invalid parameter values\n");

	}

}

/**
 * equalsIgnoreCase(char[], char[])
 *
 * method to compare two strings - ignoring case
 *
 * @param strA   (char[])   - string A
 * @param strB   (char[])   - string B
 *
 * @return       (boolean)  - true/false
 */
boolean equalsIgnoreCase(char strA[], char strB[]) {

	if (strlen(strA) != strlen(strB)) {
		return false;
	} else {
		if (strcasecmp(strA, strB) == 0)
			return true;
		else
			return false;
	}
}

/**
 * equals(char[], char[])
 *
 * method to compare two strings - case sensitive
 *
 * @param strA   (char[])   - string A
 * @param strB   (char[])   - string B
 *
 * @return       (boolean)  - true/false
 */
boolean equals(char strA[], char strB[]) {

	if (strlen(strA) != strlen(strB)) {
		return false;
	} else {
		if (strcmp(strA, strB) == 0)
			return true;
		else
			return false;
	}
}

#endif
