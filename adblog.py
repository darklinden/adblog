#!/usr/bin/env python

import subprocess
import os
import sys
import shutil

def run_cmd(cmd):
    # print("run cmd: " + " ".join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print(err)
    return out

def self_install(file, des):
    file_path = os.path.realpath(file)

    filename = file_path

    pos = filename.rfind("/")
    if pos:
        filename = filename[pos + 1:]

    pos = filename.find(".")
    if pos:
        filename = filename[:pos]

    to_path = os.path.join(des, filename)

    print("installing [" + file_path + "] \n\tto [" + to_path + "]")
    if os.path.isfile(to_path):
        os.remove(to_path)

    shutil.copy(file_path, to_path)
    run_cmd(['chmod', 'a+x', to_path])


def cmd_getargs():

    print list.count(sys.argv)
    for single_arg in sys.argv:
        print(single_arg)

    return 0

def adb_get_pid(package_name):
    pid = 0
    limit = 50
    while pid == 0 and limit > 0:
        limit -= 1
        ps_list_str = run_cmd(['adb', 'shell', 'ps', '-C', package_name])
        ps_list_str = ps_list_str.strip()

        if len(ps_list_str):
            ps_list = ps_list_str.split('\n')
            if len(ps_list) > 1:
                ps_str = ps_list[1]
                ps_num_list = ps_str.split(' ')
                for ps_num_str in ps_num_list:
                    try:
                        pid = int(ps_num_str)
                    except ValueError:
                        pid = 0

                    if pid != 0:
                        break
                if pid != 0:
                    print(ps_str)
                    break

    return pid

def __main__():

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("adblog.py", "/usr/local/bin")
        return

    # param
    package_name = ""
    platform_name = "lua"

    if len(sys.argv) > 1:
        package_name = sys.argv[1]

    if len(sys.argv) > 2:
        platform_name = sys.argv[2]

    if len(package_name) == 0:
        print("using adblog [package name] [optional platform lua(default) cpp javascript)] to log")
        return

    activity_name = "org.cocos2dx." + platform_name + ".AppActivity"

    print("adblog: starting activity " + activity_name + " of " + package_name + "...")
    activity = package_name + "/" + activity_name
    run_cmd(['adb', 'shell', 'am', 'start', '-S', activity])

    pid = adb_get_pid(package_name)

    if pid != 0:
        ps_cmd = 'adb logcat | grep --color=auto ' + str(pid)
        print(ps_cmd)
        os.system(ps_cmd)
    else:
        print("adblog: get pid for " + package_name + " failed!")

__main__()
