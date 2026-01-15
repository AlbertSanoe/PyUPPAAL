"""UModel 构建路径测试

测试 UModel 的两种构建路径（XML 和组件）的一致性和正确性。
"""
import os
import shutil
import pytest
from pyuppaal import UModel
from pyuppaal.nta import Template, Location


def bring_to_root(file_name: str):
    """获取测试文件的绝对路径"""
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(ROOT_DIR, file_name)


class TestParseXml:
    """测试 _parse_xml 静态方法"""

    def test_returns_correct_types(self):
        """验证返回正确的类型"""
        model_path = bring_to_root('test_umodel_build.xml')
        decl, templates, system, queries = UModel._parse_xml(model_path)

        assert isinstance(decl, str)
        assert isinstance(templates, list)
        assert isinstance(system, str)
        assert isinstance(queries, list)

    def test_no_side_effects(self):
        """验证解析不修改文件"""
        model_path = bring_to_root('test_umodel_build.xml')
        original_mtime = os.path.getmtime(model_path)

        UModel._parse_xml(model_path)

        assert os.path.getmtime(model_path) == original_mtime

    def test_queries_always_list(self):
        """验证 queries 始终返回列表"""
        model_path = bring_to_root('test_umodel_build.xml')
        _, _, _, queries = UModel._parse_xml(model_path)

        assert queries is not None
        assert isinstance(queries, list)


class TestLoadNoModify:
    """测试加载不修改文件"""

    def test_load_does_not_modify_file(self):
        """验证加载模型不修改 XML 文件"""
        original = bring_to_root('test_umodel_build.xml')
        copy_path = bring_to_root('test_no_modify_copy.xml')

        try:
            shutil.copy(original, copy_path)
            original_content = open(copy_path, 'rb').read()

            umodel = UModel(copy_path)

            assert open(copy_path, 'rb').read() == original_content
        finally:
            if os.path.exists(copy_path):
                os.remove(copy_path)


class TestFromComponents:
    """测试 from_components 构建"""

    def test_default_queries_is_empty_list(self):
        """验证 queries 默认为空列表而非 None"""
        loc = Location(location_id=0, location_pos=(0, 0), is_initial=True)
        tmpl = Template(name="T", locations=[loc], init_ref=0, edges=[])

        umodel = UModel.from_components(
            declaration="",
            templates=[tmpl],
            system="system T;"
        )

        assert umodel.queries == []
        assert umodel.queries is not None

    def test_autosave_disabled(self):
        """验证 from_components 禁用 autosave"""
        loc = Location(location_id=0, location_pos=(0, 0), is_initial=True)
        tmpl = Template(name="T", locations=[loc], init_ref=0, edges=[])

        umodel = UModel.from_components(
            declaration="",
            templates=[tmpl],
            system="system T;"
        )

        assert umodel._autosave == False

    def test_with_explicit_queries(self):
        """验证显式传入 queries 时正常工作"""
        loc = Location(location_id=0, location_pos=(0, 0), is_initial=True)
        tmpl = Template(name="T", locations=[loc], init_ref=0, edges=[])

        umodel = UModel.from_components(
            declaration="",
            templates=[tmpl],
            system="system T;",
            queries=["A[] not deadlock"]
        )

        assert umodel.queries == ["A[] not deadlock"]


class TestConstructionConsistency:
    """测试两种构建路径的一致性"""

    def test_xml_and_components_produce_same_result(self):
        """验证 XML 构建和组件构建产生相同结果"""
        model_path = bring_to_root('test_umodel_build.xml')

        # XML 构建
        umodel_xml = UModel(model_path)

        # 组件构建
        umodel_comp = UModel.from_components(
            declaration=umodel_xml.declaration,
            templates=umodel_xml.templates,
            system=umodel_xml.system,
            queries=umodel_xml.queries,
            model_path=model_path
        )

        assert umodel_comp.declaration == umodel_xml.declaration
        assert umodel_comp.system == umodel_xml.system
        assert umodel_comp.queries == umodel_xml.queries
        assert len(umodel_comp.templates) == len(umodel_xml.templates)

    def test_xml_load_autosave_enabled(self):
        """验证 XML 加载启用 autosave"""
        model_path = bring_to_root('test_umodel_build.xml')
        umodel = UModel(model_path)

        assert umodel._autosave == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
