#!/bin/bash

# sanitize_name.sh - Remove nasty characters from source name
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-22
# $Id$

echo "$1" | tr '()[]{}<>!@#$%^&*()~\|";:/?., '"'" '_'
