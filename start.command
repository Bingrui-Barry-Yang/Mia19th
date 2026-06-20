#!/bin/zsh
cd "$(dirname "$0")" || exit 1

if [[ ! -f index.html ]]; then
  echo "还没有生成 index.html，先运行构建程序。"
  python3 build.py || exit 1
fi

PORT=8000
echo "本地预览已启动：http://localhost:$PORT"
echo "关闭这个窗口即可停止预览。"
(sleep 1; open "http://localhost:$PORT") &
python3 -m http.server "$PORT" --bind 127.0.0.1
