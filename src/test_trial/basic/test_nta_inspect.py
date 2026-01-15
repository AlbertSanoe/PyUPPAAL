"""
测试 PyUPPAAL 的 NTA 数据结构检查功能

导入 ros2_v01_20251021_temp.xml 模型，打印所有 NTA 数据结构的详细信息。

数据结构层次:
- UModel (主模型)
  - declaration (全局声明)
  - templates (模板列表)
    - Template
      - name (模板名称)
      - params (参数)
      - declaration (局部声明)
      - init_ref (初始位置引用)
      - locations (位置列表)
        - Location
          - location_id, location_pos, name, invariant
          - is_initial, is_urgent, is_committed, is_branchpoint
          - rate_of_exponential, comments, test_code_on_enter, test_code_on_exit
      - edges (边列表)
        - Edge
          - source_location_id, target_location_id
          - select, guard, sync, update
          - probability_weight, comments, test_code, nails
  - system (系统声明)
  - queries (查询列表)
"""

import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pyuppaal as pyu
from pyuppaal.nta import Template, Location, Edge


# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# test_trial 目录
TEST_TRIAL_DIR = os.path.dirname(SCRIPT_DIR)
# 测试模型路径
TEST_MODEL_PATH = os.path.join(TEST_TRIAL_DIR, "ros2_v01_20251021_temp.xml")


def print_separator(title: str, char: str = "=", width: int = 80):
    """打印分隔线"""
    print(f"\n{char * width}")
    print(f" {title}")
    print(f"{char * width}")


def print_subseparator(title: str, char: str = "-", width: int = 60):
    """打印子分隔线"""
    print(f"\n  {char * width}")
    print(f"  {title}")
    print(f"  {char * width}")


def inspect_umodel_basic(model: pyu.UModel):
    """检查 UModel 基本信息"""
    print_separator("UModel 基本信息")
    
    print(f"\n  模型路径: {model.model_path}")
    print(f"  最大位置ID: {model.max_location_id}")
    print(f"  Template 数量: {len(model.templates)}")
    
    # 广播通道
    broadcast_chans = model.broadcast_chan
    print(f"  广播通道数量: {len(broadcast_chans)}")
    if broadcast_chans:
        print(f"  广播通道列表: {broadcast_chans}")


def inspect_declaration(model: pyu.UModel):
    """检查全局声明"""
    print_separator("全局声明 (Declaration)")
    
    declaration = model.declaration
    if declaration:
        print(f"\n  声明内容 ({len(declaration)} 字符):")
        print("  " + "-" * 60)
        # 按行打印，添加缩进
        for line in declaration.split('\n'):
            print(f"    {line}")
        print("  " + "-" * 60)
    else:
        print("\n  (无全局声明)")


def inspect_system(model: pyu.UModel):
    """检查系统声明"""
    print_separator("系统声明 (System)")
    
    system = model.system
    if system:
        print(f"\n  系统声明内容 ({len(system)} 字符):")
        print("  " + "-" * 60)
        for line in system.split('\n'):
            print(f"    {line}")
        print("  " + "-" * 60)
    else:
        print("\n  (无系统声明)")


def inspect_queries(model: pyu.UModel):
    """检查查询列表"""
    print_separator("查询列表 (Queries)")
    
    queries = model.queries
    if queries:
        print(f"\n  查询数量: {len(queries)}")
        for i, query in enumerate(queries):
            print(f"\n  查询 {i + 1}:")
            if query:
                print(f"    {query}")
            else:
                print("    (空查询)")
    else:
        print("\n  (无查询)")


def inspect_location(location: Location, init_ref: int = None, indent: str = "      "):
    """检查单个 Location 的详细信息
    
    Args:
        location: Location 对象
        init_ref: Template 的初始位置引用 ID，用于判断是否为初始位置
        indent: 缩进字符串
    """
    print(f"\n{indent}Location ID: id{location.location_id}")
    print(f"{indent}  位置坐标: {location.location_pos}")
    
    # 名称
    if location.name:
        print(f"{indent}  名称: {location.name}")
        if location.name_pos:
            print(f"{indent}    名称位置: {location.name_pos}")
    
    # 状态类型
    # 注意: is_initial 在从 XML 加载时默认为 False，
    # 因为 UPPAAL XML 中初始位置是通过 Template 的 <init ref="idX"/> 标签指定的
    state_types = []
    # 通过 init_ref 判断是否为初始位置
    if init_ref is not None and location.location_id == init_ref:
        state_types.append("initial")
    if location.is_urgent:
        state_types.append("urgent")
    if location.is_committed:
        state_types.append("committed")
    if location.is_branchpoint:
        state_types.append("branchpoint")
    
    if state_types:
        print(f"{indent}  状态类型: {', '.join(state_types)}")
    else:
        print(f"{indent}  状态类型: normal")
    
    # 不变式
    if location.invariant:
        print(f"{indent}  不变式: {location.invariant}")
        if location.invariant_pos:
            print(f"{indent}    不变式位置: {location.invariant_pos}")
    
    # 指数率
    if location.rate_of_exponential is not None:
        print(f"{indent}  指数率: {location.rate_of_exponential}")
        if location.rate_of_exp_pos:
            print(f"{indent}    指数率位置: {location.rate_of_exp_pos}")
    
    # 注释
    if location.comments:
        print(f"{indent}  注释: {location.comments}")
        if location.comments_pos:
            print(f"{indent}    注释位置: {location.comments_pos}")
    
    # 测试代码
    if location.test_code_on_enter:
        print(f"{indent}  进入测试代码: {location.test_code_on_enter}")
    if location.test_code_on_exit:
        print(f"{indent}  退出测试代码: {location.test_code_on_exit}")


