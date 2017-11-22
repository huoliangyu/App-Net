#!/usr/bin/python

# We construct the following queue system:
#               1:           root qdisc
#               |
#              1:1           child class maximum 1000kbit
#             /   \
#            /     \
#          1:10     1:11      leaf classes with 300kbit and 200kbit
#           |        |        1:11: 300kbit ceil
#          10:      11:       qdiscs
#         (sfq)    (sfq)

CHILD_CLASS_MAXIMUM = "1000kbit"
LEAF_CLASS_1_10_MAXIMUM = "300kbit"
LEAF_CLASS_1_11_MAXIMUM = "200kbit"
LEAF_CLASS_1_10_CEIL = "500kbit"
LEAF_CLASS_1_11_CEIL = "300kbit"
