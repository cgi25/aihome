import pymysql
import random
import os
import ctypes, sys
from pathlib import Path
import json
import time
import sys, subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import wmi
import json


# 读取配置文件
try:
    with open("./config.json", "r", encoding='utf-8') as f:
        config = json.loads(f.read())
except Exception as e:
    print(f"读取配置文件失败：{e}")
    sys.exit(-1)

db = pymysql.connect(host=config["database"]["host"],
                     port=config["database"]["port"],
                     user=config["database"]["user"],
                     password=config["database"]["password"],
                     database='aihomeuserinfo')
cursor = db.cursor()

db2 = pymysql.connect(host=config["database"]["host"],
                      port=config["database"]["port"],
                      user=config["database"]["user"],
                      password=config["database"]["password"],
                      database='aihomeuserinfo')
cursor2 = db2.cursor()

devicedb = pymysql.connect(host=config["database"]["host"],
                           port=config["database"]["port"],
                           user=config["database"]["user"],
                           password=config["database"]["password"],
                           database='aihomedevicesinfo')
devicedbconn = devicedb.cursor()

code = pymysql.connect(host=config["database"]["host"],
                       port=config["database"]["port"],
                       user=config["database"]["user"],
                       password=config["database"]["password"],
                       database='code',autocommit=True)
codeconn = code.cursor()

