#!/usr/bin/env sh
# -*- coding: utf-8 -*-


[ "$#" != "1" ] && \
    echo "Usage: $(basename $0) [run|report|annotate|clean]" && exit 1


COVERAGEDIR=$(dirname $0)
TESTDIR=$(dirname $COVERAGEDIR)
RCFILE=$COVERAGEDIR/coveragerc
export COVERAGE_FILE=$COVERAGEDIR/coverage.data


case "$1" in
    'run')
        coverage run --rcfile=$RCFILE $TESTDIR/runtests.py
        ;;
    'report')
        coverage report --rcfile=$RCFILE -m
        ;;
    'annotate')
        mkdir -p $COVERAGEDIR/annotate
        coverage annotate --directory=$COVERAGEDIR/annotate --rcfile=$RCFILE
        ;;
    'clean')
        coverage erase --rcfile=$RCFILE
        rm -rf $COVERAGEDIR/annotate
        ;;

    *)
        echo "Usage: $(basename $0) [run|report|clean]" && exit 1
    ;;

esac
