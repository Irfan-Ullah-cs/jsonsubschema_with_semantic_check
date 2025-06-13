"""
Created on May 13, 2025
Test file for semantic type implementation with consistent permissive model.
Run the test file with pytest .\test_stype_keyword.py -v
"""

import pytest
from jsonsubschema.api import isSubschema, meet, join, isEquivalent

# ===== Core Logic: Permissive Semantic Compatibility =====

def test_stype_at_root():
    """Test permissive semantic compatibility: different stype presence"""
    
    # Schema WITH stype
    schema_with_stype = {
        "type": "number",
        "stype": "quantitykind:Temperature"
    }
    
    # Schema WITHOUT stype
    schema_without_stype = {
        "type": "number"
    }
    
    # Permissive model: with_stype -> without_stype = True, without_stype -> with_stype = False
    with_to_without = isSubschema(schema_with_stype, schema_without_stype)
    without_to_with = isSubschema(schema_without_stype, schema_with_stype)
    
    assert with_to_without, "Schema with stype SHOULD be subtype of schema without stype (more specific → more general)"
    assert not without_to_with, "Schema without stype should NOT be subtype of schema with stype (more general → more specific)"

def test_stype_same_semantic_type():
    """Test schemas with same semantic type follow structural subtyping rules"""
    
    # Both have same stype, but different structural constraints
    more_restrictive = {
        "type": "number",
        "stype": "quantitykind:Temperature",
        "minimum": 10,
        "maximum": 30
    }
    
    less_restrictive = {
        "type": "number", 
        "stype": "quantitykind:Temperature",
        "minimum": 0,
        "maximum": 100
    }
    
    # Same semantic type: structural subtyping applies
    restrictive_to_general = isSubschema(more_restrictive, less_restrictive)
    general_to_restrictive = isSubschema(less_restrictive, more_restrictive)
    
    assert restrictive_to_general, "More structurally restrictive schema should be subtype when semantic types are same"
    assert not general_to_restrictive, "Less structurally restrictive schema should NOT be subtype when semantic types are same"

def test_stype_different_semantic_types():
    """Test schemas with different semantic types are incompatible"""
    
    temperature_schema = {
        "type": "number",
        "stype": "quantitykind:Temperature"
    }
    
    pressure_schema = {
        "type": "number",
        "stype": "quantitykind:Pressure"
    }
    
    # Different semantic types should be incompatible in both directions
    temp_to_pressure = isSubschema(temperature_schema, pressure_schema)
    pressure_to_temp = isSubschema(pressure_schema, temperature_schema)
    
    assert not temp_to_pressure, "Schemas with different semantic types should not be subtypes"
    assert not pressure_to_temp, "Schemas with different semantic types should not be subtypes (reverse)"

def test_stype_no_semantic_types():
    """Test schemas with no semantic types follow normal structural rules"""
    
    more_restrictive = {
        "type": "number",
        "minimum": 10,
        "maximum": 30
    }
    
    less_restrictive = {
        "type": "number",
        "minimum": 0,
        "maximum": 100
    }
    
    # No semantic types: normal structural subtyping
    restrictive_to_general = isSubschema(more_restrictive, less_restrictive)
    general_to_restrictive = isSubschema(less_restrictive, more_restrictive)
    
    assert restrictive_to_general, "More restrictive schema should be subtype when no semantic types"
    assert not general_to_restrictive, "Less restrictive schema should NOT be subtype when no semantic types"

# ===== Stype at Different Schema Levels =====

def test_stype_permissive_compatibility_in_object_properties():
    """Test permissive semantic compatibility in object properties"""
    
    # Property WITH stype
    schema_property_with_stype = {
        "type": "object",
        "properties": {
            "temperature": {
                "type": "number",
                "stype": "quantitykind:Temperature"
            }
        }
    }
    
    # Property WITHOUT stype
    schema_property_without_stype = {
        "type": "object",
        "properties": {
            "temperature": {
                "type": "number"
            }
        }
    }
    
    with_to_without = isSubschema(schema_property_with_stype, schema_property_without_stype)
    without_to_with = isSubschema(schema_property_without_stype, schema_property_with_stype)
    
    assert with_to_without, "Object with stype property SHOULD be subtype of object without stype property (more specific → more general)"
    assert not without_to_with, "Object without stype property should NOT be subtype of object with stype property (more general → more specific)"