def redeviceid(devicename, logedid):
    print(devicename)
    print(logedid)
    print("您的设备为虚拟机/云服务器，无硬盘序列号，deviceid创建失败。")
    print("我们将改为使用10位随机数作为您的deviceid。这可能会降低控制的准确性与安全性。")
    allow1=input("要继续吗？(y/n)")
    if allow1 == "y":
        deviceid = random.uniform(1000000000, 9999999999)
        info = (devicename,deviceid,logedid)
        sql = "INSERT INTO aihomedevicesinfo (name, id, master) VALUES (%s, %s, %s)"
        devicedbconn.execute(sql, info)
        devicedb.commit()          
        devicedbconn.close()
        devicedb.close()
        data = {"random": deviceid}
        base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
        file = base / "device.json"
        file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("注册号存储完成。")
        print("设备注册完成。")
        print("正在尝试注册侦听服务。")
        info2 = (deviceid,logedid)
        sql = "INSERT INTO code (deviceid, userid) VALUES (%s, %s)"
        codeconn.execute(sql, info2)
        code.commit()
        codeconn.close()
        code.close()
    elif allow1 == "n":
        exit()
    else:
        exit()

    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def checkdevice():
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
            sql = "SELECT master FROM aihomedevicesinfo WHERE id = %s"
            devicedbconn.execute(sql, (readedid,))
            unmaster = devicedbconn.fetchall()#unmaster是指未格式化的，根据从本地json读取到的deviceid(即上文的readedid)从数据库中获取到的设备主人的id。
            master = unmaster[0][0]#master：这里是在格式化设备主人的id，便于与已登录账户的id(即下文的logedid)进行比较。
            sql = "SELECT name FROM aihomeuserinfo WHERE id = %s"
            cursor.execute(sql, (logedid,))
            unreadedname = cursor.fetchall()#unreadedname是指未格式化的，根据已登录账户的id从数据库中查询出的其id。
            readedname=unreadedname[0][0]#readedname：这是在格式化已登录账户的id，便于欢迎页面或警告页面的展示。
            sql = "SELECT email FROM aihomeuserinfo WHERE name = %s"
            cursor.execute(sql, (master,))
            unmasteremail = cursor.fetchall()#unmasteremail是指未格式化的，使用上文提到的方式获取到的设备主人账户的id(即master)从数据库获取到设备主人的email。
            masteremail=unmasteremail[0][0]#masteremail：这里是在格式化设备主人的email，便于欢迎页面或警告页面的展示。

            '''
            =========================================总结注释==================================================================================总结注释=========================================
            通过上面的内容，我们获取到了以下信息(变量)
            readedid:本地存储的deviceid
            master:设备主人账户的id
            readedname:已登录账户的id
            masteremail:设备主任的email
            =========================================总结注释==================================================================================总结注释=========================================
            '''

            if readedname == master:
            #这是在判断已登录账户的id和设备主人的id是否相同。这个if是相同时。
                sql = "SELECT name FROM aihomedevicesinfo WHERE id = %s"
                devicedbconn.execute(sql, (readedid,))
                undname = devicedbconn.fetchall()#undname是指未格式化的，根据已登录账户的id从数据库中查询出的设备的名称。
                dname = undname[0][0]#dname：这是在格式化已获取的设备名称，便于下方的展示。
                print("您的设备名称如下")
                print(dname)
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
            elif readedname != master:#readedname是指根据当前登录的账户的id从数据库中查询到的name，非设备主人name。
                sql = "SELECT name FROM aihomedevicesinfo WHERE id = %s"
                devicedbconn.execute(sql, (readedid,))
                undname = devicedbconn.fetchall()
                dname = undname[0][0]
                print("这不是你的设备或该设备不由你管理。请联系设备主人/管理者。我们有权获取的信息如下：")
                print("设备名称：")
                print(dname)
                print("设备主人/管理者名称：")
                print(master)
                print("设备主人/管理者电子邮箱：")
                print(masteremail)
                time.sleep(30)
                exit()
        else:
            print("本地认证信息已损坏，原有设备信息已丢失。即将执行修复操作，即重新注册设备。")
            reg2()
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
            sql = "SELECT EXISTS(SELECT name FROM aihomedevicesinfo WHERE id=%s)"
            devicedbconn.execute(sql, (deviceid,))
            res = devicedbconn.fetchone() 
            exists = bool(res and res[0])





            if not exists:
                print("注册号确认完成。")
                data = {"random": deviceid}
                base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
                file = base / "device.json"
                file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                print("注册号存储完成。")
                devicename=input("请为您的设备命名：")
                info = (devicename,deviceid,logedid)
                sql = "INSERT INTO aihomedevicesinfo (name, id, master) VALUES (%s, %s, %s)"
                try:
                    devicedbconn.execute(sql, info)
                except pymysql.err.IntegrityError:
                    redeviceid(devicename, logedid) 
                devicedb.commit()
                devicedbconn.close()
                devicedb.close()
                print("设备注册完成。")
                print("正在尝试注册侦听服务。")
                info2 = (deviceid,logedid)
                sql = "INSERT INTO code (deviceid, userid) VALUES (%s, %s)"
                codeconn.execute(sql, info2)
                code.commit()
                codeconn.close()
                code.close()
            
            else:
                print("注册号有误。您的硬盘序列号在我们的服务器上注册过，但您不必担心，我们可以为您重新获取注册号。")
                print("我们将改为使用7位随机数作为您的deviceid。这可能会降低控制的准确性与安全性。如果您不同意，请在10秒内退出注册程序，并停止使用该软件，或者咨询服务人员cgi2024@outlook.com寻求帮助。")
                for i in range(10):
                    print(f"剩余时间：{i}s")
                    time.sleep(1)
                time.sleep(1)
                print("看起来您同意以随机数的形式生成deviceid。我们将继续操作。")
                deviceid = random.randint(4_263_897, 9_999_999)
                print("注册号获取完成。")
                sql = "SELECT EXISTS(SELECT name FROM aihomedevicesinfo WHERE id=%s)"
                devicedbconn.execute(sql, (deviceid,))
                res = devicedbconn.fetchone() 
                exists = bool(res and res[0])
                if not exists:
                    print("注册号确认完成。")
                    data = {"random": deviceid}
                    base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
                    file = base / "device.json"
                    file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    print("注册号存储完成。")
                    devicename=input("请为您的设备命名：")
                    info = (devicename,deviceid,logedid)
                    sql = "INSERT INTO aihomedevicesinfo (name, id, master) VALUES (%s, %s, %s)"
                    devicedbconn.execute(sql, info)
                    devicedb.commit()
                    devicedbconn.close()
                    devicedb.close()
                    print("设备注册完成。")
                    print("正在尝试注册侦听服务。")
                    info2 = (deviceid,logedid)
                    sql = "INSERT INTO code (deviceid, userid) VALUES (%s, %s)"
                    codeconn.execute(sql, info2)
                    code.commit()
                    codeconn.close()
                    code.close()
                else:
                    print("两次随机注册号均已被占用。请重启注册程序。")
                
                
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

            sql = "SELECT EXISTS(SELECT name FROM aihomedevicesinfo WHERE id=%s)"
            devicedbconn.execute(sql, (deviceid,))
            res = devicedbconn.fetchone() 
            exists = bool(res and res[0])





            if not exists:
                print("注册号确认完成。")
                data = {"random": deviceid}
                base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
                file = base / "device.json"
                file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                print("注册号存储完成。")
                devicename=input("请为您的设备命名：")
                info = (devicename,deviceid,logedid)
                sql = "INSERT INTO aihomedevicesinfo (name, id, master) VALUES (%s, %s, %s)"
                devicedbconn.execute(sql, info)
                devicedb.commit()
                devicedbconn.close()
                devicedb.close()
                print("设备注册完成。")
                print("正在尝试注册侦听服务。")
                info2 = (deviceid,logedid)
                sql = "INSERT INTO code (deviceid, userid) VALUES (%s, %s)"
                codeconn.execute(sql, info2)
                code.commit()
                codeconn.close()
                code.close()
            else:
                print("注册号有误，即将重新获取注册号。")
                deviceid = random.randint(4_263_897, 9_999_999)
                print("注册号获取完成。")
                sql = "SELECT EXISTS(SELECT name FROM aihomedevicesinfo WHERE id=%s)"
                devicedbconn.execute(sql, (deviceid,))
                res = devicedbconn.fetchone() 
                exists = bool(res and res[0])
                if not exists:
                    print("注册号确认完成。")
                    data = {"random": deviceid}
                    base = Path(os.environ["LOCALAPPDATA"]) / "homedevices"
                    file = base / "device.json"
                    file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    print("注册号存储完成。")
                    devicename=input("请为您的设备命名：")
                    info = (devicename,deviceid,logedid)
                    sql = "INSERT INTO aihomedevicesinfo (name, id, master) VALUES (%s, %s, %s)"
                    devicedbconn.execute(sql, info)
                    devicedb.commit()
                    devicedbconn.close()
                    devicedb.close()
                    print("设备注册完成。")
                    print("正在尝试注册侦听服务。")
                    info2 = (deviceid,logedid)
                    sql = "INSERT INTO code (deviceid, userid) VALUES (%s, %s)"
                    codeconn.execute(sql, info2)
                    code.commit()
                    codeconn.close()
                    code.close()
                else:
                    print("两次随机注册号均已被占用。请重启注册程序。")

