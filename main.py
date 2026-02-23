import requests
import random
import os
import ctypes, sys
from pathlib import Path
import json
import time
import sys, subprocess
import wmi

API = "https://api.cgi26.cn"
token = None
device_secret = None

def redeviceid(devicename):
    print(devicename)
    print(logedid)
    print("您的设备为虚拟机/云服务器，无硬盘序列号，或者您在同一块硬盘上安装了多个系统，或者deviceid与他人重合（如果您运气特别好的话）deviceid创建失败。")
    print("我们将改为使用10位随机数作为您的deviceid。这可能会降低控制的准确性与安全性。")
    allow1=input("要继续吗？(y/n)")
    if allow1 == "y":
        deviceid = str(random.randint(10**9, 10**10 - 1))

        api_register_device(deviceid, devicename)

        data = {"random": deviceid}
        base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
        file = base / "device.json"
        file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("注册号存储完成。")
        print("设备注册完成。")
    elif allow1 == "n":
        exit()
    else:
        exit()

    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def checkdevice(logedid,device_secret):
    print("用户登陆完成。您的用户id为：")
    print(logedid)
    from pathlib import Path

    try:
        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "device.json"
        with file.open("r", encoding="utf-8") as f:
            pass
        deviceinfofile=1
    except FileNotFoundError:
        deviceinfofile=0

    target = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
    deviceinfo = 1 if target.is_dir() else 2
    if deviceinfo == 1:
        print("该设备已注册。请稍后，我们正在为您查询您的设备代号。")
        if deviceinfofile == 1:
            file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "device.json"
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            readedid = data["random"]#readedid是指从本地json中读取到的deviceid。
            deviceid = readedid

            api_is_owner(deviceid)
            if not api_is_owner(deviceid):
                print("不是你的设备，禁止操作。")
                time.sleep(30)
                exit()
            print("查询成功，这是您的设备。")
            print("请从下方操作中选择，并键入其左侧对应的代号：")
            print("————————————————————————————————————————————————————————————")
            print("1. 开始侦听并执行")
            print("2. 退出")
            print("============================================================")
            userinput2=input("请输入要执行的操作的代号：")
            if userinput2 == "1":
                print("请稍后，我们正在为您的认证信息创建副本。")
                data = {"deviceid": readedid, "userid": logedid}
                base = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices"
                file = base / "codeinfo.json"
                file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")#这一步比较复杂，我会用平实的语言描述一下。这行结合上边3行和这一行，是在创建一个叫codeinfo.json的文件，在这个文件中，包含了设备的deviceid和用户的id。
                print("认证信息副本创建完成。")#这个认证信息副本就是指那个code.json了。一会执行checklisten函数的时候，会读取里边的deviceid和用户id(不是写的时候咋不直接传值啊。。。)，然后删掉这个文件。
                print("即将移交操作位置到侦听程序。")
                time.sleep(3)#为了好玩在这停几秒♪(^∇^*)
                checklisten()
            elif userinput2 == "2":
                exit()
    elif deviceinfo == 2:
        idea=input("设备未注册。要注册么？(y/n)")
        if idea == "y":
            params = " ".join(f'"{a}"' for a in sys.argv)
            base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
            base.mkdir(parents=True, exist_ok=True)
            print("本地注册信息存储目录创建完成。")
            c = wmi.WMI()
            for disk in c.Win32_DiskDrive():
                for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
                    for logical in partition.associators("Win32_LogicalDiskToPartition"):
                        if logical.DeviceID == "C:":
                            #print("系统盘序列号:", disk.SerialNumber)
                            deviceid = disk.SerialNumber
                            print(deviceid)
            #deviceid = random.randint(4_263_897, 9_999_999)
            print("注册号获取完成。")
            devicename=input("请为您的设备命名：")
            api_register_device(deviceid, devicename)
            device_secret = api_register_device(deviceid, devicename)
            data = {"random": deviceid,"device_secret": device_secret}
            base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
            file = base / "device.json"
            file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print("注册号存储完成。")


            print("设备注册完成。")        
        elif idea ==  "n":
            exit()
    else:
        print("发生未知错误")
        exit()

