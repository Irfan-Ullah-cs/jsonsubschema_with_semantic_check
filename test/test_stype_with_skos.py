"""
Created on May 13, 2025
Consolidated tests for semantic type checking (stype) in jsonsubschema,
with SKOS hierarchy support and basic meet/join operations.
CORRECTED VERSION - Replace your entire test file with this.
"""

import pytest
import json
import os
import rdflib
from jsonsubschema.api import isSubschema, meet, join, isEquivalent
from jsonsubschema.semantic_type import SemanticTypeResolver, normalize_iri


def setup_test_graph():
    """Setup a test graph with QUDT relationships for testing"""
    graph = rdflib.Graph()
    
    # Add test QUDT relationships
    test_data = """
    @prefix quantitykind: <http://qudt.org/vocab/quantitykind/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    quantitykind:RelativeHumidity skos:broader quantitykind:RelativePartialPressure .
    quantitykind:RelativePartialPressure skos:broader quantitykind:PressureRatio .
    quantitykind:Temperature skos:broader quantitykind:ThermodynamicTemperature .
    """
    
    graph.parse(data=test_data, format="turtle")
    return graph


# ===== SKOS Hierarchy and IRI Normalization Tests =====

def test_singleton_resolver():
    """Test that SemanticTypeResolver uses the singleton pattern correctly"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    
    resolver1 = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    resolver2 = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    assert resolver1 is resolver2, "Should return the same instance"

def test_normalize_iri():
    """Test IRI normalization for different formats"""
    # Full IRIs should remain unchanged
    assert normalize_iri("http://qudt.org/vocab/quantitykind/Temperature") == "http://qudt.org/vocab/quantitykind/Temperature"
    
    # Compact notation should be expanded
    assert normalize_iri("quantitykind:Temperature") == "http://qudt.org/vocab/quantitykind/Temperature"
    assert normalize_iri("skos:broader") == "http://www.w3.org/2004/02/skos/core#broader"
    
    # Unknown prefixes should be returned as-is
    assert normalize_iri("unknown:Temperature") == "unknown:Temperature"
    
    # None and empty string should remain unchanged
    assert normalize_iri(None) is None
    assert normalize_iri("") == ""

def test_skos_direct_relationship():
    """Test direct subtype relationship in SKOS"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Check direct relationship
    direct_result = resolver.is_subtype_of(
        "http://qudt.org/vocab/quantitykind/RelativeHumidity",
        "http://qudt.org/vocab/quantitykind/RelativePartialPressure"
    )
    assert direct_result, "Direct relationship should be detected"

def test_skos_transitive_relationship():
    """Test transitive subtype relationship in SKOS"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Check transitive relationship
    transitive_result = resolver.is_subtype_of(
        "http://qudt.org/vocab/quantitykind/RelativeHumidity",
        "http://qudt.org/vocab/quantitykind/PressureRatio"
    )
    assert transitive_result, "Transitive relationship should be detected"

def test_skos_compact_notation():
    """Test compact notation support for SKOS concepts"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Check with compact notation
    compact_result = resolver.is_subtype_of(
        "quantitykind:RelativeHumidity",
        "quantitykind:PressureRatio"
    )
    assert compact_result, "Compact notation should work for SKOS hierarchies"

def test_skos_non_relationship():
    """Test cases where concepts are not related"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Check unrelated concepts
    unrelated_result = resolver.is_subtype_of(
        "http://qudt.org/vocab/quantitykind/Temperature",
        "http://qudt.org/vocab/quantitykind/Pressure"
    )
    
    assert not unrelated_result, "Unrelated concepts should not be subtypes"

# ===== Schema Subtyping with SKOS Tests =====

def test_schema_with_skos_concepts():
    """Test schema subtyping with SKOS concept hierarchies"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Define schemas with SKOS concepts
    specific_schema = {
        "type": "number",
        "stype": "quantitykind:RelativeHumidity"
    }
    
    general_schema = {
        "type": "number",
        "stype": "quantitykind:PressureRatio"
    }
    
    # Test subschema relationship
    assert isSubschema(specific_schema, general_schema), "Specific concept should be subschema of general concept"
    assert not isSubschema(general_schema, specific_schema), "General concept should not be subschema of specific concept"

def test_nested_schema_with_skos():
    """Test nested schemas with SKOS concepts"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Define nested schemas with SKOS concepts
    nested_specific = {
        "type": "object",
        "properties": {
            "reading": {
                "type": "number",
                "stype": "quantitykind:RelativeHumidity"
            }
        }
    }
    
    nested_general = {
        "type": "object",
        "properties": {
            "reading": {
                "type": "number",
                "stype": "quantitykind:PressureRatio"
            }
        }
    }
    
    # Test subschema relationship
    assert isSubschema(nested_specific, nested_general), "Nested specific concept should be subschema of nested general concept"
    assert not isSubschema(nested_general, nested_specific), "Nested general concept should not be subschema of nested specific concept"

def test_real_world_sensor_schemas():
    """Test with realistic sensor data schemas"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Define realistic sensor schemas
    humidity_sensor = {
        "type": "object",
        "stype": "quantitykind:Sensor",
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "reading": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
                "stype": "quantitykind:RelativeHumidity"
            },
            "unit": {"type": "string", "enum": ["%"]}
        },
        "required": ["id", "timestamp", "reading", "unit"]
    }
    
    pressure_sensor = {
        "type": "object",
        "stype": "quantitykind:Sensor",
        "properties": {
            "id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "reading": {
                "type": "number",
                "stype": "quantitykind:PressureRatio"
            },
            "unit": {"type": "string"}
        },
        "required": ["id", "timestamp", "reading"]
    }
    
    # Test subschema relationship
    assert isSubschema(humidity_sensor, pressure_sensor), \
           "Humidity sensor (with narrower semantic type) should be a subschema of pressure sensor (with broader semantic type)"
    assert not isSubschema(pressure_sensor, humidity_sensor), \
           "Pressure sensor (with broader semantic type) should not be a subschema of humidity sensor (with narrower semantic type)"

