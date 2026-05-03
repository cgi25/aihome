<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Home Remote - 远程控制面板</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .projects-container {
            width: 100%;
            max-width: 1000px;
            padding: 4rem 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .projects-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2.5rem;
            width: 100%;
            margin-top: 2rem;
        }

        .project-card {
            padding: 2rem;
            min-height: 220px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .project-card:hover {
            transform: translateY(-12px);
            background: rgba(255, 255, 255, 0.4);
            border-color: rgba(255, 255, 255, 0.8);
        }

        .btn {
            display: inline-block;
            margin-top: 1.5rem;
            padding: 0.7rem 1.8rem;
            background: #ffffff;
            color: #5dade2;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.9rem;
            transition: 0.3s;
            border: 1px solid #5dade2;
        }

        .btn:hover {
            background: #5dade2;
            color: white;
            box-shadow: 0 8px 20px rgba(93, 173, 226, 0.3);
        }
        :root {
            --primary: #6366f1;
            --bg-dark: #0f172a;
        }
        body {
            background-color: var(--bg-dark);
            color: white;
            overflow-x: hidden;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        /* 毛玻璃效果 */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1.5rem;
        }
        /* 光标跟随发光背景 */
        #glow-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            background: radial-gradient(circle at var(--x, 50%) var(--y, 50%), rgba(99, 102, 241, 0.15) 0%, transparent 40%);
            z-index: -1;
        }
        .input-style {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        .input-style:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
            outline: none;
        }
        .btn-primary {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            transition: transform 0.2s;
        }
        .btn-primary:active { transform: scale(0.95); }
    </style>
</head>
<body>
    <div id="glow-bg"></div>

    <div class="min-h-screen flex items-center justify-center p-4">
        <div id="login-container" class="glass-card w-full max-w-md p-8 shadow-2xl">
            <h1 class="text-3xl font-bold text-center mb-8 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">控制台登录</h1>
            <div class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2 opacity-70">用户 ID</label>
                    <input type="text" id="user-id" class="w-full p-3 rounded-xl input-style" placeholder="请输入您的 ID">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2 opacity-70">密码</label>
                    <input type="password" id="password" class="w-full p-3 rounded-xl input-style" placeholder="••••••••">
                </div>
                <button onclick="handleLogin()" class="w-full btn-primary py-3 rounded-xl font-bold shadow-lg">进入系统</button>
                </div>
            </div>

        <div id="main-panel" class="hidden glass-card w-full max-w-2xl p-6 md:p-10 shadow-2xl">
            <div class="flex justify-between items-center mb-8">
                <div>
                    <h2 class="text-2xl font-bold">远程指令下发</h2>
                    <p class="text-sm opacity-50">正在操控：<span id="display-user">Guest</span></p>
                </div>
                <button onclick="logout()" class="text-sm opacity-50 hover:opacity-100">退出</button>
            </div>

            <div class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2 opacity-70">目标设备 ID</label>
                    <input type="text" id="target-device-id" class="w-full p-3 rounded-xl input-style" placeholder="例如: 硬盘序列号">
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-2 opacity-70">您的需求</label>
                    <textarea id="ai-input" rows="3" class="w-full p-3 rounded-xl input-style" placeholder="例如：帮我关机、打开计算器、清理系统垃圾..."></textarea>
                </div>

                <div id="status-display" class="hidden p-4 rounded-xl bg-indigo-900/30 border border-indigo-500/30 text-sm">
                    <p id="status-text">处理中...</p>
                    <code id="cmd-preview" class="block mt-2 text-indigo-300"></code>
                </div>

                <button onclick="processAndSend()" id="send-btn" class="w-full btn-primary py-4 rounded-xl font-bold flex items-center justify-center gap-2">
                    <span>发送 AI 指令</span>
                </button>
            </div>
        </div>
    </div>

    <script>
        // 配置项
        const CONFIG = {
            API_BASE: "https://api.cgi26.cn", // 对应你的 server.py 地址
            AI_API: "https://yunwu.ai/v1/chat/completions",
            AI_KEY: "sk-VnXnTfoUmwYL24a8EFyO8RiSzwkRn8qwBKAviZzAplQm3XXT"
        };

        let userToken = "";

        // 鼠标跟随效果
        document.addEventListener('mousemove', (e) => {
            document.body.style.setProperty('--x', e.clientX + 'px');
            document.body.style.setProperty('--y', e.clientY + 'px');
        });

        // 登录处理
        async function handleLogin() {
            const userId = document.getElementById('user-id').value;
            const password = document.getElementById('password').value;

            try {
                const res = await fetch(`${CONFIG.API_BASE}/api/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, password: password })
                });
                
                const data = await res.json();
                if (res.ok) {
                    userToken = data.token;
                    document.getElementById('display-user').innerText = userId;
                    document.getElementById('login-container').classList.add('hidden');
                    document.getElementById('main-panel').classList.remove('hidden');
                } else {
                    alert('登录失败: ' + (data.detail || '请检查账号密码'));
                }
            } catch (e) {
                alert('连接服务器失败');
            }
        }

        // AI 转译逻辑
        async function translateToCmd(prompt) {
            const res = await fetch(CONFIG.AI_API, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${CONFIG.AI_KEY}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: "gpt-5.4-mini", // 或其他可用模型
                    messages: [
                        { role: "system", content: "你是一个 Windows 系统助手。请将用户的中文需求转换为单条可在 CMD 命令行执行的命令。只输出命令本身，不要有任何解释文字或代码块符号。" },
                        { role: "user", content: prompt }
                    ]
                })
            });
            const data = await res.json();
            return data.choices[0].message.content.trim();
        }

        // 执行流程
        async function processAndSend() {
            const deviceId = document.getElementById('target-device-id').value;
            const prompt = document.getElementById('ai-input').value;
            const btn = document.getElementById('send-btn');
            const statusBox = document.getElementById('status-display');

            if (!deviceId || !prompt) return alert('请填写完整信息');

            try {
                btn.disabled = true;
                btn.innerText = "AI 思考中...";
                statusBox.classList.remove('hidden');
                document.getElementById('status-text').innerText = "🤖 AI 正在转译指令...";

                // 1. 调用 AI 获取命令
                const cmd = await translateToCmd(prompt);
                document.getElementById('cmd-preview').innerText = "> " + cmd;

                // 2. 下发命令到服务端 (对应 /api/cmd/push)
                document.getElementById('status-text').innerText = "🚀 正在通过服务端下发...";
                const pushRes = await fetch(`${CONFIG.API_BASE}/api/cmd/push`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${userToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ device_id: deviceId, cmd: cmd })
                });

                if (pushRes.ok) {
                    document.getElementById('status-text').innerText = "✅ 指令已成功入库，等待受控端轮询。";
                } else {
                    throw new Error('推送失败');
                }

            } catch (e) {
                document.getElementById('status-text').innerText = "❌ 错误: " + e.message;
            } finally {
                btn.disabled = false;
                btn.innerText = "发送 AI 指令";
            }
        }

        function logout() {
            location.reload();
        }
    </script>
</body>
</html>