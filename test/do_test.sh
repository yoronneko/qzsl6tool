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
    else
        printf  "${ESC}[31mFailed.${ESC}[m\n"
        diff --color=always ${BASENAME}.${EXT_TO} expect/${BASENAME}.${EXT_TO} |lv
        exit 1
    fi
    #grep -q dump ${BASENAME}.${EXT_TO}
    #if [[ $? -ne 0 ]]; then
    #    printf "  ${ESC}[33mWarning: Unexpected dump.${ESC}[m\n"
    #    exit 1
    #fi
    rm ${BASENAME}.${EXT_TO}
}

psdr_conv() {
    CODE=${CODEDIR}psdrread.py ARG=-l EXT_FROM=psdr EXT_TO=l6
    echo "Pocket SDR log data conversion:"
    echo "- QZS L6 (${CODE} ${ARG})"
    SRCDIR=../sample/
    BASENAME=20211226-082212clas
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20211226-082212mdc
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    ARG='-e' EXT_TO=e6b
    echo "- GAL E6B (${CODE} ${ARG})"
    BASENAME=20230305-063900has
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

alst_conv() {
    CODE=${CODEDIR}alstread.py ARG=-l EXT_FROM=alst EXT_TO=l6
    echo "Allystar raw data conversion:"
    echo "- QZS L6 (${CODE} ${ARG})"
    SRCDIR=../sample/
    BASENAME=20220326-231200clas
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20220326-231200mdc
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20221130-125237mdc-ppp
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

nov_conv() {
    CODE=${CODEDIR}novread.py ARG=-e EXT_FROM=nov EXT_TO=e6b
    echo "NovAtel raw data conversion:"
    echo "- GAL E6B (${CODE} ${ARG})"
    SRCDIR=../sample/
    BASENAME=20230819-053733has
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    ARG=-q EXT_TO=lnav
    BASENAME=20230819-061342qlnav
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

sept_conv() {
    CODE=${CODEDIR}septread.py ARG=-l EXT_FROM=sbf EXT_TO=l6
    echo "Septentrio raw data conversion:"
    echo "- QZS L6 (${CODE} ${ARG})"
    SRCDIR=../sample/
    BASENAME=20230819-082130clas
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20230819-085030mdc-ppp
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    ARG=-e EXT_TO=e6b
    echo "- GAL E6B (${CODE} ${ARG})"
    BASENAME=20230819-081730hasbds
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    ARG=-b EXT_TO=b2b
    echo "- BDS B2b (${CODE} ${ARG})"
    BASENAME=20230819-081730hasbds
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

ubx_conv() {
    CODE=${CODEDIR}ubxread.py ARG='--l1s -p 186' EXT_FROM=ubx EXT_TO=l1s
    echo "u-blox raw data conversion:"
    echo "- QZS L1S (${CODE} ${ARG})"
    SRCDIR=../sample/
    BASENAME=20230919-114418
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    ARG='-i' EXT_TO=inav
    echo "- GAL I/NAV (${CODE} ${ARG})"
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

qzs_l6() {
    CODE=${CODEDIR}qzsl6read.py ARG='-t 2' EXT_FROM=l6 EXT_TO=txt
    echo "QZS L6 message read (${CODE} ${ARG}):"

    SRCDIR=expect/
    BASENAME=20220326-231200clas
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20220326-231200mdc
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20221130-125237mdc-ppp
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20230819-082130clas
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20230819-085030mdc-ppp
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    SRCDIR=../sample/
    BASENAME=2019001A
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=2022001A
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=2024214A.200
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

qzs_l1s() {
    CODE=${CODEDIR}qzsl1sread.py ARG='-t 2' EXT_FROM=l1s EXT_TO=l1s.txt
    echo "QZS L1S message read (${CODE} ${ARG}):"

    SRCDIR=expect/
    BASENAME=20230919-114418
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

qzs_l6_rtcm() {
    CODE=${CODEDIR}qzsl6read.py ARG='-r' EXT_FROM=l6 EXT_TO=rtcm
    echo "QZS L6 to RTCM message conversion (${CODE} ${ARG})"

    SRCDIR=expect/
    BASENAME=20220326-231200clas
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20220326-231200mdc
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20221130-125237mdc-ppp
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

rtcm() {
    CODE=${CODEDIR}rtcmread.py ARG='-t 2' EXT_FROM=rtcm EXT_TO=rtcm.txt
    echo "RTCM message read (${CODE} ${ARG})"

    SRCDIR=../sample/
    BASENAME=20190529hiroshima
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20210101jaxamdc
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20221213-010900
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    SRCDIR=expect/
    BASENAME=20220326-231200clas
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20220326-231200mdc
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20221130-125237mdc-ppp
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

gal_inav() {
    CODE=${CODEDIR}galinavread.py ARG= EXT_FROM=inav EXT_TO=inav.txt
    echo "GAL I/NAV message read (${CODE} ${ARG})"

    SRCDIR=expect/
    BASENAME=20230919-114418
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

gal_e6() {
    CODE=${CODEDIR}gale6read.py ARG='-t 2' EXT_FROM=e6b EXT_TO=txt
    echo "GAL E6 message read (${CODE} ${ARG})"

    SRCDIR=expect/
    BASENAME=20230305-063900has
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    BASENAME=20230819-081730hasbds
    EXT_TO=e6b.txt
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

bds_b2() {
    CODE=${CODEDIR}bdsb2read.py ARG='-t 2 -p 60' EXT_FROM=b2b EXT_TO=b2b.txt
    echo "BDS B2 message read (${CODE} ${ARG})"

    SRCDIR=expect/
    BASENAME=20230819-081730hasbds
    do_test $CODE $EXT_FROM $EXT_TO $BASENAME $SRCDIR $ARG

    echo ""
}

psdr_conv
alst_conv
nov_conv
sept_conv
ubx_conv
qzs_l6
qzs_l1s
qzs_l6_rtcm
rtcm
gal_inav
gal_e6
bds_b2

# EOF

