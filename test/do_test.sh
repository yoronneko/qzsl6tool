#!/bin/bash

CODEDIR=../python/
#CODEDIR=

ESC=$(printf '\033')

do_test() {
    local CODE=$1
    local EXT_FROM=$2
    local EXT_TO=$3
    local BASENAME=$4
    local SRCDIR=$5
    local ARG=${@:6:($#-5)}
    echo -n "  ${BASENAME}.${EXT_FROM}: "
    cat ${SRCDIR}${BASENAME}.${EXT_FROM} | ${CODE} ${ARG} \
        > ${BASENAME}.${EXT_TO}
    cmp -s ${BASENAME}.${EXT_TO} expect/${BASENAME}.${EXT_TO}
    if [[ $? -eq 0 ]]; then
        printf "${ESC}[32mPassed.${ESC}[m\n"
        rm ${BASENAME}.${EXT_TO}
    else
        printf  "${ESC}[31mFailed.${ESC}[m\n"
    fi
}

# ------ test 1: pksdr2qzsl6.py ------
CODE=${CODEDIR}pksdr2qzsl6.py ARG= EXT_FROM=txt EXT_TO=l6
echo "1. Pocket SDR to QZS L6 message conversion (${CODE})"

SRCDIR=../sample/
BASENAME=20211226-082212pocketsdr-clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20211226-082212pocketsdr-mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""
# ------ test 2: alst2qzsl6.py ------
CODE=${CODEDIR}alst2qzsl6.py ARG=-l EXT_FROM=alst EXT_TO=l6
echo "2. Allystar to QZS L6 message conversion (${CODE})"

SRCDIR=../sample/
BASENAME=20220326-231200clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20220326-231200mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20221130-125237mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""
# ------ test 3: qzsl62rtcm.py L6 message dump with -t 2 option ------
CODE=${CODEDIR}qzsl62rtcm.py ARG='-t 2' EXT_FROM=l6 EXT_TO=txt
echo "3. QZS L6 message dump with -t 2 option (${CODE})"

SRCDIR=expect/
BASENAME=20220326-231200clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20220326-231200mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20221130-125237mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""
# ------ test 4: qzsl62rtcm.py RTCM conversion ------
CODE=${CODEDIR}qzsl62rtcm.py ARG='-r' EXT_FROM=l6 EXT_TO=rtcm
echo "4. QZS L6 to RTCM message conversion (${CODE})"

SRCDIR=expect/
BASENAME=20220326-231200clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20220326-231200mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20221130-125237mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""
# ------ test 5: showrtcm.py RTCM message ------
CODE=${CODEDIR}showrtcm.py ARG= EXT_FROM=rtcm EXT_TO=rtcm.txt
echo "5. RTCM message dump (${CODE})"

SRCDIR=expect/
BASENAME=20220326-231200clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20220326-231200mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20221130-125237mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

SRCDIR=../sample/
BASENAME=20221213-010900
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""
# ------ test 6: pksdr2has.py Galileo HAS with -t 2 option ------
CODE=${CODEDIR}pksdr2has.py ARG='-t 2' EXT_FROM=txt EXT_TO=txt
echo "6. Pocket SDR HAS message dump with -t 2 option (${CODE})"

SRCDIR=../sample/
BASENAME=20220930-115617pocketsdr-e6b
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20230305-063900pocketsdr-e6b
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""
# ------ test 7: NovAtel raw data dump ------
CODE=${CODEDIR}novdump.py ARG='' EXT_FROM=nov EXT_TO=txt
echo "7. NovAtel raw message dump (${CODE})"

SRCDIR=../sample/
BASENAME=20230819-053733has
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20230819-061342misc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""
# ------ test 8: NovAtel HAS message dump with -t 2 option ------
CODE=${CODEDIR}nov2has.py ARG='-t 2' EXT_FROM=nov EXT_TO=decoded.txt
echo "8. NovAtel HAS message dump with -t 2 option (${CODE})"

SRCDIR=../sample/
BASENAME=20230819-053733has
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""
# ------ test 9: Septentrio raw data dump ------
CODE=${CODEDIR}septdump.py ARG='' EXT_FROM=sept EXT_TO=txt
echo "9. Septentrio raw data dump (${CODE})"

SRCDIR=../sample/
BASENAME=20230819-081730hasbds
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20230819-082130clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20230819-085030mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""

# EOF
