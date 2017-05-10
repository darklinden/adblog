#!/usr/bin/env python

import subprocess
import os
import sys
import shutil

MAY_SYM_PATH = [
    "frameworks/runtime-src/proj.android/obj/local/armeabi",
    "runtime-src/proj.android/obj/local/armeabi",
    "proj.android/obj/local/armeabi",
    "obj/local/armeabi",
    "local/armeabi",
    "armeabi",
]

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

def get_value_by_key(src, prefix, key):
    src = src[len(prefix) + 1:]
    list = src.split(" ")
    for kvpair in list:
        kvpair = kvpair.strip()
        kvlist = kvpair.split("=")
        if len(kvlist) == 2:
            tmpkey = kvlist[0]
            tmpkey = tmpkey.strip('\'')
            tmpkey = tmpkey.strip()
            if tmpkey == key:
                tmpValue = kvlist[1]
                tmpValue = tmpValue.strip('\'')
                tmpValue = tmpValue.strip()
                return tmpValue

    return ''

def get_package_and_activity(path):
    # aapt dump badging fish-lua-debug.apk
    # package: name='com.by.fishgame' versionCode='2000303' versionName='2.0.3.3' platformBuildVersionName='4.4.2-1456859'
    # launchable-activity: name='org.cocos2dx.lua.AppActivity'  label='' icon=''

    package_str = ""
    activity_str = ""

    pprefix = "package:"
    aprefix = "launchable-activity:"

    info_str = run_cmd(['aapt', 'dump', 'badging', path])
    info_list = info_str.split("\n")
    for pinfo in info_list:

        if pinfo[:len(pprefix)] == pprefix:
            package_str = pinfo

        if pinfo[:len(aprefix)] == aprefix:
            activity_str = pinfo

        if len(package_str) > 0 and len(activity_str) > 0:
            break

    package_name = get_value_by_key(package_str, pprefix, "name")
    activity_name = get_value_by_key(activity_str, aprefix, "name")

    return package_name, activity_name

def adb_get_pid(package_name):
    pid = 0
    limit = 50
    while pid == 0 and limit > 0:
        limit -= 1
        ps_list_str = run_cmd(['adb', 'shell', 'ps', '|grep', package_name])
        ps_list_str = ps_list_str.strip()

        if len(ps_list_str):
            ps_list = ps_list_str.split('\n')
            if len(ps_list) > 0:
                for ps_line_str in ps_list:
                    ps_num_list = ps_line_str.split(' ')
                    has_package_name = False
                    for s_str in ps_num_list:
                        s_str = s_str.strip()
                        s_str = s_str.strip("'")
                        s_str = s_str.strip('"')
                        if s_str.lower() == package_name.lower():
                            has_package_name = True
                            break

                    if has_package_name:
                        print(package_name)
                        print(ps_num_list)

                        for ps_num_str in ps_num_list:
                            try:
                                pid = int(ps_num_str)
                            except ValueError:
                                pid = 0

                            if pid != 0:
                                break

                    if pid != 0:
                        print(ps_line_str)
                        break

    return pid

def __main__():

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("adblog.py", "/usr/local/bin")
        return

    param = ""
    if len(sys.argv) > 1:
        param = sys.argv[1]

    if len(param) == 0:
        print("using adblog [apk-path] [-i reinstall package first] to log")
        print("using adblog [package.name] to log")
        print("using adblog -r to log running activity")
        print("using adblog -s [symbolic path] to log ndk stack")
        return

    if param == "-r":
        package_name = ""
        package_line = ""
        act_lines = run_cmd(['adb', 'shell', 'dumpsys', 'activity'])
        act_lines = act_lines.split("\n")
        idx = 0
        while idx < len(act_lines):
            l = act_lines[idx]
            if "Running activities" in l:
                package_line = act_lines[idx + 1]
                break
            idx += 1

        if len(package_line) > 0:
            package_words = package_line.split(" ")
            p_w = []
            for w in package_words:
                nw = w.strip()
                if len(nw) > 0:
                    p_w.append(nw)
            print(p_w)
            if len(p_w) > 4:
                package_name = p_w[3]

        if len(package_name) > 0:
            print("get running app: " + package_name)
            pid = adb_get_pid(package_name)

            if pid != 0:
                ps_cmd = 'adb logcat | grep --color=auto ' + str(pid)
                print(ps_cmd)
                os.system(ps_cmd)
            else:
                print("adblog: get pid for " + package_name + " failed!")
        else:
            print("adblog: get pid for running app failed!")
    elif param.lower() == "-s":
        param1 = ""
        if len(sys.argv) > 2:
            param1 = sys.argv[2]
        if not param1.startswith("/"):
            param1 = os.path.join(os.getcwd(), param1)
        for p in MAY_SYM_PATH:
            if os.path.isdir(os.path.join(param1, p)):
                param1 = os.path.join(param1, p)
                break
        if not param1.endswith("armeabi"):
            print("adblog: please select symbolic path first!")
            return
        ps_cmd = 'adb logcat | ndk-stack -sym ' + param1
        print(ps_cmd)
        os.system(ps_cmd)
    elif os.path.isfile(param):
        # param
        package_name, activity_name = get_package_and_activity(param)

        if len(sys.argv) > 2:
            if sys.argv[2] == "-i":
                print("uninstalling old apk ...")
                print(run_cmd(['adb', 'uninstall', package_name]))
                print("installing new apk ...")
                print(run_cmd(['adb', 'install', param]))

        if len(package_name) > 0 and len(activity_name) > 0:
            print("adblog: get package name " + package_name + " activity name " + activity_name)
        else:
            print("adblog: get package name " + package_name + " activity name " + activity_name)
            return

        print("adblog: starting process ...")
        activity = package_name + "/" + activity_name
        run_cmd(['adb', 'shell', 'am', 'start', '-S', activity])

        pid = adb_get_pid(package_name)

        if pid != 0:
            ps_cmd = 'adb logcat | grep --color=auto ' + str(pid)
            print(ps_cmd)
            os.system(ps_cmd)
        else:
            print("adblog: get pid for " + package_name + " failed!")
    else:
        package_name = param

        pid = adb_get_pid(package_name)

        if pid != 0:
            ps_cmd = 'adb logcat | grep --color=auto ' + str(pid)
            print(ps_cmd)
            os.system(ps_cmd)
        else:
            print("adblog: get pid for " + package_name + " failed!")

__main__()