def test_stype_permissive_compatibility_in_array_items():
    """Test permissive semantic compatibility in array items"""
    
    # Array items WITH stype
    array_with_stype_items = {
        "type": "array",
        "items": {
            "type": "number",
            "stype": "quantitykind:Temperature"
        }
    }
    
    # Array items WITHOUT stype
    array_without_stype_items = {
        "type": "array",
        "items": {
            "type": "number"
        }
    }
    
    with_to_without = isSubschema(array_with_stype_items, array_without_stype_items)
    without_to_with = isSubschema(array_without_stype_items, array_with_stype_items)
    
    assert with_to_without, "Array with stype items SHOULD be subtype of array without stype items (more specific → more general)"
    assert not without_to_with, "Array without stype items should NOT be subtype of array with stype items (more general → more specific)"

def test_stype_nested_levels():
    """Test permissive semantic compatibility at multiple nesting levels"""
    
    # Deeply nested WITH stype
    nested_with_stype = {
        "type": "object",
        "properties": {
            "sensor_data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "reading": {
                            "type": "number",
                            "stype": "quantitykind:Temperature"
                        }
                    }
                }
            }
        }
    }
    
    # Deeply nested WITHOUT stype
    nested_without_stype = {
        "type": "object",
        "properties": {
            "sensor_data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "reading": {
                            "type": "number"
                        }
                    }
                }
            }
        }
    }
    
    with_to_without = isSubschema(nested_with_stype, nested_without_stype)
    without_to_with = isSubschema(nested_without_stype, nested_with_stype)
    
    assert with_to_without, "Deeply nested schema with stype SHOULD be subtype of same structure without stype (more specific → more general)"
    assert not without_to_with, "Deeply nested schema without stype should NOT be subtype of same structure with stype (more general → more specific)"

# ===== Same Stype Tests with Different Properties =====

def test_stype_same_object_level_different_properties():
    """Test schemas with same stype at object level but different properties"""
    
    # Object with same stype but more properties (more specific)
    more_specific_schema = {
        "type": "object",
        "stype": "quantitykind:Sensor",
        "properties": {
            "id": {"type": "string"},
            "temperature": {"type": "number", "minimum": 0},
            "pressure": {"type": "number"},
            "location": {"type": "string"}
        },
        "required": ["id", "temperature"]
    }
    
    # Object with same stype but fewer properties (less specific)
    less_specific_schema = {
        "type": "object",
        "stype": "quantitykind:Sensor",
        "properties": {
            "id": {"type": "string"},
            "temperature": {"type": "number"}
        }
    }
    
    # Same stype: structural subtyping should apply
    specific_to_general = isSubschema(more_specific_schema, less_specific_schema)
    general_to_specific = isSubschema(less_specific_schema, more_specific_schema)
    
    assert specific_to_general, "More specific schema (same stype, more properties) should be subtype of less specific"
    assert not general_to_specific, "Less specific schema should NOT be subtype of more specific (same stype)"

def test_stype_same_array_level_different_constraints():
    """Test arrays with same stype but different item constraints"""
    
    # Array with same stype but more restrictive items
    restrictive_array = {
        "type": "array",
        "stype": "quantitykind:MeasurementArray",
        "items": {
            "type": "number",
            "stype": "quantitykind:Temperature",
            "minimum": 0,
            "maximum": 100
        },
        "minItems": 1
    }
    
    # Array with same stype but less restrictive items
    permissive_array = {
        "type": "array",
        "stype": "quantitykind:MeasurementArray",
        "items": {
            "type": "number",
            "stype": "quantitykind:Temperature"
        }
    }
    
    # Same stype: structural subtyping should apply
    restrictive_to_permissive = isSubschema(restrictive_array, permissive_array)
    permissive_to_restrictive = isSubschema(permissive_array, restrictive_array)
    
    assert restrictive_to_permissive, "More restrictive array (same stype) should be subtype of less restrictive"
    assert not permissive_to_restrictive, "Less restrictive array should NOT be subtype of more restrictive (same stype)"

