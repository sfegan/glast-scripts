#!/bin/bash

# sanitize_name.sh - Remove nasty characters from source name
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-22
# $Id: sanitize_name.sh 1988 2010-07-21 11:59:29Z sfegan $

echo "$1" | tr '()[]{}<>!@#$%^&*()~\|";:/?., '"'" '_'
