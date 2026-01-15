"""
测试 PyUPPAAL 的 XML 导出功能

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
# 输出目录
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


def test_xml_property():
    """测试 UModel.xml 属性 - 获取 XML 字符串"""
    print("=" * 60)
    print("测试 1: UModel.xml 属性")
    print("=" * 60)

    # 加载模型
    model = pyu.UModel(TEST_MODEL_PATH)
    print(f"已加载模型: {TEST_MODEL_PATH}")

    # 获取 XML 字符串
    xml_str = model.xml

    # 验证 XML 字符串
    print(f"\nXML 字符串长度: {len(xml_str)} 字符")

    # 检查关键标签
    key_tags = ["<nta>", "</nta>", "<declaration>", "<template>", "<system>"]
    print("\n检查关键标签:")
    for tag in key_tags:
        if tag in xml_str:
            print(f"  ✓ 包含 {tag}")
        else:
            print(f"  ✗ 缺少 {tag}")

    # 显示 XML 前 500 个字符
    print("\nXML 内容预览 (前 500 字符):")
    print("-" * 40)
    print(xml_str[:500])
    print("-" * 40)

    return xml_str


def test_save_as():
    """测试 UModel.save_as() 方法 - 保存模型到新路径"""
    print("\n" + "=" * 60)
    print("测试 2: UModel.save_as() 方法")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 加载模型
    model = pyu.UModel(TEST_MODEL_PATH)
    print(f"已加载模型: {TEST_MODEL_PATH}")
    print(f"原始模型路径: {model.model_path}")

    # 保存到新路径
    new_path = os.path.join(OUTPUT_DIR, "exported_save_as.xml")
    model.save_as(new_path)
    print(f"\n已保存到新路径: {new_path}")
    print(f"模型路径已更新为: {model.model_path}")

    # 验证文件存在
    if os.path.exists(new_path):
        file_size = os.path.getsize(new_path)
        print(f"✓ 文件创建成功，大小: {file_size} 字节")

        # 尝试重新加载验证
        reloaded_model = pyu.UModel(new_path)
        print(f"✓ 文件可重新加载，包含 {len(reloaded_model.templates)} 个 Template")
    else:
        print("✗ 文件创建失败")

    return new_path


def test_copy_as():
    """测试 UModel.copy_as() 方法 - 复制模型到新路径"""
    print("\n" + "=" * 60)
    print("测试 3: UModel.copy_as() 方法")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 加载模型
    model = pyu.UModel(TEST_MODEL_PATH)
    print(f"已加载模型: {TEST_MODEL_PATH}")
    print(f"原始模型路径: {model.model_path}")

    # 复制到新路径
    copy_path = os.path.join(OUTPUT_DIR, "exported_copy_as.xml")
    copied_model = model.copy_as(copy_path)

    print(f"\n已复制到新路径: {copy_path}")
    print(f"原始模型路径 (不变): {model.model_path}")
    print(f"复制模型路径: {copied_model.model_path}")

    # 验证文件存在
    if os.path.exists(copy_path):
        file_size = os.path.getsize(copy_path)
        print(f"✓ 文件创建成功，大小: {file_size} 字节")
        print(f"✓ 返回新的 UModel 实例，包含 {len(copied_model.templates)} 个 Template")
    else:
        print("✗ 文件创建失败")

    return copied_model


def test_write_xml_tree():
    """测试 UModel.write_xml_tree() 方法 - 带缩进写入 XML"""
    print("\n" + "=" * 60)
    print("测试 4: UModel.write_xml_tree() 方法")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 加载模型
    model = pyu.UModel(TEST_MODEL_PATH)
    print(f"已加载模型: {TEST_MODEL_PATH}")

    # 测试不同缩进
    indent_values = [0, 2, 4]

    for indent in indent_values:
        output_path = os.path.join(OUTPUT_DIR, f"exported_indent_{indent}.xml")
        model.write_xml_tree(output_path, indent)

        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"\n缩进 {indent}:")
            print(f"  ✓ 文件: {output_path}")
            print(f"  ✓ 大小: {file_size} 字节")

            # 显示文件前几行
            with open(output_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[:5]
                print(f"  前 {len(lines)} 行预览:")
                for line in lines:
                    print(f"    {line.rstrip()}")
        else:
            print(f"\n缩进 {indent}: ✗ 文件创建失败")


def main():
    """主函数"""
    print("PyUPPAAL XML 导出功能测试")
    print("测试文件: ros2_v01_20251021_temp.xml")
    print("=" * 60)

    # 检查测试模型是否存在
    if not os.path.exists(TEST_MODEL_PATH):
        print(f"错误: 测试模型不存在: {TEST_MODEL_PATH}")
        return

    # 运行 XML 导出测试
    test_xml_property()
    test_save_as()
    test_copy_as()
    test_write_xml_tree()

    print("\n" + "=" * 60)
    print("所有 XML 导出测试完成!")
    print(f"输出文件保存在: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