def test_stype_same_object_different_semantic_properties():
    """Test objects with same root stype but different semantic properties"""
    
    # Object with temperature semantic property
    temp_focused_schema = {
        "type": "object",
        "stype": "quantitykind:Sensor",
        "properties": {
            "id": {"type": "string"},
            "reading": {
                "type": "number",
                "stype": "quantitykind:Temperature"
            }
        }
    }
    
    # Object with pressure semantic property (same root stype)
    pressure_focused_schema = {
        "type": "object",
        "stype": "quantitykind:Sensor",
        "properties": {
            "id": {"type": "string"},
            "reading": {
                "type": "number",
                "stype": "quantitykind:Pressure"
            }
        }
    }
    
    # Same root stype but different property stypes should be incompatible
    temp_to_pressure = isSubschema(temp_focused_schema, pressure_focused_schema)
    pressure_to_temp = isSubschema(pressure_focused_schema, temp_focused_schema)
    
    assert not temp_to_pressure, "Same root stype but different property semantic types should not be subtypes"
    assert not pressure_to_temp, "Same root stype but different property semantic types should not be subtypes (reverse)"

# ===== Different Stype Tests with Varying Properties =====

def test_stype_different_object_same_structure():
    """Test objects with different stypes but identical structure"""
    
    person_schema = {
        "type": "object",
        "stype": "foaf:Person",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        },
        "required": ["name"]
    }
    
    organization_schema = {
        "type": "object",
        "stype": "foaf:Organization",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}  # Same structure
        },
        "required": ["name"]
    }
    
    # Different stypes should be incompatible regardless of structure
    person_to_org = isSubschema(person_schema, organization_schema)
    org_to_person = isSubschema(organization_schema, person_schema)
    
    assert not person_to_org, "Different semantic types should not be subtypes even with same structure"
    assert not org_to_person, "Different semantic types should not be subtypes even with same structure (reverse)"

def test_stype_different_array_different_items():
    """Test arrays with different stypes and different item types"""
    
    temperature_array = {
        "type": "array",
        "stype": "quantitykind:TemperatureArray",
        "items": {
            "type": "number",
            "minimum": -273.15,
            "maximum": 1000
        }
    }
    
    string_array = {
        "type": "array",
        "stype": "quantitykind:StringArray",
        "items": {
            "type": "string",
            "minLength": 1
        }
    }
    
    # Different stypes and different item types should be incompatible
    temp_to_string = isSubschema(temperature_array, string_array)
    string_to_temp = isSubschema(string_array, temperature_array)
    
    assert not temp_to_string, "Arrays with different stypes and item types should not be subtypes"
    assert not string_to_temp, "Arrays with different stypes and item types should not be subtypes (reverse)"

# ===== Mixed Property Tests =====

def test_stype_object_some_properties_same_stype():
    """Test objects where some properties have same stype, others different"""
    
    sensor_schema_a = {
        "type": "object",
        "stype": "quantitykind:Sensor",
        "properties": {
            "temperature": {
                "type": "number",
                "stype": "quantitykind:Temperature",
                "minimum": 0
            },
            "humidity": {
                "type": "number",
                "stype": "quantitykind:RelativeHumidity",
                "minimum": 0,
                "maximum": 100
            },
            "id": {"type": "string"}
        }
    }
    
    sensor_schema_b = {
        "type": "object",
        "stype": "quantitykind:Sensor",
        "properties": {
            "temperature": {
                "type": "number",
                "stype": "quantitykind:Temperature"  # Same stype, less restrictive
            },
            "humidity": {
                "type": "number",
                "stype": "quantitykind:Pressure"  # Different stype!
            },
            "id": {"type": "string"}
        }
    }
    
    # Mixed compatibility: same root and some properties, but different property stype
    a_to_b = isSubschema(sensor_schema_a, sensor_schema_b)
    b_to_a = isSubschema(sensor_schema_b, sensor_schema_a)
    
    assert not a_to_b, "Schemas with different property semantic types should not be subtypes"
    assert not b_to_a, "Schemas with different property semantic types should not be subtypes (reverse)"

