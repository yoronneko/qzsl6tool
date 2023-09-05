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

# ------
CODE=${CODEDIR}psdrread.py ARG=-l EXT_FROM=psdr EXT_TO=l6
echo "Pocket SDR to QZS L6 message conversion (${CODE} ${ARG})"

SRCDIR=../sample/
BASENAME=20211226-082212clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20211226-082212mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

# ------
CODE=${CODEDIR}alstread.py ARG=-l EXT_FROM=alst EXT_TO=l6
echo ""
echo "Allystar to QZS L6 message conversion (${CODE} ${ARG})"

SRCDIR=../sample/
BASENAME=20220326-231200clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20220326-231200mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20221130-125237mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

# ------
CODE=${CODEDIR}novread.py ARG='' EXT_FROM=nov EXT_TO=txt
echo ""
echo "NovAtel raw message read (${CODE})"

SRCDIR=../sample/
BASENAME=20230819-053733has
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20230819-061342misc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

# ------
CODE=${CODEDIR}septread.py ARG='' EXT_FROM=sept EXT_TO=txt
echo ""
echo "Septentrio raw data read (${CODE})"

SRCDIR=../sample/
BASENAME=20230819-081730hasbds
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20230819-082130clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20230819-085030mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

# ------
CODE=${CODEDIR}qzsl6read.py ARG='-t 2' EXT_FROM=l6 EXT_TO=txt
echo ""
echo "QZS L6 message read (${CODE} ${ARG})"

SRCDIR=expect/
BASENAME=20220326-231200clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20220326-231200mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20221130-125237mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

# ------
CODE=${CODEDIR}qzsl6read.py ARG='-r' EXT_FROM=l6 EXT_TO=rtcm
echo ""
echo "QZS L6 to RTCM message conversion (${CODE} ${ARG})"

SRCDIR=expect/
BASENAME=20220326-231200clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20220326-231200mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20221130-125237mdc-ppp
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

# ------
CODE=${CODEDIR}rtcmread.py ARG= EXT_FROM=rtcm EXT_TO=rtcm.txt
echo ""
echo "RTCM message read (${CODE})"

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

# ------
echo
echo '--- Compatibility test: you may see update note ---'
echo

# ------
CODE=${CODEDIR}pksdr2qzsl6.py ARG= EXT_FROM=psdr EXT_TO=l6
echo "Pocket SDR to QZS L6 message conversion (${CODE})"

SRCDIR=../sample/
BASENAME=20211226-082212clas
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20211226-082212mdc
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

# ------
CODE=${CODEDIR}pksdr2has.py ARG='-t 2' EXT_FROM=psdr EXT_TO=txt
echo ""
echo "Pocket SDR HAS message read (${CODE} ${ARG})"

SRCDIR=../sample/
BASENAME=20220930-115617has
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

BASENAME=20230305-063900has
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

# ------
CODE=${CODEDIR}nov2has.py ARG='-t 2' EXT_FROM=nov EXT_TO=decoded.txt
echo ""
echo "NovAtel HAS message read (${CODE} ${ARG})"

SRCDIR=../sample/
BASENAME=20230819-053733has
do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

echo ""

# EOF
