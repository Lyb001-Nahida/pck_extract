import os
import struct
import sys
import subprocess
import glob
from pathlib import Path

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# vgmstream 路径（固定）
VGM_PATH = os.path.join(SCRIPT_DIR, "vgmstream", "vgmstream-cli.exe")


class PCKWaveExtractor:
    """从 PCK 中提取 WAV 音频"""
    
    def __init__(self, pck_path, output_dir):
        self.pck_path = pck_path
        self.output_dir = output_dir
        self.raw_dir = os.path.join(output_dir, "raw")
        
        os.makedirs(self.raw_dir, exist_ok=True)
    
    def extract(self):
        """提取所有 WAV（不解码）"""
        print(f"📂 读取: {self.pck_path}")
        
        try:
            with open(self.pck_path, 'rb') as f:
                data = f.read()
        except Exception as e:
            print(f"❌ 读取失败: {e}")
            return 0
        
        print(f"📊 文件大小: {len(data):,} bytes")
        print()
        
        wav_count = 0
        pos = 0
        
        while True:
            riff_pos = data.find(b'RIFF', pos)
            if riff_pos == -1:
                break
            
            if riff_pos + 12 > len(data):
                break
                
            if data[riff_pos + 8:riff_pos + 12] != b'WAVE':
                pos = riff_pos + 1
                continue
            
            try:
                file_size = struct.unpack('<I', data[riff_pos + 4:riff_pos + 8])[0]
                total_size = file_size + 8
                
                if riff_pos + total_size > len(data):
                    total_size = len(data) - riff_pos
                
                wav_data = data[riff_pos:riff_pos + total_size]
                
                if self._is_valid_wav(wav_data):
                    wav_count += 1
                    
                    raw_path = os.path.join(self.raw_dir, f"raw_{wav_count:04d}.wav")
                    with open(raw_path, 'wb') as out:
                        out.write(wav_data)
                    
                    info = self._get_wav_info(wav_data)
                    print(f"  ✅ 提取 #{wav_count}: raw_{wav_count:04d}.wav  {info}")
                    
                    pos = riff_pos + total_size
                else:
                    pos = riff_pos + 1
                    
            except Exception as e:
                print(f"  ⚠️ 错误: {e}")
                pos = riff_pos + 1
        
        print(f"\n✅ 共提取 {wav_count} 个 WAV 文件")
        print(f"📁 保存在: {self.raw_dir}")
        
        return wav_count
    
    def _is_valid_wav(self, data):
        if len(data) < 44:
            return False
        if data[:4] != b'RIFF':
            return False
        if data[8:12] != b'WAVE':
            return False
        return True
    
    def _get_wav_info(self, data):
        try:
            fmt_pos = data.find(b'fmt ')
            if fmt_pos == -1:
                return "未知格式"
            
            channels = struct.unpack('<H', data[fmt_pos + 10:fmt_pos + 12])[0]
            sample_rate = struct.unpack('<I', data[fmt_pos + 12:fmt_pos + 16])[0]
            bit_depth = struct.unpack('<H', data[fmt_pos + 22:fmt_pos + 24])[0]
            
            data_pos = data.find(b'data')
            if data_pos != -1:
                data_size = struct.unpack('<I', data[data_pos + 4:data_pos + 8])[0]
                duration = data_size / (channels * (bit_depth / 8) * sample_rate)
                return f"{channels}ch, {sample_rate}Hz, {bit_depth}bit, {duration:.1f}s"
            
            return f"{channels}ch, {sample_rate}Hz, {bit_depth}bit"
        except:
            return "未知格式"