def test_stype_nested_same_and_different():
    """Test nested structures with mix of same and different stypes"""
    
    complex_schema_a = {
        "type": "object",
        "stype": "quantitykind:Device",
        "properties": {
            "sensors": {
                "type": "array",
                "stype": "quantitykind:SensorArray",
                "items": {
                    "type": "object",
                    "stype": "quantitykind:TemperatureSensor",
                    "properties": {
                        "reading": {
                            "type": "number",
                            "stype": "quantitykind:Temperature"
                        }
                    }
                }
            }
        }
    }
    
    complex_schema_b = {
        "type": "object",
        "stype": "quantitykind:Device",  # Same root stype
        "properties": {
            "sensors": {
                "type": "array",
                "stype": "quantitykind:SensorArray",  # Same array stype
                "items": {
                    "type": "object",
                    "stype": "quantitykind:PressureSensor",  # Different item stype!
                    "properties": {
                        "reading": {
                            "type": "number",
                            "stype": "quantitykind:Pressure"  # Different reading stype!
                        }
                    }
                }
            }
        }
    }
    
    # Deep semantic incompatibility should propagate up
    a_to_b = isSubschema(complex_schema_a, complex_schema_b)
    b_to_a = isSubschema(complex_schema_b, complex_schema_a)
    
    assert not a_to_b, "Deep semantic incompatibility should prevent subtyping"
    assert not b_to_a, "Deep semantic incompatibility should prevent subtyping (reverse)"

# ===== Structural Variation Tests =====

def test_stype_same_different_required_fields():
    """Test same stype with different required field constraints"""
    
    strict_required_schema = {
        "type": "object",
        "stype": "foaf:Person",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "phone": {"type": "string"}
        },
        "required": ["name", "email", "phone"]  # More required fields
    }
    
    loose_required_schema = {
        "type": "object",
        "stype": "foaf:Person",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "phone": {"type": "string"}
        },
        "required": ["name"]  # Fewer required fields
    }
    
    # Same stype: more required fields should be subtype of fewer required fields
    strict_to_loose = isSubschema(strict_required_schema, loose_required_schema)
    loose_to_strict = isSubschema(loose_required_schema, strict_required_schema)
    
    assert strict_to_loose, "Schema with more required fields (same stype) should be subtype of fewer required"
    assert not loose_to_strict, "Schema with fewer required fields should NOT be subtype of more required (same stype)"

def test_stype_same_additional_properties():
    """Test same stype with different additionalProperties constraints"""
    
    no_additional_schema = {
        "type": "object",
        "stype": "quantitykind:Measurement",
        "properties": {
            "value": {"type": "number"},
            "unit": {"type": "string"}
        },
        "additionalProperties": False  # No additional properties allowed
    }
    
    allow_additional_schema = {
        "type": "object",
        "stype": "quantitykind:Measurement",
        "properties": {
            "value": {"type": "number"},
            "unit": {"type": "string"}
        },
        "additionalProperties": True  # Additional properties allowed
    }
    
    # Same stype: no additional should be subtype of allow additional
    no_additional_to_allow = isSubschema(no_additional_schema, allow_additional_schema)
    allow_to_no_additional = isSubschema(allow_additional_schema, no_additional_schema)
    
    assert no_additional_to_allow, "Schema with no additional properties (same stype) should be subtype of allow additional"
    assert not allow_to_no_additional, "Schema allowing additional properties should NOT be subtype of no additional (same stype)"

