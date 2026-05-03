import os
import time
import hmac
import hashlib
import smtplib
import fastapi
from fastapi import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import pymysql
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from dotenv import load_dotenv
from fastapi import Path
load_dotenv()
app = FastAPI()
class VerifyReq(BaseModel):
    user_id: str
    code: str   


# 环境变量加载（用于存储敏感数据）
DB_HOST = "YOUR_DB_HOST"          # 你现在用的数据库地址
DB_PORT = 1145          # 你现在用的数据库端口
DB_USER = "YOUR_DB_USER"          # 你现在用的数据库用户
DB_PASS = "YOUR_DB_PASS"
DB_USERINFO = os.getenv("AIHOME_DB_USERINFO", "aihomeuserinfo")
DB_DEVICE = os.getenv("AIHOME_DB_DEVICE", "aihomedevicesinfo")
DB_CODE = os.getenv("AIHOME_DB_CODE", "code")
SMTP_SERVER = "smtp.qq.com"  # 替换为你自己的邮件服务器地址
SMTP_PORT = 587  # SMTP端口
SENDER_EMAIL = "your@mail.com"  # 发送邮箱
SENDER_PASSWORD = "yourpassword"  # 发送邮箱的授权码或密码

TOKEN_SECRET = os.getenv("AIHOME_TOKEN_SECRET", "your-secret")
TOKEN_SALT = "aihome-token-v1"
token_ser = URLSafeTimedSerializer(TOKEN_SECRET, salt=TOKEN_SALT)


def send_verification_email(receiver_email):
    # 生成随机验证码
    verification_code = random.randint(100000, 999999)

    # 创建邮件内容
    subject = "您的验证码"
    body = f"您的验证码是: {verification_code}"

    # 创建 MIME 邮件
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # 发送邮件
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # 加密连接
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        return verification_code
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return None
#数据库连接函数
def db_conn(dbname: str):
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=dbname, charset="utf8mb4",
        autocommit=True
    )
#数据模型,用于验证输入数据
class LoginReq(BaseModel):
    user_id: str
    password: str
class PushCmdReq(BaseModel):
    device_id: str
    cmd: str
class PollReq(BaseModel):
    device_id: str
    device_secret: str
class RegisterReq(BaseModel):
    device_id: str
    device_name: str
class RegisterUserReq(BaseModel):
    user_id: str
    password: str
    email: str
    name: str
class Enable2FAReq(BaseModel):
    user_id: str
class SendRegCodeReq(BaseModel):
    user_id: str
    email: str
#生成token
def issue_token(user_id: str) -> str:
    return token_ser.dumps({"uid": user_id, "iat": int(time.time())})
#验证token
def verify_token(auth_header: str) -> str:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization: Bearer <token>")
    token = auth_header.split(" ", 1)[1].strip()
    try:
        data = token_ser.loads(token, max_age=3600)  # 1小时过期
    except SignatureExpired:
        raise HTTPException(401, "Token expired")
    except BadSignature:
        raise HTTPException(401, "Invalid token")
    return data["uid"]
#用户登录,返回 token
@app.post("/api/login")
def login(req: LoginReq):
    conn = db_conn(DB_USERINFO)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pwd, lver, email FROM aihomeuserinfo WHERE id=%s", (req.user_id,))
            row = cur.fetchone()

            if not row or row[0] != req.password:
                raise HTTPException(403, "Bad credentials")

            lver = row[1]
            email = row[2]  # 获取用户的邮箱

    finally:
        conn.close()

    # 如果开启了两步验证（lver == 1），发送验证码邮件
    if lver == 1:
        verification_code = send_verification_email(email)
        if verification_code:
            # 在数据库中存储验证码，用于后续验证
            conn = db_conn(DB_USERINFO)
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE aihomeuserinfo SET verification_code = %s WHERE id = %s", 
                                (verification_code, req.user_id))
            finally:
                conn.close()

    return {
        "token": issue_token(req.user_id),
        "lver": lver
    }
#设备注册,返回 device_secret
@app.post("/api/device/register")
def register_device(req: RegisterReq, authorization: Optional[str] = Header(None)):
    uid = verify_token(authorization)
    device_secret = hashlib.sha256(f"{uid}:{req.device_id}:{TOKEN_SECRET}".encode()).hexdigest()

    # aihomedevicesinfo upsert
    conn = db_conn(DB_DEVICE)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO aihomedevicesinfo (name,id,master,device_secret) VALUES (%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE name=VALUES(name), master=VALUES(master), device_secret=VALUES(device_secret)",
                (req.device_name, req.device_id, uid, device_secret)
            )
    finally:
        conn.close()

    # code 表预建行（侦听服务那一行）
    conn2 = db_conn(DB_CODE)
    try:
        with conn2.cursor() as cur2:
            cur2.execute(
                "INSERT INTO code (deviceid, userid, code) VALUES (%s,%s,NULL) "
                "ON DUPLICATE KEY UPDATE userid=VALUES(userid)",
                (req.device_id, uid)
            )
    finally:
        conn2.close()

    return {"device_secret": device_secret}