def check_vgmstream():
    """检查 vgmstream-cli 是否可用"""
    if not os.path.exists(VGM_PATH):
        print(f"❌ 找不到 vgmstream-cli: {VGM_PATH}")
        print(f"💡 请确保 vgmstream-cli.exe 放在脚本目录的 vgmstream/ 文件夹下")
        return False
    
    try:
        result = subprocess.run(
            [VGM_PATH, '--help'],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except:
        return False


def batch_decode(raw_dir, decoded_dir):
    """批量解码所有 WAV"""
    
    os.makedirs(decoded_dir, exist_ok=True)
    
    raw_files = glob.glob(os.path.join(raw_dir, "*.wav"))
    
    if not raw_files:
        print(f"⚠️ 没有找到需要解码的文件: {raw_dir}")
        return 0
    
    print(f"\n🎵 找到 {len(raw_files)} 个文件需要解码")
    print(f"🔧 vgmstream: {VGM_PATH}")
    print()
    
    if not os.path.exists(VGM_PATH):
        print(f"❌ 找不到 vgmstream-cli.exe")
        return 0
    
    success_count = 0
    
    for i, raw_path in enumerate(raw_files, 1):
        base_name = os.path.basename(raw_path)
        output_name = base_name.replace("raw_", "decoded_")
        output_path = os.path.join(decoded_dir, output_name)
        
        if os.path.exists(output_path):
            print(f"  ⏭️ 跳过 #{i}: {output_name} (已存在)")
            success_count += 1
            continue
        
        try:
            cmd = [
                VGM_PATH,
                "-o", output_path,
                raw_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                size_kb = os.path.getsize(output_path) / 1024
                print(f"  ✅ 解码 #{i}: {output_name} ({size_kb:.1f} KB)")
                success_count += 1
            else:
                error_msg = result.stderr[:80] if result.stderr else "未知错误"
                print(f"  ❌ 解码 #{i}: {output_name} 失败 ({error_msg})")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ 解码 #{i}: {output_name} 超时")
        except Exception as e:
            print(f"  ❌ 解码 #{i}: {output_name} 异常 ({e})")
    
    print(f"\n✅ 解码完成: {success_count}/{len(raw_files)}")
    return success_count


def main():
    print("=" * 60)
    print("🎵 PCK WAV 提取器 + 批量解码器")
    print("=" * 60)
    
    # 检查 vgmstream
    print(f"\n🔧 vgmstream 路径: {VGM_PATH}")
    if os.path.exists(VGM_PATH):
        print("   ✅ 找到 vgmstream-cli.exe")
    else:
        print("   ❌ 未找到 vgmstream-cli.exe")
        print("   💡 请放在脚本目录/vgmstream/vgmstream-cli.exe")
    
    # 获取 PCK 路径
    if len(sys.argv) > 1:
        pck_path = sys.argv[1].strip('"')
    else:
        print("\n💡 提示: 可以直接拖拽文件到命令行窗口")
        pck_path = input("📁 请输入 PCK 文件路径: ").strip().strip('"')
        pck_name = os.path.basename(pck_path)
    
    if not os.path.exists(pck_path):
        print(f"\n❌ 文件不存在: {pck_path}")
        input("\n按 Enter 退出...")
        return
    
    # 输出目录
    default_output = os.path.join(os.path.dirname(pck_path), f"{os.path.splitext(pck_name)[0]}_extracted")
    output_dir = input(f"📂 输出目录 (默认: {default_output}): ").strip().strip('"')
    if not output_dir:
        output_dir = default_output
    
    raw_dir = os.path.join(output_dir, "raw")
    decoded_dir = os.path.join(output_dir, "decoded")
    
    print("\n" + "=" * 60)
    print("【阶段 1】提取加密 WAV")
    print("=" * 60)
    
    # 提取
    extractor = PCKWaveExtractor(pck_path, output_dir)
    count = extractor.extract()
    
    if count == 0:
        print("\n⚠️ 没有提取到任何文件")
        input("\n按 Enter 退出...")
        return
    
    # 解码
    print("\n" + "=" * 60)
    print("【阶段 2】批量解码")
    print("=" * 60)
    
    batch_decode(raw_dir, decoded_dir)
    
    # 完成
    print("\n" + "=" * 60)
    print("✅ 全部完成！")
    print(f"📁 加密 WAV: {raw_dir}")
    print(f"📁 解码 WAV: {decoded_dir}")
    print("=" * 60)
    
    input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()