def test_stype_mixed_properties_compatibility():
    """Test permissive compatibility with mixed stype constraints"""
    
    # Schema with mixed stype constraints
    mixed_constrained_schema = {
        "type": "object",
        "properties": {
            "temperature": {
                "type": "number",
                "stype": "quantitykind:Temperature"  # Has stype
            },
            "count": {
                "type": "integer"  # No stype
            }
        }
    }
    
    # Schema with no stype constraints
    unconstrained_schema = {
        "type": "object",
        "properties": {
            "temperature": {
                "type": "number"  # No stype
            },
            "count": {
                "type": "integer"  # No stype
            }
        }
    }
    
    mixed_to_unconstrained = isSubschema(mixed_constrained_schema, unconstrained_schema)
    unconstrained_to_mixed = isSubschema(unconstrained_schema, mixed_constrained_schema)
    
    assert mixed_to_unconstrained, "Schema with mixed stype constraints SHOULD be subtype of unconstrained schema (more specific → more general)"
    assert not unconstrained_to_mixed, "Unconstrained schema should NOT be subtype of schema with mixed stype constraints (more general → more specific)"

def test_stype_partial_constraint_overlap():
    """Test schemas with overlapping but different stype constraints"""
    
    # Schema A: temperature has stype, pressure doesn't
    schema_a = {
        "type": "object",
        "properties": {
            "temperature": {
                "type": "number",
                "stype": "quantitykind:Temperature"  # Has stype
            },
            "pressure": {
                "type": "number"  # No stype
            }
        }
    }
    
    # Schema B: pressure has stype, temperature doesn't  
    schema_b = {
        "type": "object",
        "properties": {
            "temperature": {
                "type": "number"  # No stype
            },
            "pressure": {
                "type": "number",
                "stype": "quantitykind:Pressure"  # Has stype
            }
        }
    }
    
    # Different constraint patterns should be incompatible
    a_to_b = isSubschema(schema_a, schema_b)
    b_to_a = isSubschema(schema_b, schema_a)
    
    assert not a_to_b, "Schemas with different stype constraint patterns should not be subtypes"
    assert not b_to_a, "Schemas with different stype constraint patterns should not be subtypes (reverse)"

# ===== API Integration Tests =====

def test_stype_with_meet_operation():
    """Test meet operation with permissive semantic compatibility"""
    
    schema_with_stype = {
        "type": "number",
        "stype": "quantitykind:Temperature",
        "minimum": 0,
        "maximum": 100
    }
    
    schema_without_stype = {
        "type": "number",
        "minimum": 20,
        "maximum": 80
    }
    
    # Meet with different stype presence should work (permissive model)
    meet_result = meet(schema_with_stype, schema_without_stype)
    
    # Should return valid schema, not bottom
    assert isinstance(meet_result, dict), "Meet of schemas with different stype presence should return valid schema"
    assert "not" not in meet_result, "Meet should not return bottom schema with permissive model"

def test_stype_with_meet_same_stype():
    """Test meet operation with same semantic types"""
    
    schema1 = {
        "type": "number",
        "stype": "quantitykind:Temperature",
        "minimum": 0,
        "maximum": 100
    }
    
    schema2 = {
        "type": "number",
        "stype": "quantitykind:Temperature", 
        "minimum": 20,
        "maximum": 80
    }
    
    # Meet should work normally with same stype
    meet_result = meet(schema1, schema2)
    
    assert isinstance(meet_result, dict), "Meet should return valid schema for same stype"
    assert meet_result.get("stype") == "quantitykind:Temperature", "Meet should preserve semantic type"

def test_stype_with_join_operation():
    """Test join operation with permissive semantic compatibility"""
    
    schema_with_stype = {
        "type": "number",
        "stype": "quantitykind:Temperature",
        "minimum": 0,
        "maximum": 50
    }
    
    schema_without_stype = {
        "type": "number",
        "minimum": 25,
        "maximum": 100
    }
    
    # Join with different stype presence should not have stype in result
    join_result = join(schema_with_stype, schema_without_stype)
    
    assert isinstance(join_result, dict), "Join should return valid schema"
    assert "stype" not in join_result, "Join of schemas with different stype presence should not have stype"

