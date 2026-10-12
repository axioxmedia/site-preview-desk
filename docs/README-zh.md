# 本地站点预览器

**由安溯媒体打包**

加载网站 ZIP 源码包与 SQL 文件，自动检测 PHP 相关设定，启动临时本地服务器，并用默认浏览器打开预览。

![截图](APPCap.png)

## 功能

- 原生文件对话框选择 ZIP 与 SQL
- 自动检测 PHP 版本与常用扩展
- 解压 ZIP、尝试将 SQL 导入临时 SQLite、优先使用 `php -S`
- 一键打开默认浏览器
- 停止并清理临时文件
- 黑金主题可切浅色，中英切换，会话记忆

## 安装

推荐使用 [GitHub Deploy Desk](https://github.com/axioxmedia/github-deployer)，或：

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

打包 Windows EXE：

```bat
build_exe.bat
```

详见 `HOW_TO_BUILD.txt`。
