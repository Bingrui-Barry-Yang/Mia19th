# 互动信封

这是一个可以发布到 GitHub Pages 的互动信封。信件正文经加密后存在 `index.html` 中，正确密码只在访问者的浏览器里用于解密。

## 重新生成或修改密码

1. 在终端进入本目录。
2. 安装一次依赖：

   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. 运行：

   ```bash
   python3 build.py
   ```

4. 按提示输入两次新密码。程序会读取 `咪呀22.txt` 并覆盖生成 `index.html`。

密码不会写入任何文件。如果忘记密码，只需用新密码重新生成。

## 本地预览

在 macOS 上双击 `start.command`，或在终端运行：

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

然后打开 <http://localhost:8000>。不建议直接双击 `index.html`，因为部分浏览器会禁止本地文件使用解密 API。

## 发布到 GitHub Pages

1. 在 GitHub 新建一个仓库，例如 `letter-for-mia`。
2. 将 `index.html` 和 `keshi-LIMBO.mp3` 上传到仓库根目录；不要上传明文的 `咪呀22.txt`。
3. 进入仓库 **Settings → Pages**。
4. 在 **Build and deployment** 中选择 **Deploy from a branch**。
5. Branch 选择 `main`，文件夹选择 `/ (root)`，然后保存。
6. 等待 GitHub 显示发布成功，即可使用 `https://用户名.github.io/letter-for-mia/` 访问。

GitHub Pages 链接是公开的，请通过另外的渠道告知收信人密码。

## 文件说明

- `build.py`：读取正文、加密并生成页面。
- `index.html`：最终互动页面。
- `keshi-LIMBO.mp3`：点击火漆印章后开始循环播放的背景音乐。
- `start.command`：macOS 本地预览入口。
- `requirements.txt`：Python 加密依赖。
