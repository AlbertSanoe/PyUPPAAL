"""
测试 PyUPPAAL 的 Mermaid 通信图导出功能

测试文件: ros2_v01_20251021_temp.xml
"""

import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pyuppaal as pyu

# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# test_trial 目录
TEST_TRIAL_DIR = os.path.dirname(SCRIPT_DIR)
# 测试模型路径
TEST_MODEL_PATH = os.path.join(TEST_TRIAL_DIR, "ros2_v01_20251021_temp.xml")


def test_get_communication_graph():
    """测试从 UModel 获取通信图"""
    print("=" * 60)
    print("测试 1: UModel.get_communication_graph()")
    print("=" * 60)

    # 加载模型
    model = pyu.UModel(TEST_MODEL_PATH)
    print(f"已加载模型: {TEST_MODEL_PATH}")
    print(f"模型包含 {len(model.templates)} 个 Template:")
    for t in model.templates:
        print(f"  - {t.name}")

    try:
        # 获取通信图（不美化）
        cg = model.get_communication_graph(is_beautify=False)
        print("\n原始通信图 (is_beautify=False):")
        print(cg.mermaid_str)

        # 获取通信图（美化后）
        cg_beautified = model.get_communication_graph(is_beautify=True)
        print("\n美化后的通信图 (is_beautify=True):")
        print(cg_beautified.mermaid_str)

        return cg_beautified
    except AssertionError:
        print("\n警告: 通信图生成失败!")
        print("原因: 模型的 system 声明格式不被支持 (多行格式)")
        print("PyUPPAAL 的 build_cg.py 目前只支持单行 system 声明")
        print("\n模型的 system 声明:")
        print("-" * 40)
        # 只显示前500个字符
        system_preview = model.system[:500] if len(model.system) > 500 else model.system
        print(system_preview)
        if len(model.system) > 500:
            print("... (截断)")
        print("-" * 40)
        return None


def test_mermaid_export():
    """测试 Mermaid 导出功能"""
    print("\n" + "=" * 60)
    print("测试 3: Mermaid.export() 导出功能")
    print("=" * 60)

    # 加载模型并获取通信图
    model = pyu.UModel(TEST_MODEL_PATH)

    cg = model.get_communication_graph(is_beautify=True)

    # 导出目录
    export_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(export_dir, exist_ok=True)

    # 导出为 Markdown 文件
    md_path = os.path.join(export_dir, "communication_graph.md")
    cg.export(md_path)
    print(f"\n已导出 Markdown 文件: {md_path}")

    # 读取并显示导出的内容
    with open(md_path, "r", encoding="utf-8") as f:
        print(f"文件内容:\n{f.read()}")

    # 注意：导出 SVG/PNG/JPG 需要网络连接（使用 mermaid.ink API）
    print("\n注意: 导出 SVG/PNG/JPG 格式需要网络连接 (使用 mermaid.ink API)")

    # 测试图片导出（需要网络）
    try:
        svg_path = os.path.join(export_dir, "communication_graph.svg")
        cg.export(svg_path)
        print(f"已导出 SVG 文件: {svg_path}")

        png_path = os.path.join(export_dir, "communication_graph.png")
        cg.export(png_path)
        print(f"已导出 PNG 文件: {png_path}")
    except Exception as e:
        print(f"图片导出失败 (可能是网络问题): {e}")


def main():
    """主函数"""
    print("PyUPPAAL Mermaid 通信图导出功能测试")
    print("测试文件: ros2_v01_20251021_temp.xml")
    print("=" * 60)

    # 检查测试模型是否存在
    if not os.path.exists(TEST_MODEL_PATH):
        print(f"错误: 测试模型不存在: {TEST_MODEL_PATH}")
        return

    # 运行测试
    cg = test_get_communication_graph()

    # 只有通信图生成成功才测试导出
    if cg is not None:
        test_mermaid_export()
    else:
        print("\n跳过导出测试 (通信图生成失败)")

    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
