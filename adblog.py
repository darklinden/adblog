#!/usr/bin/env python

import subprocess
import os
import sys
import shutil
import time

G_ADB = ""
G_AAPT = ""
G_DEVICE = ""


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

    info_str = run_cmd([G_AAPT, 'dump', 'badging', path])
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
        ps_list_str = run_cmd([G_ADB, "-s", G_DEVICE, 'shell', 'ps', '|grep', package_name])
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


def init_tools():
    global G_ADB
    global G_AAPT
    global G_DEVICE

    G_ADB = run_cmd(["which", "adb"])

    G_ADB = G_ADB.strip()

    G_AAPT = run_cmd(["which", "aapt"])

    if len(G_AAPT.strip()) > 0:
        return

    platform_tools_path = os.path.dirname(G_ADB)
    sdk_path = os.path.dirname(platform_tools_path)
    build_tools_path = os.path.join(sdk_path, "build-tools")
    build_tools_list = os.listdir(build_tools_path)
    build_tools_list.sort()

    last_build_tool = os.path.join(build_tools_path, build_tools_list[-1])

    if os.path.isdir(last_build_tool):
        G_AAPT = os.path.join(last_build_tool, "aapt")

    os.system(G_ADB + " kill-server")

    devices_str = run_cmd(["adb", "devices"])
    devices = devices_str.split('\n')
    device_list = []
    for d in devices:
        if len(d.strip()) <= 0:
            continue

        dl = d.split('\t')
        if len(dl) != 2:
            continue

        device_list.append(dl[0])

    if len(device_list) == 0:
        print("adblog error: no device found!")
    elif len(device_list) == 1:
        G_DEVICE = device_list[0]
    elif len(device_list) > 1:
        print("adblog: please select device:")
        idx = 0
        for d in device_list:
            print ("\t" + str(idx) + "\t" + d)
        idx = input("choose:")

        G_DEVICE = device_list[idx]


def print_help():
    print("adblog "
          "\n\t-c cmd "
          "\n\t\t r log running activity"
          "\n\t\t s log armeabi symbol"
          "\n\t\t i install apk, run and log"
          "\n\t\t l read apk package name, run and logcat"
          "\n\t\t mem install apk if not exist, run and log memory"
          "\n\t\t cpu install apk if not exist, run and log cpu"
          "\n\t-f [file path] ")


