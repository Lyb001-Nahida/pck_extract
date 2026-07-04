# 🎵 PCK WAV 提取器 + 批量解码器

从 PCK 文件中提取加密的 WAV 音频，并通过 vgmstream 批量解码为标准 WAV 格式。

---

## 📦 依赖

- Python 3.6+
- vgmstream-cli.exe（下载地址：https://github.com/vgmstream/vgmstream/releases）

---

## 📁 目录结构
```
项目目录/
├── pck_extract.py # 主脚本
├── vgmstream/
│ └── vgmstream-cli.exe # vgmstream 解码器（必需）
```
---

## 🚀 使用方法

### 方式一：命令行参数

```
python pck_extract.py "D:\path\to\file.pck"
```
方式二：交互式运行
直接运行脚本，按提示输入 PCK 文件路径：


python pck_extract.py
cmd运行时支持拖拽文件到命令行窗口，自动填入路径。

📂 输出结构
在 PCK 文件同目录下创建 {文件名}_extracted/ 文件夹，包含：

```
{文件名}_extracted/
├── raw/               # 阶段1：从 PCK 提取的原始 WAV（可能加密/非标准）
│   ├── raw_0001.wav
│   ├── raw_0002.wav
│   └── ...
└── decoded/           # 阶段2：vgmstream 解码后的标准 WAV
    ├── decoded_0001.wav
    ├── decoded_0002.wav
    └── ...
```
⚙️ 工作流程
阶段 1：提取
扫描 PCK 文件中所有 RIFF 头

校验并提取完整的 WAV 数据块

保存为 raw_xxxx.wav

阶段 2：解码
调用 vgmstream-cli.exe 批量解码

跳过已存在的解码文件

输出为 decoded_xxxx.wav

🛠️ 配置说明

|配置项	| 说明 |
|-----|-----|
|VGM_PATH|固定指向脚本目录下的 vgmstream/vgmstream-cli.exe
|超时时间|	单个文件解码超时设为 120 秒|

##⚠️ 常见问题
❌ "找不到 vgmstream-cli.exe"
确保 vgmstream-cli.exe 放在脚本目录的 vgmstream/ 子文件夹中：
```
pck_extract.py
vgmstream/
    └── vgmstream-cli.exe
```
❌ "没有提取到任何文件"
确认 PCK 文件是否包含 WAV 数据

检查文件是否损坏或加密格式不标准

⏰ 解码超时
部分大文件可能需要更长时间，可修改脚本中的 timeout=120 参数。

📝 许可
本工具仅供学习研究使用，请勿用于商业用途或侵犯他人版权。
