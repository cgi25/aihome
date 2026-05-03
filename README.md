### 你好！感谢你来到我的项目

这个项目的主要功能是：用户在网页上用平常的语言描述需要对一台电脑进行的操作，服务端使用ai转译成可执行的cmd命令，随后下发给这台电脑令其执行，使其完成用户的要求，达到使用户可以远程便捷地操控用户的计算机的目的。

您可以选择直接从仓库下载cgi26-api-used.py并运行以使用cgi26的已部署好的服务（指无需您部署服务端），也可以选择使用仓库中的server.py和main.py自行组建服务端。

## 部署教程

### 1.在服务器下载服务端。
```shell
git clone https://github.com/cgi25/aihome.git
cd ./aihome
```



### 2.将server.py中的信息进行修改。

`DB_HOST = "YOUR_DB_HOST"`          # 改为您的数据库地址\
`DB_PORT = XXXX`                    # 改为您的数据库端口\
`DB_USER = "YOUR_DB_USER"`          # 改为您的数据库用户\
`DB_PASS = "YOUR_DB_PASS"`          # 改为您的数据库密码\
`DB_USERINFO = os.getenv("AIHOME_DB_USERINFO", "aihomeuserinfo")`\
`DB_DEVICE = os.getenv("AIHOME_DB_DEVICE", "aihomedevicesinfo")`\
`DB_CODE = os.getenv("AIHOME_DB_CODE", "code")`\
`SMTP_SERVER = "smtp.qq.com"`       # 改为您的邮件服务器地址\
`SMTP_PORT = XXX`                   # 改为您的SMTP端口\
`SENDER_EMAIL = "your@mail.com"`    # 改为您的发送邮箱\
`SENDER_PASSWORD = "yourpassword"`  # 改为您的SMTP密码

将上述信息根据注释改为您的信息。

## 3.创建数据库结构
确保您的服务器安装了MySQL。推荐版本5.2.3
根据aihomeuserinfo.sql aihomedevicesinfo.sql code.sql创建三个数据库。\
(什么？你问我为什么不写在一个数据库里？因为我写的时候还啥也不懂…)

## 4.安装依赖并启动服务端。
```shell
pip install fastapi pydantic uvicorn pymysql python-dotenv itsdangerous && uvicorn server:app --host 0.0.0.0 --port 8010
```
注意：防火墙放行8010端口

此时，您的API地址应为ip地址:8010(例如:111.11.111.11:8010)。您可以通过反向代理来使用域名。

## 5.修改客户端。
下载main.py，将11行处的`"https://api.yoururl.com"`修改为上一步您获得的API地址。

## 6.安装依赖并启动客户端。
安装依赖。
```shell
pip install requests pathlib wmi
```
启动客户端。
```shell
python main.py
```

如果您在客户端启动时选择了“注册”，那么程序会在注册完毕后退出。您只需再次启动并选择“登录”，随后登陆您刚刚注册的账户即可。“注册设备”操作同理。

注意：当前版本存在众多缺陷，其中最显著的一个即为无法使用两步验证。在您使用当前版本注册用户时，请勿启用两步验证，否则将无法运行。

注意：项目运行时存在泄露您的设备信息、文件的风险，请谨慎运行。