def __main__():
    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("adblog.py", "/usr/local/bin")
        return

    init_tools()

    argLen = len(sys.argv)

    cmd = ""
    file_path = ""

    idx = 1
    while idx < argLen:
        cmd_s = sys.argv[idx]
        if cmd_s[0] == "-":
            c = cmd_s[1:]
            v = sys.argv[idx + 1]
            if c == "c":
                cmd = v
            elif c == "f":
                file_path = v
            idx += 2
        else:
            idx += 1

    if file_path == "" and cmd == "":
        print_help()
        return

    if cmd == "r":
        package_name = ""
        package_line = ""
        act_lines = run_cmd([G_ADB, "-s", G_DEVICE, 'shell', 'dumpsys', 'activity'])
        act_lines = act_lines.split("\n")
        idx = 0
        while idx < len(act_lines):
            l = act_lines[idx]
            if "Running activities" in l:
                package_line = act_lines[idx + 1]

                if len(package_line) > 0:
                    package_words = package_line.split(" ")
                    for w in package_words:
                        nw = w.strip()
                        if len(nw) > 0 and nw.startswith("A="):
                            package_name = nw[2:]
                # print(package_name)
                if package_name != "com.mumu.launcher":
                    break

            idx += 1

        if len(package_name) > 0:
            print("get running app: " + package_name)
            pid = adb_get_pid(package_name)

            if pid != 0:
                ps_cmd = G_ADB + "-s" + G_DEVICE + ' logcat | grep --color=auto ' + str(pid)
                print(ps_cmd)
                os.system(ps_cmd)
            else:
                print("adblog: get pid for " + package_name + " failed!")
        else:
            print("adblog: get pid for running app failed!")
    elif cmd == "s":
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        if not "armeabi" in os.path.basename(file_path).lower():
            print("adblog: please select symbolic file_path first!")
            return
        ps_cmd = G_ADB + "-s" + G_DEVICE + ' logcat | ndk-stack -sym ' + file_path
        print(ps_cmd)
        os.system(ps_cmd)
    elif cmd == "i":
        # param
        package_name, activity_name = get_package_and_activity(file_path)

        print("uninstalling old apk ...")
        print(run_cmd(['adb', "-s", G_DEVICE, 'uninstall', package_name]))
        print("installing new apk ...")
        print(run_cmd(['adb', "-s", G_DEVICE, 'install', file_path]))

        print("adblog: get package name " + package_name + " activity name " + activity_name)
        if len(package_name) <= 0 or len(activity_name) <= 0:
            return

        print("adblog: starting process ...")
        activity = package_name + "/" + activity_name
        run_cmd([G_ADB, "-s", G_DEVICE, 'shell', 'am', 'start', '-S', activity])

        pid = adb_get_pid(package_name)

        if pid != 0:
            ps_cmd = G_ADB + "-s" + G_DEVICE + ' logcat | grep --color=auto ' + str(pid)
            print(ps_cmd)
            os.system(ps_cmd)
        else:
            print("adblog: get pid for " + package_name + " failed!")

    elif cmd == "l":
        # param
        package_name, activity_name = get_package_and_activity(file_path)

        print("adblog: get package name " + package_name + " activity name " + activity_name)
        if len(package_name) <= 0 or len(activity_name) <= 0:
            return

        print("adblog: starting process ...")
        activity = package_name + "/" + activity_name
        run_cmd([G_ADB, "-s", G_DEVICE, 'shell', 'am', 'start', '-S', activity])

        pid = adb_get_pid(package_name)

        if pid != 0:
            ps_cmd = G_ADB + "-s" + G_DEVICE + ' logcat | grep --color=auto ' + str(pid)
            print(ps_cmd)
            os.system(ps_cmd)
        else:
            print("adblog: get pid for " + package_name + " failed!")

    elif cmd == "mem":
        # param
        package_name, activity_name = get_package_and_activity(file_path)

        print("adblog: get package name " + package_name + " activity name " + activity_name)
        if len(package_name) <= 0 or len(activity_name) <= 0:
            return

        pls = run_cmd([G_ADB, "-s", G_DEVICE, "shell", "pm", "list", "packages"])
        pl = pls.split('\n')
        installed = False
        for l in pl:
            if l.strip().endswith(package_name):
                installed = True
                break

        if not installed:
            print("installing apk ...")
            print(run_cmd([G_ADB, "-s", G_DEVICE, 'install', file_path]))

        print("adblog: starting process ...")
        activity = package_name + "/" + activity_name
        run_cmd([G_ADB, "-s", G_DEVICE, 'shell', 'am', 'start', '-S', activity])

        pid = adb_get_pid(package_name)

        if pid != 0:
            while (True):
                print (run_cmd([G_ADB, "-s", G_DEVICE, "shell", "dumpsys", "meminfo", str(pid)]))
                time.sleep(2)
        else:
            print("adblog: get pid for " + package_name + " failed!")

    elif cmd == "cpu":
        # param
        package_name, activity_name = get_package_and_activity(file_path)

        print("adblog: get package name " + package_name + " activity name " + activity_name)
        if len(package_name) <= 0 or len(activity_name) <= 0:
            return

        pls = run_cmd([G_ADB, "-s", G_DEVICE, "shell", "pm", "list", "packages"])
        pl = pls.split('\n')
        installed = False
        for l in pl:
            if l.strip().endswith(package_name):
                installed = True
                break

        if not installed:
            print("installing apk ...")
            print(run_cmd([G_ADB, "-s", G_DEVICE, 'install', file_path]))

        print("adblog: starting process ...")
        activity = package_name + "/" + activity_name
        run_cmd([G_ADB, "-s", G_DEVICE, 'shell', 'am', 'start', '-S', activity])

        pid = adb_get_pid(package_name)

        if pid != 0:
            while (True):
                print (run_cmd([G_ADB, "-s", G_DEVICE, "shell", "dumpsys", "cpuinfo", "|", "grep", package_name]))
                time.sleep(2)
        else:
            print("adblog: get pid for " + package_name + " failed!")
    else:
        print_help()


__main__()