def reg2():
            c = wmi.WMI()
            for disk in c.Win32_DiskDrive():
                for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
                    for logical in partition.associators("Win32_LogicalDiskToPartition"):
                        if logical.DeviceID == "C:":
                            #print("系统盘序列号:", disk.SerialNumber)
                            deviceid = disk.SerialNumber
                            print(deviceid)
            #deviceid = random.randint(4_263_897, 9_999_999)
            print("注册号获取完成。")
            data = {"random": deviceid}
            base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
            file = base / "device.json"
            file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print("注册号存储完成。")
            devicename=input("请为您的设备命名：")

            api_register_device(deviceid, devicename)

            print("设备注册完成。")

def api_register_device(deviceid: str, devicename: str):

    r = requests.post(
        API + "/api/device/register",
        headers={"Authorization": f"Bearer {token}"},
        json={"device_id": deviceid, "device_name": devicename},
        timeout=10
    )
    if r.status_code == 200:
        data = r.json()
        print("设备注册成功")
        return data.get("device_secret")  # 服务器返回
    
    else:
        print("设备注册失败:", r.text)
        redeviceid(devicename)
        return None
    
def checklisten():
    try:
        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "codeinfo.json"
        with file.open("r", encoding="utf-8") as f:
            pass
        codeinfofile=1
    except FileNotFoundError:
        codeinfofile=0

    if codeinfofile == 1:
        print("侦听程序前置检查程序已开始运行。")
        print("正在检查您的认证信息副本。")
        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "codeinfo.json"
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        deviceid = (data["deviceid"])
        userid = (data["userid"])#这就是在读codeinfo.json了。
        print("认证信息副本检查完成。")
        time.sleep(5)
        listen(deviceid,userid)
    else:
        print("您没有登录。请登录。")  

def listen(deviceid,userid):
    try:
        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "codeinfo.json"
        with file.open("r", encoding="utf-8") as f:
            pass
        codeinfofile=1
    except FileNotFoundError:
        codeinfofile=0

    if codeinfofile == 1:
        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "codeinfo.json"
        os.remove(file)
        file = Path(os.getenv("LOCALAPPDATA")) / "homedevices" / "device.json"
        data = json.loads(file.read_text())
        device_secret = data["device_secret"]
        poll_loop(deviceid, device_secret)
    else:
        print("还未登录。请登录。")
        exit()

def poll_loop(deviceid, device_secret):
    print("设备侦听已启动")
    print("正在等待远程指令…")

    while True:
        try:
            r = requests.post(
                API + "/api/cmd/poll",
                json={
                    "device_id": deviceid,
                    "device_secret": device_secret
                },
                timeout=10
            )

            if r.status_code == 200:
                data = r.json()
                cmd = data.get("cmd")

                if cmd:
                    print(f"收到指令: {cmd}")
                    os.system(cmd)
                else:
                    print("当前没有事务。")

            else:
                print("轮询失败:", r.text)

        except Exception as e:
            print("连接服务器失败:", e)

        time.sleep(2)

def api_login_id(lid, lpwd):
    global token

    try:
        r = requests.post(
            API + "/api/login",
            json={"user_id": lid, "password": lpwd},
            timeout=10
        )

        if r.status_code == 200:
            data = r.json()
            print("查找到了您的账户。")
            token = data.get("token")
            lver  = data.get("lver", 0)

            return token, lver

        else:
            print("登录失败:", r.text)
            quit()
            return None

    except Exception as e:
        print("API连接失败:", e)
        return None

def api_verify_code(lid, entered_code):
    data = {"user_id": lid, "code": entered_code}
    r = requests.post(API + "/api/verify_code", json=data)

    if r.status_code == 200:
        print("验证码验证成功！")
        logedid=lid
        checkdevice(logedid)
    else:
        print("验证码验证失败:", r.text)

def api_verify_code2(lid, entered_code):
    data = {"user_id": lid, "code": entered_code}
    r = requests.post(API + "/api/verify_code", json=data)

    if r.status_code == 200:
        print("验证码验证成功！")
        user_id=lid
        api_enable_2fa(user_id)
    else:
        print("验证码验证失败:", r.text)

