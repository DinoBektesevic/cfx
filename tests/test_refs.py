"""Tests for FieldRef and ComponentRef path proxies."""

import pytest

from cfx import Config, Float, Int
from cfx.refs import ComponentRef, FieldRef

#############################################################################
# Fixtures
#############################################################################


class LeafConfig(Config):
    confid = "leaf"
    x = Float(1.0, "x value")
    y = Int(0, "y value")


class BranchConfig(Config, components=[LeafConfig]):
    confid = "branch"
    z = Float(3.0, "branch own field")


class DeepConfig(Config, components=[BranchConfig]):
    confid = "deep"


#############################################################################
# FieldRef — basic construction
#############################################################################


class TestFieldRefBasic:
    def test_leaf_field_returns_fieldref(self):
        ref = LeafConfig.x
        assert isinstance(ref, FieldRef)
        assert ref._path == "x"

    def test_leaf_fieldref_has_none_cls(self):
        ref = LeafConfig.x
        assert ref._cls is None

    def test_branch_field_returns_fieldref(self):
        ref = BranchConfig.z
        assert isinstance(ref, FieldRef)
        assert ref._path == "z"

    def test_repr(self):
        assert repr(LeafConfig.x) == "FieldRef('x')"


#############################################################################
# FieldRef — chained traversal
#############################################################################


class TestFieldRefChain:
    def test_component_access_returns_fieldref(self):
        ref = BranchConfig.leaf
        assert isinstance(ref, FieldRef)
        assert ref._path == "leaf"
        assert ref._cls is LeafConfig

    def test_one_level_chain(self):
        ref = BranchConfig.leaf.x
        assert isinstance(ref, FieldRef)
        assert ref._path == "leaf.x"
        assert ref._cls is None

    def test_two_level_chain(self):
        ref = DeepConfig.branch.leaf.x
        assert isinstance(ref, FieldRef)
        assert ref._path == "branch.leaf.x"

    def test_chain_to_branch_field(self):
        ref = DeepConfig.branch.z
        assert ref._path == "branch.z"


#############################################################################
# FieldRef — error cases
#############################################################################


class TestFieldRefErrors:
    def test_unknown_name_raises(self):
        with pytest.raises(AttributeError, match="no field or component"):
            _ = BranchConfig.leaf.nonexistent

    def test_traverse_past_leaf_raises(self):
        ref = LeafConfig.x  # _cls is None
        with pytest.raises(AttributeError, match="cannot traverse past leaf"):
            _ = ref.anything

    def test_unknown_component_field_raises(self):
        with pytest.raises(AttributeError, match="no field or component"):
            _ = BranchConfig.leaf.nonexistent

    def test_private_name_raises(self):
        with pytest.raises(AttributeError):
            _ = LeafConfig.x._something


#############################################################################
# ComponentRef — class vs instance access
#############################################################################


class TestComponentRef:
    def test_class_access_returns_fieldref(self):
        ref = BranchConfig.leaf
        assert isinstance(ref, FieldRef)
        assert ref._path == "leaf"
        assert ref._cls is LeafConfig

    def test_instance_access_returns_subconfig(self):
        cfg = BranchConfig()
        assert isinstance(cfg.leaf, LeafConfig)

    def test_instance_access_is_independent(self):
        cfg1 = BranchConfig()
        cfg2 = BranchConfig()
        cfg1.leaf.x = 99.0
        assert cfg2.leaf.x == 1.0

    def test_component_ref_installed_on_class(self):
        assert isinstance(BranchConfig.__dict__["leaf"], ComponentRef)