#推送命令
@app.post("/api/cmd/push")
def push_cmd(req: PushCmdReq, authorization: Optional[str] = Header(None)):
    uid = verify_token(authorization)
    conn = db_conn(DB_DEVICE)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT master FROM aihomedevicesinfo WHERE id=%s", (req.device_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Device not found")
            if row[0] != uid:
                raise HTTPException(403, "Not your device")
    finally:
        conn.close()

    # 更新命令
    conn2 = db_conn(DB_CODE)
    try:
        with conn2.cursor() as cur2:
            cur2.execute("UPDATE code SET code=%s WHERE deviceid=%s", (req.cmd, req.device_id))
    finally:
        conn2.close()

    return {"ok": True}
#轮询
@app.post("/api/cmd/poll")
def poll(req: PollReq):
    # 1) 校验 device_secret
    conn = db_conn(DB_DEVICE)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT device_secret FROM aihomedevicesinfo WHERE id=%s", (req.device_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Device not found")
            if row[0] != req.device_secret:
                raise HTTPException(403, "Bad device secret")

            # 2) 更新在线状态（如果你表里有这些字段）
            try:
                cur.execute(
                    "UPDATE aihomedevicesinfo SET ifonline=1, lastseen=NOW() WHERE id=%s",
                    (req.device_id,)
                )
            except Exception:
                pass  # 没有字段也不影响轮询拿命令

    finally:
        conn.close()

    # 3) 取出命令并清空
    cmd = None
    conn2 = db_conn(DB_CODE)
    try:
        with conn2.cursor() as cur2:
            cur2.execute("SELECT code FROM code WHERE deviceid=%s", (req.device_id,))
            row = cur2.fetchone()
            cmd = row[0] if row and row[0] else None
            if cmd:
                cur2.execute("UPDATE code SET code=NULL WHERE deviceid=%s", (req.device_id,))
    finally:
        conn2.close()

    return {"cmd": cmd}
#邮箱验证码
@app.post("/api/verify_code")
def verify_code(req: VerifyReq):

    user_id = req.user_id
    entered_code = req.code

    conn = db_conn(DB_USERINFO)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT verification_code FROM aihomeuserinfo WHERE id=%s",
                (user_id,)
            )
            row = cur.fetchone()

            if not row:
                raise HTTPException(404, "User not found")

            stored_code = str(row[0])

            if stored_code != str(entered_code):
                raise HTTPException(400, "验证码错误")

            # 清空验证码
            cur.execute(
                "UPDATE aihomeuserinfo SET verification_code=NULL WHERE id=%s",
                (user_id,)
            )

    finally:
        conn.close()

    return {"ok": True}
@app.get("/api/device/{device_id}/owner")
def device_owner(device_id: str = Path(...), authorization: Optional[str] = Header(None)):
    uid = verify_token(authorization)

    conn = db_conn(DB_DEVICE)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT master,name FROM aihomedevicesinfo WHERE id=%s",
                (device_id,)
            )
            row = cur.fetchone()

            if not row:
                raise HTTPException(404, "Device not found")

            master, name = row[0], row[1]

    finally:
        conn.close()

    return {
        "device_id": device_id,
        "device_name": name,
        "master": master,
        "is_owner": (str(master) == str(uid))
    }
@app.post("/api/register")
def register_user(req: RegisterUserReq):

    conn = db_conn(DB_USERINFO)
    try:
        with conn.cursor() as cur:

            # 是否已存在
            cur.execute(
                "SELECT id FROM aihomeuserinfo WHERE id=%s",
                (req.user_id,)
            )
            if cur.fetchone():
                raise HTTPException(400, "用户已存在")

            # 写入数据库
            cur.execute(
                """
                INSERT INTO aihomeuserinfo
                (id, pwd, email, lver, name)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    req.user_id,
                    req.password,
                    req.email,
                    0,            # 默认未开启两步验证
                    req.name      # 昵称
                )
            )

    finally:
        conn.close()

    return {"ok": True, "msg": "注册成功"}
@app.post("/api/user/enable_2fa")
def enable_2fa(req: Enable2FAReq):

    conn = db_conn(DB_USERINFO)
    try:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT email FROM aihomeuserinfo WHERE id=%s",
                (req.user_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "用户不存在")

            email = row[0]

            code = send_verification_email(email)
            if not code:
                raise HTTPException(500, "邮件发送失败")

            cur.execute(
                "UPDATE aihomeuserinfo SET verification_code=%s WHERE id=%s",
                (code, req.user_id)
            )

    finally:
        conn.close()

    return {"msg": "验证码已发送"}
@app.post("/api/enable_2fa")
def enable_2fa(req: Enable2FAReq):
    user_id = req.user_id
    # 这里我们不再验证验证码了，前面已经处理过
    conn = db_conn(DB_USERINFO)
    try:
        with conn.cursor() as cur:
            # 将 lver 设置为 1，表示开启了两步验证
            cur.execute("UPDATE aihomeuserinfo SET lver = 1 WHERE id = %s", (user_id,))
            conn.commit()
    finally:
        conn.close()

    return {"ok": True}
@app.post("/api/send_registration_code")
def send_registration_code(req: SendRegCodeReq):
    user_id = req.user_id
    email = req.email

    conn = db_conn(DB_USERINFO)
    try:
        with conn.cursor() as cur:
            # 生成验证码并发送到邮箱
            verification_code = send_verification_email(email)

            # 将验证码存入数据库
            cur.execute(
                "UPDATE aihomeuserinfo SET verification_code=%s WHERE id=%s",
                (verification_code, user_id)
            )

    finally:
        conn.close()

    return {"msg": "验证码已发送"}