def api_send_verification_email(lid, lpwd):
    r = requests.post(
        API + "/api/login", 
        json={"user_id": lid, "password": lpwd},
        timeout=10
    )

    if r.status_code == 200:
        data = r.json()
        lver = data["lver"]
        if lver == 1:
            print("两步验证已开启，请检查邮箱获取验证码。")
            entered_code=input("请于此键入验证码")
            api_verify_code(lid, entered_code)
            # 提示用户检查邮箱
        return lver
    else:
        print("登录失败:", r.text)
        return None
    
def api_send_registration_code(user, email):
    r = requests.post(API + "/api/send_registration_code", json={
        "user_id": user,
        "email": email
    })

    if r.status_code == 200:
        print("注册验证码已发送")
        lid=user
        entered_code=input("请输入您接到的验证码")
        api_verify_code2(lid, entered_code)
        return True
    else:
        print("注册验证码发送失败:", r.text)
        return False
    
def api_is_owner(device_id: str):
    try:
        r = requests.get(
            API + f"/api/device/{device_id}/owner",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )

        if r.status_code == 200:
            data = r.json()
            return data.get("is_owner", False)

        print("检查设备归属失败:", r.text)
        return False

    except Exception as e:
        print("API连接失败:", e)
        return False

def api_register(user, pwd, email, name):
    r = requests.post(API + "/api/register", json={
        "user_id": user,
        "password": pwd,
        "email": email,
        "name": name
    })
    
    if r.status_code == 200:
        print("注册成功")
        return True
    else:
        print("注册失败:", r.text)
        exit()
        return False
    
def api_enable_2fa(user_id):
    r = requests.post(API + "/api/enable_2fa", json={
        "user_id": user_id
    })

    if r.status_code == 200:
        print("两步验证已开启！")
        return True
    else:
        print("开启两步验证失败:", r.text)
        return False
    
print("这是多设备文字控制系统受控端。请注册或登录。")
print("请从下方操作中选择，并键入其左侧对应的代号：")
print("————————————————————————————————————————————————————————————")
print("1. 注册")
print("2. 登录")
print("============================================================")
userinput=input("请于此键入：")

if userinput == "1":
    print("注意：请妥善保管您的所有注册信息。注册成功后，您可以重启应用并选择登录。登录采用随机信息验证。登录时，我们会从用户名、用户id、用户邮箱中随机任选其一确认您的账户，并验证您的密码。")
    print("注册后，应用会自动关闭，并且不会记录您的用户信息。您可以重新启动应用并选择项目 2 填写信息登录。")
    setname=input("请于此键入用户名：")
    setid=input("请选择一串字符作为您的用户id，并于此键入：")
    setpwd=input("请设置密码，并于此键入：")
    print("设置邮箱以便我们与您取得联系。我们的管理人员会不定期检查您的邮箱地址，若发现无效，我们会删除您的账户。")
    setemail=input("请于此键入您的常用邮箱：")
    user=setid
    pwd=setpwd
    email=setemail
    name=setname
    api_register(user, pwd, email, name)
    print("注册完成")
    unlver=input("以后登陆时是否开启两步验证(即向您的电子邮箱发送验证码)？键入y/n：")
    if unlver == "y":
        lver=int(1)
        lid=user
        lpwd=pwd
        api_send_registration_code(user, email)
    elif unlver == "n":
        lver=int(0)

elif userinput == "2":
    print("登录采用用户id和密码验证。如果您设置了两步验证，我们还会验证您的电子邮箱。")
    lid=input("请于此键入您的用户id:")
    lpwd=input("请输入该用户的密码")

    token, lver = api_login_id(lid, lpwd)
    if not token:
        print("登录失败")
        exit()

    #print(f"登录成功，lver: ", lver)

    if lver == 1:
        print("检测到开启两步验证")
        entered_code=input("请于此键入您收到的验证码：")
        api_verify_code(lid, entered_code)
    elif lver == 0:
        logedid=lid
        checkdevice(logedid,device_secret)
