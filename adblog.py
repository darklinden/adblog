import Queue
import threading
import urllib2
import subprocess
import os
import sys
import string

def cmd_getargs():

    print list.count(sys.argv)
    for single_arg in sys.argv:
        print(single_arg)

    return 0

def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out, err

def cmp_strlen(x, y):
    return len(x) - len(y)

def __main__():

    # param
    if len(sys.argv) != 2:
        print("using adblog grep-string to log")
        return

    grep_string = sys.argv[1]

    ps_list_str = ""

    while len(ps_list_str) <= 0:
        ps_list_str, ps_err = run_cmd(['adb', 'shell', 'ps', '|', 'grep', grep_string])
        if ps_err:
            print(ps_err)
            break

    ps_num = 0

    if ps_list_str:
        ps_list = ps_list_str.split('\n')
        ps_list = sorted(ps_list, cmp=cmp_strlen)

        for ps_str in ps_list:
            pss_list = ps_str.split(' ')
            for pstr in pss_list:
                try:
                    ps_num = int(pstr)
                except ValueError:
                    ps_num = 0

                if ps_num != 0:
                    break
            if ps_num != 0:
                print(ps_str)
                break

        if ps_num != 0:
            ps_cmd = 'adb logcat | grep ' + str(ps_num)
            print(ps_cmd)
            os.system(ps_cmd)


__main__()