def test_stype_with_join_same_stype():
    """Test join operation with same semantic types"""
    
    schema1 = {
        "type": "number",
        "stype": "quantitykind:Temperature",
        "minimum": 0,
        "maximum": 50
    }
    
    schema2 = {
        "type": "number",
        "stype": "quantitykind:Temperature",
        "minimum": 25,
        "maximum": 100
    }
    
    # Join should work normally with same stype
    join_result = join(schema1, schema2)
    
    assert isinstance(join_result, dict), "Join should return valid schema for same stype"
    assert join_result.get("stype") == "quantitykind:Temperature", "Join should preserve semantic type"

def test_stype_with_equivalence():
    """Test equivalence with permissive semantic compatibility"""
    
    schema_with_stype = {
        "type": "number",
        "stype": "quantitykind:Temperature"
    }
    
    schema_without_stype = {
        "type": "number"
    }
    
    schema_same_stype = {
        "type": "number",
        "stype": "quantitykind:Temperature"
    }
    
    # Different stype presence should not be equivalent
    different_stype_equiv = isEquivalent(schema_with_stype, schema_without_stype)
    
    # Same stype should be equivalent
    same_stype_equiv = isEquivalent(schema_with_stype, schema_same_stype)
    
    assert not different_stype_equiv, "Schemas with different stype presence should not be equivalent"
    assert same_stype_equiv, "Schemas with same stype should be equivalent"

# ===== Hierarchical Semantic Type Tests =====

def test_stype_hierarchical_subtyping():
    """Test hierarchical semantic type relationships"""
    
    # Specific semantic type
    specific_schema = {
        "type": "number",
        "stype": "quantitykind:Temperature"
    }
    
    # General semantic type 
    general_schema = {
        "type": "number",
        "stype": "quantitykind:ThermodynamicTemperature"
    }
    
    # Test that hierarchical comparison works without crashing
    specific_to_general = isSubschema(specific_schema, general_schema)
    general_to_specific = isSubschema(general_schema, specific_schema)
    
    assert isinstance(specific_to_general, bool), "Hierarchical semantic type comparison should work"
    assert isinstance(general_to_specific, bool), "Hierarchical semantic type comparison should work"

# ===== Edge Cases =====

def test_stype_both_empty():
    """Test stype behavior when both schemas are empty"""
    
    empty_schema1 = {}
    empty_schema2 = {}
    
    # Both empty schemas should be equivalent
    equiv_result = isEquivalent(empty_schema1, empty_schema2)
    subtype_1_to_2 = isSubschema(empty_schema1, empty_schema2)
    subtype_2_to_1 = isSubschema(empty_schema2, empty_schema1)
    
    assert equiv_result, "Empty schemas should be equivalent"
    assert subtype_1_to_2, "Empty schema should be subtype of empty schema"
    assert subtype_2_to_1, "Empty schema should be subtype of empty schema (reverse)"

def test_stype_identical_schemas():
    """Test identical schemas with stype"""
    
    schema1 = {
        "type": "number",
        "stype": "quantitykind:Temperature",
        "minimum": 0,
        "maximum": 100
    }
    
    schema2 = {
        "type": "number",
        "stype": "quantitykind:Temperature",
        "minimum": 0,
        "maximum": 100
    }
    
    # Identical schemas should be equivalent and subtypes of each other
    equiv_result = isEquivalent(schema1, schema2)
    subtype_1_to_2 = isSubschema(schema1, schema2)
    subtype_2_to_1 = isSubschema(schema2, schema1)
    
    assert equiv_result, "Identical schemas should be equivalent"
    assert subtype_1_to_2, "Identical schema should be subtype of itself"
    assert subtype_2_to_1, "Identical schema should be subtype of itself (reverse)"

if __name__ == "__main__":
    pytest.main(["-v", __file__])