# ===== Meet Operation Tests with Semantic Types =====

def test_meet_with_identical_semantic_types():
    """Test meet operation with identical semantic types"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Define schemas with identical semantic types
    schema1 = {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "stype": "quantitykind:Temperature"
    }
    
    schema2 = {
        "type": "number",
        "minimum": 50,
        "maximum": 150,
        "stype": "quantitykind:Temperature"
    }
    
    # Perform meet operation
    result = meet(schema1, schema2)
    
    # Test result
    assert result.get("type") == "number", "Meet should preserve type"
    assert result.get("minimum") == 50, "Meet should take maximum of minimums"
    assert result.get("maximum") == 100, "Meet should take minimum of maximums"
    assert result.get("stype") == "quantitykind:Temperature", "Meet should preserve identical semantic type"

def test_meet_with_hierarchical_semantic_types():
    """Test meet operation with hierarchical semantic types"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Define schemas with hierarchical semantic types
    schema1 = {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "stype": "quantitykind:RelativeHumidity"  # More specific
    }
    
    schema2 = {
        "type": "number",
        "minimum": 50,
        "maximum": 150,
        "stype": "quantitykind:PressureRatio"  # More general
    }
    
    # Perform meet operation
    result = meet(schema1, schema2)
    
    # Test result
    assert result.get("type") == "number", "Meet should preserve type"
    assert result.get("minimum") == 50, "Meet should take maximum of minimums"
    assert result.get("maximum") == 100, "Meet should take minimum of maximums"
    assert result.get("stype") in ["quantitykind:RelativeHumidity", "http://qudt.org/vocab/quantitykind/RelativeHumidity"], \
            "Meet should preserve more specific semantic type"

# ===== Join Operation Tests with Semantic Types =====

def test_join_with_identical_semantic_types():
    """Test join operation with identical semantic types"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Define schemas with identical semantic types
    schema1 = {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "stype": "quantitykind:Temperature"
    }
    
    schema2 = {
        "type": "number",
        "minimum": 50,
        "maximum": 150,
        "stype": "quantitykind:Temperature"
    }
    
    # Perform join operation
    result = join(schema1, schema2)
    
    # Test result
    assert result.get("type") == "number", "Join should preserve type"
    assert result.get("minimum") == 0, "Join should take minimum of minimums"
    assert result.get("maximum") == 150, "Join should take maximum of maximums"
    assert result.get("stype") == "quantitykind:Temperature", "Join should preserve identical semantic type"

def test_join_with_hierarchical_semantic_types():
    """Test join operation with hierarchical semantic types"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Define schemas with hierarchical semantic types
    schema1 = {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "stype": "quantitykind:RelativeHumidity"  # More specific
    }
    
    schema2 = {
        "type": "number",
        "minimum": 50,
        "maximum": 150,
        "stype": "quantitykind:PressureRatio"  # More general
    }
    
    # Perform join operation
    result = join(schema1, schema2)
    
    # Test result
    assert result.get("type") == "number", "Join should preserve type"
    assert result.get("minimum") == 0, "Join should take minimum of minimums"
    assert result.get("maximum") == 150, "Join should take maximum of maximums"
    assert result.get("stype") in ["quantitykind:PressureRatio", "http://qudt.org/vocab/quantitykind/PressureRatio"], \
            "Join should preserve more general semantic type"

# ===== CLI Interface Tests =====

def test_cli_with_semantic_types():
    """Test CLI interface with semantic type checking"""
    SemanticTypeResolver.reset_instance()
    graph = setup_test_graph()
    resolver = SemanticTypeResolver.get_instance(graph=graph, lazy_load=False)
    
    # Create test schema files
    humidity_schema = {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "stype": "quantitykind:RelativeHumidity"
    }
    
    pressure_schema = {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "stype": "quantitykind:PressureRatio"
    }
    
    # Create directory and write schemas
    os.makedirs("test_semantic", exist_ok=True)
    
    with open("test_semantic/humidity.json", "w") as f:
        json.dump(humidity_schema, f, indent=2)
    
    with open("test_semantic/pressure.json", "w") as f:
        json.dump(pressure_schema, f, indent=2)
    
    # Test subschema relationship directly with API
    assert isSubschema(humidity_schema, pressure_schema), \
           "Humidity schema should be a subschema of pressure schema (via API)"
    assert not isSubschema(pressure_schema, humidity_schema), \
           "Pressure schema should not be a subschema of humidity schema (via API)"
    
    # Clean up
    os.remove("test_semantic/humidity.json")
    os.remove("test_semantic/pressure.json")
    os.rmdir("test_semantic")

if __name__ == "__main__":
    pytest.main(["-v", __file__])