def inspect_edge(edge: Edge, indent: str = "      "):
    """检查单个 Edge 的详细信息"""
    print(f"\n{indent}Edge: id{edge.source_location_id} -> id{edge.target_location_id}")
    
    # 选择表达式
    if edge.select:
        print(f"{indent}  选择 (select): {edge.select}")
        if edge.select_pos:
            print(f"{indent}    选择位置: {edge.select_pos}")
    
    # 守卫条件
    if edge.guard:
        print(f"{indent}  守卫 (guard): {edge.guard}")
        if edge.guard_pos:
            print(f"{indent}    守卫位置: {edge.guard_pos}")
    
    # 同步标签
    if edge.sync:
        print(f"{indent}  同步 (sync): {edge.sync}")
        if edge.sync_pos:
            print(f"{indent}    同步位置: {edge.sync_pos}")
    
    # 更新表达式
    if edge.update:
        print(f"{indent}  更新 (update): {edge.update}")
        if edge.update_pos:
            print(f"{indent}    更新位置: {edge.update_pos}")
    
    # 概率权重
    if edge.probability_weight is not None:
        print(f"{indent}  概率权重: {edge.probability_weight}")
        if edge.prob_weight_pos:
            print(f"{indent}    概率权重位置: {edge.prob_weight_pos}")
    
    # 注释
    if edge.comments:
        print(f"{indent}  注释: {edge.comments}")
        if edge.comments_pos:
            print(f"{indent}    注释位置: {edge.comments_pos}")
    
    # 测试代码
    if edge.test_code:
        print(f"{indent}  测试代码: {edge.test_code}")
    
    # 弯曲点
    if edge.nails:
        print(f"{indent}  弯曲点 (nails): {edge.nails}")


def inspect_template(template: Template, index: int):
    """检查单个 Template 的详细信息"""
    print_subseparator(f"Template {index + 1}: {template.name}")
    
    # 基本信息
    print(f"\n    名称: {template.name}")
    print(f"    初始位置引用: id{template.init_ref}")
    print(f"    Location 数量: {len(template.locations)}")
    print(f"    Edge 数量: {len(template.edges) if template.edges else 0}")
    
    # 参数
    if template.params:
        print("\n    参数 (params):")
        print(f"      {template.params}")
    
    # 局部声明
    if template.declaration:
        print("\n    局部声明 (declaration):")
        print("    " + "-" * 50)
        for line in template.declaration.split('\n'):
            print(f"      {line}")
        print("    " + "-" * 50)
    
    # Locations
    print(f"\n    === Locations ({len(template.locations)}) ===")
    for location in template.locations:
        inspect_location(location, init_ref=template.init_ref)
    
    # Edges
    if template.edges:
        print(f"\n    === Edges ({len(template.edges)}) ===")
        for edge in template.edges:
            inspect_edge(edge)
    else:
        print("\n    === Edges (0) ===")
        print("      (无边)")


def inspect_templates(model: pyu.UModel):
    """检查所有 Templates"""
    print_separator("Templates 详细信息")
    
    templates = model.templates
    print(f"\n  共有 {len(templates)} 个 Template")
    
    for i, template in enumerate(templates):
        inspect_template(template, i)


def print_statistics(model: pyu.UModel):
    """打印统计汇总信息"""
    print_separator("统计汇总")
    
    total_locations = 0
    total_edges = 0
    total_initial = 0
    total_urgent = 0
    total_committed = 0
    total_branchpoint = 0
    
    for template in model.templates:
        total_locations += len(template.locations)
        total_edges += len(template.edges) if template.edges else 0
        # 每个 Template 有一个初始位置（通过 init_ref 指定）
        total_initial += 1
        
        for location in template.locations:
            if location.is_urgent:
                total_urgent += 1
            if location.is_committed:
                total_committed += 1
            if location.is_branchpoint:
                total_branchpoint += 1
    
    print(f"\n  Template 总数: {len(model.templates)}")
    print(f"  Location 总数: {total_locations}")
    print(f"  Edge 总数: {total_edges}")
    print("\n  Location 类型统计:")
    print(f"    - Initial: {total_initial}")
    print(f"    - Urgent: {total_urgent}")
    print(f"    - Committed: {total_committed}")
    print(f"    - Branchpoint: {total_branchpoint}")
    print(f"    - Normal: {total_locations - total_urgent - total_committed - total_branchpoint}")
    
    # 查询统计
    queries = model.queries
    print(f"\n  Query 总数: {len(queries) if queries else 0}")
    
    # 广播通道统计
    broadcast_chans = model.broadcast_chan
    print(f"  广播通道总数: {len(broadcast_chans)}")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print(" PyUPPAAL NTA 数据结构检查工具")
    print(" 测试文件: ros2_v01_20251021_temp.xml")
    print("=" * 80)
    
    # 检查测试模型是否存在
    if not os.path.exists(TEST_MODEL_PATH):
        print(f"\n错误: 测试模型不存在: {TEST_MODEL_PATH}")
        return
    
    # 加载模型
    print(f"\n正在加载模型: {TEST_MODEL_PATH}")
    model = pyu.UModel(TEST_MODEL_PATH)
    print("模型加载成功!")
    
    # 检查各部分
    inspect_umodel_basic(model)
    inspect_declaration(model)
    inspect_system(model)
    inspect_queries(model)
    inspect_templates(model)
    print_statistics(model)
    
    print("\n" + "=" * 80)
    print(" NTA 数据结构检查完成!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