def checklisten():
    try:
        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "codeinfo.json"
        with file.open("r", encoding="utf-8") as f:
            pass
        codeinfofile=1
    except FileNotFoundError:
        codeinfofile=0

    if codeinfofile == 1:
        
        code = pymysql.connect(host='154.37.215.80',port=3006,user='root',password='4wRlHrSQjl4pqZqP',database='code')
        codeconn = code.cursor()



        print("侦听程序前置检查程序已开始运行。")
        print("正在检查您的认证信息副本。")
        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "codeinfo.json"
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        deviceid = (data["deviceid"])
        userid = (data["userid"])#这就是在读codeinfo.json了。
        print("认证信息副本检查完成。")
        time.sleep(5)
        print("开始检查您的侦听服务注册情况。")
        sql = "SELECT userid FROM code WHERE deviceid = %s"
        print(userid)
        print(deviceid)
        codeconn.execute(sql, (deviceid,))
        unmaster = codeconn.fetchone() 
        print(unmaster)
        master=unmaster[0][0]
        print(master)
        if master == userid:
            listen()
        else: 
            print("不是你的设备。")
    else:
        print("您没有登录。请登录。")  

def listen():
    try:
        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "codeinfo.json"
        with file.open("r", encoding="utf-8") as f:
            pass
        codeinfofile=1
    except FileNotFoundError:
        codeinfofile=0


    if codeinfofile == 1:

        file = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "homedevices" / "codeinfo.json"
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        os.remove(file)
        deviceid = (data["deviceid"])
        userid = (data["userid"])
        def get_column_value():
            codeconn.execute(f"SELECT code FROM code WHERE deviceid = %s", (deviceid,))
            result = codeconn.fetchone()
            return result[0] if result else None
        while True:
            sql = "UPDATE aihomedevicesinfo SET ifonline = 1, lastseen = NOW() WHERE id = %s"
            devicedbconn.execute(sql, (deviceid,))
            devicedb.commit()   
            value = get_column_value()
            if value is None:
                print("当前没有事务。")
            else:
                os.system(value)
                sql = "UPDATE code SET code = NULL WHERE deviceid = %s"
                codeconn.execute(sql, (deviceid,))
                code.commit()
                print(f"操作：执行命令{value}")
            time.sleep(1)
    else:
        print("还未登录。请登录。")
        subprocess.Popen([sys.executable, r".\main.py"], creationflags=subprocess.CREATE_NEW_CONSOLE); sys.exit(0)

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
    rcode = random.randint(256598, 998526)
    sender_email = config["smtp"]["email"]
    receiver_email = setemail
    password = config["smtp"]["password"]

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "多设备文字控制系统注册"
    message.attach(MIMEText(f"这是多设备文字控制系统注册的邮箱确认环节。测试。这是您的验证码：{rcode}"))
    with smtplib.SMTP("smtp.qq.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
    print(f"我们刚刚向{setemail}(即您注册时填入的邮箱)发送了一封带有6位验证码的电子邮件。请查看这封邮件并填入验证码。")
    print(rcode)
    uninputrcode=input("请于此键入验证码：")
    inputrcode=int(uninputrcode)
    #print(inputrcode)
    #print(rcode)
    if inputrcode == rcode:
        print("邮箱验证完成")
        unlver=input("以后登陆时是否开启两步验证(即向您的电子邮箱发送验证码)？键入y/n：")
        if unlver == "y":
            lver=int(1)
        elif unlver == "n":
            lver=int(0)
        try:
            info = (setname,setid,setpwd,setemail,lver)
            sql = "INSERT INTO aihomeuserinfo (name, id, pwd, email, lver) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, info)
            db.commit()
            cursor.close()
            db.close()
            print("注册完成")
        except pymysql.err.IntegrityError:
            print("用户id或用户名有重合，请重新注册。")
            exit()
    else:
        print("验证码错误，注册终止。")

elif userinput == "2":
    print("登录采用随机信息验证。我们会从用户名、用户id、用户邮箱中随机任选其一确认您的账户，并验证您的密码。如果您设置了两步验证，我们还会验证您的电子邮箱。")
    lway = random.randint(1, 3)
    if lway==1:
        lname=input("请于此键入您的用户名:")
        try:
            sql = "SELECT pwd FROM aihomeuserinfo WHERE name = %s"
            cursor.execute(sql, (lname,))
            checkpwds = cursor.fetchall()

        
            sql = "SELECT lver FROM aihomeuserinfo WHERE name = %s"
            cursor.execute(sql, (lname,))
            lver = cursor.fetchall()[0][0]
            #print(lver)

            sql = "SELECT email FROM aihomeuserinfo WHERE name = %s"
            cursor.execute(sql, (lname,))
            lveremail = cursor.fetchall()[0][0]
            #print(lveremail)

            sql = "SELECT id FROM aihomeuserinfo WHERE name = %s"
            cursor2.execute(sql, (lname,))
            logedid0 = cursor2.fetchall()
            logedid = logedid0[0][0]
            #print(checkpwd)

            row = cursor.fetchone()
            sql = "SELECT EXISTS(SELECT pwd FROM aihomeuserinfo WHERE name=%s)"
            cursor.execute(sql, (lname,))
            res = cursor.fetchone() 
            exists = bool(res and res[0])
        except IndexError:
            print("不存在的用户。")
            exit()

        if not exists:
            print("滚木")
        else:
            if checkpwds:
                checkpwd = checkpwds[0][0]
                #print(checkpwd)
                lpwd=input("请输入该用户的密码")

                if (lpwd) == (checkpwd):
                    print("密码认证成功")                    
                    if lver == 1:
                            print("您的账户在注册时启用了两步验证。我们将验证您的电子邮箱。")
                            rcode = random.randint(256598, 998526)
                            sender_email = config["smtp"]["email"]
                            receiver_email = lveremail
                            password = config["smtp"]["password"]

                            message = MIMEMultipart()
                            message["From"] = sender_email
                            message["To"] = receiver_email
                            message["Subject"] = "多设备文字控制系统登录"
                            message.attach(MIMEText(f"这是多设备文字控制系统注册的邮箱确认环节。测试。这是您的验证码：{rcode}"))
                            with smtplib.SMTP("smtp.qq.com", 587) as server:
                                server.starttls()
                                server.login(sender_email, password)
                                server.sendmail(sender_email, receiver_email, message.as_string())
                                server.quit()
                            print(f"我们刚刚向{lveremail}(即您账户的电子邮箱)发送了一封带有6位验证码的电子邮件。请查看这封邮件并填入验证码。")
                            uninputrcode=input("请于此键入验证码：")
                            inputrcode=int(uninputrcode)
                            #print(inputrcode)
                            #print(rcode)
                            if inputrcode == rcode:
                                print("邮箱验证完成")
                                checkdevice()
                            else:
                                print("验证码错误，操作终止。")
                                exit()
                    elif lver==0:
                        print("您的账户没有启用两步验证。")
                        print("登陆完成。")
                        checkdevice()
                        

                    
                else:
                    print("密码错误，我阐述你的梦")






    elif lway==2:
        lid=input("请于此键入您的用户id:")
        try:
            sql = "SELECT pwd FROM aihomeuserinfo WHERE id = %s"
            cursor.execute(sql, (lid,))
            checkpwds = cursor.fetchall()
    
            #print(checkpwd)

            sql = "SELECT lver FROM aihomeuserinfo WHERE id = %s"
            cursor.execute(sql, (lid,))
            lver = cursor.fetchall()[0][0]

            sql = "SELECT email FROM aihomeuserinfo WHERE id = %s"
            cursor.execute(sql, (lid,))
            lveremail = cursor.fetchall()[0][0]

            row = cursor.fetchone()
            sql = "SELECT EXISTS(SELECT pwd FROM aihomeuserinfo WHERE id=%s)"
            cursor.execute(sql, (lid,))
            res = cursor.fetchone() 
            exists = bool(res and res[0])
        except IndexError:
            print("不存在的用户。")    
            exit()

        if not exists:
            print("滚木")
        else:
            if checkpwds:
                checkpwd = checkpwds[0][0]
                #print(checkpwd)
                lpwd=input("请输入该用户的密码")

                if (lpwd) == (checkpwd):
                    print("密码认证成功")                    
                    if lver == 1:
                            print("您的账户在注册时启用了两步验证。我们将验证您的电子邮箱。")
                            rcode = random.randint(256598, 998526)
                            sender_email = config["smtp"]["email"]
                            receiver_email = lveremail
                            password = config["smtp"]["password"]

                            message = MIMEMultipart()
                            message["From"] = sender_email
                            message["To"] = receiver_email
                            message["Subject"] = "多设备文字控制系统登录"
                            message.attach(MIMEText(f"这是多设备文字控制系统注册的邮箱确认环节。测试。这是您的验证码：{rcode}"))
                            with smtplib.SMTP("smtp.qq.com", 587) as server:
                                server.starttls()
                                server.login(sender_email, password)
                                server.sendmail(sender_email, receiver_email, message.as_string())
                                server.quit()
                            print(f"我们刚刚向{lveremail}(即您账户的电子邮箱)发送了一封带有6位验证码的电子邮件。请查看这封邮件并填入验证码。")
                            uninputrcode=input("请于此键入验证码：")
                            inputrcode=int(uninputrcode)
                            #print(inputrcode)
                            #print(rcode)
                            if inputrcode == rcode:
                                print("邮箱验证完成")
                                logedid = lid
                                checkdevice()
                            else:
                                print("验证码错误，操作终止。")
                                exit()
                    elif lver==0:
                        print("您的账户没有启用两步验证。")
                        logedid = lid
                        print("登陆完成。")
                        checkdevice()
                else:
                    print("我阐述你的梦")






    elif lway==3:
        lemail=input("请于此键入您的邮箱:")
        try:
            sql = "SELECT pwd FROM aihomeuserinfo WHERE email = %s"
            cursor.execute(sql, (lemail,))
            checkpwds = cursor.fetchall()

            sql = "SELECT id FROM aihomeuserinfo WHERE email = %s"
            cursor2.execute(sql, (lemail,))
            logedid0 = cursor2.fetchall()
            logedid = logedid0[0][0]

            row = cursor.fetchone()
            sql = "SELECT EXISTS(SELECT pwd FROM aihomeuserinfo WHERE email=%s)"
            cursor.execute(sql, (lemail,))
            res = cursor.fetchone() 
            exists = bool(res and res[0])

            sql = "SELECT lver FROM aihomeuserinfo WHERE email = %s"
            cursor.execute(sql, (lemail,))
            lver = cursor.fetchall()[0][0]

            sql = "SELECT id FROM aihomeuserinfo WHERE email = %s"
            cursor2.execute(sql, (lemail,))
            logedid0 = cursor2.fetchall()
            logedid = logedid0[0][0]
        except IndexError:
            print("不存在的用户。")
            exit()
        lveremail = lemail
        if not exists:
            print("滚木")
        else:
            if checkpwds:
                checkpwd = checkpwds[0][0]
                #print(checkpwd)
                lpwd=input("请输入该用户的密码")

                if (lpwd) == (checkpwd):
                    print("密码认证成功")                    
                    if lver == 1:
                            print("您的账户在注册时启用了两步验证。我们将验证您的电子邮箱。")
                            rcode = random.randint(256598, 998526)
                            sender_email = config["smtp"]["email"]
                            receiver_email = lveremail
                            password = config["smtp"]["password"]

                            message = MIMEMultipart()
                            message["From"] = sender_email
                            message["To"] = receiver_email
                            message["Subject"] = "多设备文字控制系统登录"
                            message.attach(MIMEText(f"这是多设备文字控制系统注册的邮箱确认环节。测试。这是您的验证码：{rcode}"))
                            with smtplib.SMTP("smtp.qq.com", 587) as server:
                                server.starttls()
                                server.login(sender_email, password)
                                server.sendmail(sender_email, receiver_email, message.as_string())
                                server.quit()
                            print(f"我们刚刚向{lveremail}(即您账户的电子邮箱)发送了一封带有6位验证码的电子邮件。请查看这封邮件并填入验证码。")
                            uninputrcode=input("请于此键入验证码：")
                            inputrcode=int(uninputrcode)
                            #print(inputrcode)
                            #print(rcode)
                            if inputrcode == rcode:
                                print("邮箱验证完成")
                                checkdevice()
                            else:
                                print("验证码错误，操作终止。")
                                exit()
                    elif lver==0:
                        print("您的账户没有启用两步验证。")
                        print("登陆完成。")
                        checkdevice()
                else:
                    print("我阐述你的梦")







    cursor.close()
    db.close()