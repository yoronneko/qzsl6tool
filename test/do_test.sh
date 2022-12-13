#!/bin/bash

CODEDIR=../python/
#CODEDIR=

do_test() {
    CODE=$1
    EXT_FROM=$2
    EXT_TO=$3
    BASENAME=$4
    SRCDIR=$5
    ARG=${@:6:($#-5)}
    echo -n "  ${BASENAME}.${EXT_FROM}: "
    cat ${SRCDIR}${BASENAME}.${EXT_FROM} | ${CODE} ${ARG} \
        > ${BASENAME}.${EXT_TO}
    diff -q ${BASENAME}.${EXT_TO} expect/${BASENAME}.${EXT_TO} > /dev/null \
        && echo "Passed." \
        || echo "Failed."
    rm ${BASENAME}.${EXT_TO}
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

# EOF
