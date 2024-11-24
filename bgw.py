



#combat@sd36cm1> netstat -nap | grep -E '1039|2945' | grep ESTABLISHED
#(No info could be read for "-p": geteuid()=5784 but you should be root.)
#tcp        0      0 10.10.48.240:2945       10.44.244.51:51471      ESTABLISHED -
#tcp        0      0 10.10.48.240:1039       10.10.48.58:59610       ESTABLISHED -

#combat@sd36cm1> netstat -nt| grep -E '1039|2945'
#tcp        0      0 10.10.48.240:2945       10.44.244.51:51471      ESTABLISHED
#tcp        0      0 10.10.48.240:1039       10.10.48.58:59610       ESTABLISHED

