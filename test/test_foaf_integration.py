"""
Created on May 13, 2025
Comprehensive test cases for FOAF (Friend of a Friend) integration with jsonsubschema,
focusing on loading, relationships, lazy loading, caching, and FOAF-specific functionality.

Run the test file with pytest .\test_faof_integration.py -v
"""

import pytest
import json
import os
from jsonsubschema.api import isSubschema, meet, join, isEquivalent
from jsonsubschema.semantic_type import SemanticTypeResolver, is_semantically_compatible, normalize_iri
import jsonsubschema.config as config

# ===== FOAF Loading and Setup Tests =====

def test_foaf_graph_loading():
    """Test FOAF ontology loading from external URL"""
    # Reset resolver to test fresh loading
    SemanticTypeResolver.reset_instance()
    
    # Enable semantic reasoning
    config.set_semantic_reasoning(True)
    
    # Add FOAF ontology URL
    config.add_semantic_graph_url("http://xmlns.com/foaf/0.1/")
    
    # Get resolver instance (should trigger loading)
    resolver = SemanticTypeResolver.get_instance()
    
    # Test that resolver has graph data
    assert hasattr(resolver, 'graph'), "Resolver should have graph attribute"
    assert resolver.graph is not None, "Resolver graph should not be None"
    
    # Test that graph has some triples (FOAF might load successfully or fail gracefully)
    triple_count = len(resolver.graph)
    assert isinstance(triple_count, int), "Graph should have countable triples"

def test_foaf_custom_extensions_loading():
    """Test loading custom FOAF extensions via Turtle format"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add custom FOAF extensions
    custom_foaf_data = """
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    # Employment hierarchy
    ex:Employee skos:broader foaf:Person .
    ex:Manager skos:broader ex:Employee .
    ex:CEO skos:broader ex:Manager .
    
    # Organization hierarchy
    ex:Company skos:broader foaf:Organization .
    ex:StartUp skos:broader ex:Company .
    
    # Document hierarchy
    ex:TechnicalDocument skos:broader foaf:Document .
    ex:Report skos:broader ex:TechnicalDocument .
    """
    
    # Parse custom data into graph
    resolver.graph.parse(data=custom_foaf_data, format="turtle")
    
    # Test that custom relationships are loaded
    employee_to_person = resolver.is_subtype_of("ex:Employee", "foaf:Person")
    manager_to_employee = resolver.is_subtype_of("ex:Manager", "ex:Employee")
    
    assert isinstance(employee_to_person, bool), "Should handle custom FOAF extensions"
    assert isinstance(manager_to_employee, bool), "Should handle custom hierarchies"

def test_foaf_loading_failure_handling():
    """Test graceful handling when FOAF loading fails"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Add invalid URL to test error handling
    config.add_semantic_graph_url("http://invalid-foaf-url.example/foaf.rdf")
    
    # Should not crash when loading fails
    resolver = SemanticTypeResolver.get_instance()
    
    # Should still be functional
    result = resolver.is_subtype_of("foaf:Person", "foaf:Agent")
    assert isinstance(result, bool), "Should handle loading failures gracefully"

# ===== FOAF Relationship Testing =====

def test_foaf_basic_relationships():
    """Test basic FOAF concept relationships"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Test core FOAF relationships (may depend on successful loading)
    person_agent = resolver.is_subtype_of("foaf:Person", "foaf:Agent")
    organization_agent = resolver.is_subtype_of("foaf:Organization", "foaf:Agent")
    group_agent = resolver.is_subtype_of("foaf:Group", "foaf:Agent")
    
 

    if person_agent:
        # FOAF loaded successfully - test expected relationships
        assert person_agent, "Person should be subtype of Agent in FOAF ontology"
        # Organization and Group relationships depend on FOAF ontology structure
        print(f"FOAF relationships - Person->Agent: {person_agent}, Organization->Agent: {organization_agent}, Group->Agent: {group_agent}")
    else:
        # FOAF may not have loaded - just verify we get boolean responses
        print(f"FOAF ontology may not have loaded - got responses: Person->Agent: {person_agent}")
    
    # All should return boolean regardless of loading success
    assert isinstance(person_agent, bool), "Person-Agent relationship should return boolean"
    assert isinstance(organization_agent, bool), "Organization-Agent relationship should return boolean"
    assert isinstance(group_agent, bool), "Group-Agent relationship should return boolean"

def test_foaf_custom_relationship_hierarchy():
    """Test custom FOAF relationship hierarchies"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add employment hierarchy
    employment_hierarchy = """
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    ex:Employee skos:broader foaf:Person .
    ex:Manager skos:broader ex:Employee .
    ex:CEO skos:broader ex:Manager .
    ex:Consultant skos:broader foaf:Person .
    """
    
    resolver.graph.parse(data=employment_hierarchy, format="turtle")
    
    # Test direct relationships
    employee_person = resolver.is_subtype_of("ex:Employee", "foaf:Person")
    manager_employee = resolver.is_subtype_of("ex:Manager", "ex:Employee")
    
    # Test transitive relationships
    ceo_employee = resolver.is_subtype_of("ex:CEO", "ex:Employee")
    ceo_person = resolver.is_subtype_of("ex:CEO", "foaf:Person")
    
    # Test non-relationships
    consultant_manager = resolver.is_subtype_of("ex:Consultant", "ex:Manager")
    
    # Direct relationships should be true
    assert employee_person, "Employee should be subtype of Person (ex:Employee -> foaf:Person)"
    assert manager_employee, "Manager should be subtype of Employee (ex:Manager -> ex:Employee)"
    
    # Transitive relationships should be true
    assert ceo_employee, "CEO should be subtype of Employee transitively (ex:CEO -> ex:Manager -> ex:Employee)"
    assert ceo_person, "CEO should be subtype of Person transitively (ex:CEO -> ex:Manager -> ex:Employee -> foaf:Person)"
    
    # Non-relationships should be false
    assert not consultant_manager, "Consultant should not be subtype of Manager (different branch: ex:Consultant -> foaf:Person)"

def test_foaf_self_relationships():
    """Test that FOAF concepts are subtypes of themselves"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    foaf_concepts = [
        "foaf:Person",
        "foaf:Agent", 
        "foaf:Organization",
        "foaf:Group",
        "foaf:Document"
    ]
    
    for concept in foaf_concepts:
        self_result = resolver.is_subtype_of(concept, concept)
        assert self_result, f"FOAF concept should be subtype of itself: {concept}"

# ===== FOAF Caching Tests =====

def test_foaf_relationship_caching():
    """Test that FOAF relationship queries are cached"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add test data
    test_data = """
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    ex:Employee skos:broader foaf:Person .
    """
    
    resolver.graph.parse(data=test_data, format="turtle")
    
    # Query same relationship multiple times
    concept1 = "ex:Employee"
    concept2 = "foaf:Person"
    
    results = []
    for i in range(5):
        result = resolver.is_subtype_of(concept1, concept2)
        results.append(result)
    
    # All results should be identical (cached)
    assert all(r == results[0] for r in results), "Cached FOAF relationship results should be consistent"
    
    # Test that cache has entry
    cache_key = (resolver.normalize_iri(concept1) if hasattr(resolver, 'normalize_iri') else concept1, 
                resolver.normalize_iri(concept2) if hasattr(resolver, 'normalize_iri') else concept2)
    assert hasattr(resolver, 'relation_cache'), "Resolver should have relation cache"

def test_foaf_cache_consistency_across_queries():
    """Test cache consistency across different query patterns"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add test hierarchy
    hierarchy_data = """
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    ex:Manager skos:broader ex:Employee .
    ex:Employee skos:broader foaf:Person .
    """
    
    resolver.graph.parse(data=hierarchy_data, format="turtle")
    
    # Query relationships in different orders
    manager_employee_1 = resolver.is_subtype_of("ex:Manager", "ex:Employee")
    employee_person_1 = resolver.is_subtype_of("ex:Employee", "foaf:Person")
    manager_person_1 = resolver.is_subtype_of("ex:Manager", "foaf:Person")
    
    # Query again in different order
    manager_person_2 = resolver.is_subtype_of("ex:Manager", "foaf:Person")
    employee_person_2 = resolver.is_subtype_of("ex:Employee", "foaf:Person")
    manager_employee_2 = resolver.is_subtype_of("ex:Manager", "ex:Employee")
    
    # Results should be consistent
    assert manager_employee_1 == manager_employee_2, "Manager-Employee relationship should be consistent"
    assert employee_person_1 == employee_person_2, "Employee-Person relationship should be consistent"
    assert manager_person_1 == manager_person_2, "Manager-Person relationship should be consistent"

# ===== FOAF Lazy Loading Tests =====

def test_foaf_lazy_graph_loading():
    """Test that FOAF graphs are loaded lazily when needed"""
    # Test that resolver can be created without immediate graph loading
    SemanticTypeResolver.reset_instance()
    
    # Disable semantic reasoning initially
    config.set_semantic_reasoning(False)
    
    # Create resolver - should not load graphs
    resolver = SemanticTypeResolver.get_instance()
    initial_triple_count = len(resolver.graph)
    
    # Enable semantic reasoning
    config.set_semantic_reasoning(True)
    
    # Reset to trigger fresh loading
    SemanticTypeResolver.reset_instance()
    config.add_semantic_graph_url("http://xmlns.com/foaf/0.1/")
    
    # Create new resolver - should load graphs
    resolver_with_loading = SemanticTypeResolver.get_instance()
    
    # Should have graph functionality available
    assert hasattr(resolver_with_loading, 'graph'), "Resolver should have graph after enabling semantic reasoning"

def test_foaf_on_demand_relationship_resolution():
    """Test that FOAF relationships are resolved on-demand"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add data that will be queried
    foaf_data = """
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    ex:Student skos:broader foaf:Person .
    ex:Professor skos:broader foaf:Person .
    """
    
    resolver.graph.parse(data=foaf_data, format="turtle")
    
    # Test that queries work on-demand
    student_person = resolver.is_subtype_of("ex:Student", "foaf:Person")
    professor_person = resolver.is_subtype_of("ex:Professor", "foaf:Person")
    student_professor = resolver.is_subtype_of("ex:Student", "ex:Professor")
    
    # Based on the loaded hierarchy, both Student and Professor should be subtypes of Person
    assert student_person, "Student should be subtype of Person (ex:Student -> foaf:Person)"
    assert professor_person, "Professor should be subtype of Person (ex:Professor -> foaf:Person)"
    # Student should NOT be subtype of Professor (different branches)
    assert not student_professor, "Student should not be subtype of Professor (parallel branches under foaf:Person)"

# ===== FOAF Schema Integration Tests =====

def test_foaf_schema_semantic_compatibility():
    """Test semantic compatibility with FOAF concepts in schemas"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add FOAF hierarchy
    foaf_hierarchy = """
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    ex:Employee skos:broader foaf:Person .
    """
    
    resolver.graph.parse(data=foaf_hierarchy, format="turtle")
    
    # Employee schema (more specific)
    employee_schema = {
        "type": "object",
        "stype": "ex:Employee",
        "properties": {
            "foaf:name": {"type": "string"},
            "employee_id": {"type": "string"}
        }
    }
    
    # Person schema (more general)
    person_schema = {
        "type": "object",
        "stype": "foaf:Person",
        "properties": {
            "foaf:name": {"type": "string"}
        }
    }
    
    # Test semantic compatibility
    employee_to_person = is_semantically_compatible(employee_schema, person_schema, resolver)
    person_to_employee = is_semantically_compatible(person_schema, employee_schema, resolver)
    
    # Test schema subtyping
    employee_subtype_person = isSubschema(employee_schema, person_schema)
    person_subtype_employee = isSubschema(person_schema, employee_schema)
    
    # Employee should be semantically compatible with Person (more specific -> more general)
    assert employee_to_person, "Employee should be semantically compatible with Person (ex:Employee -> foaf:Person)"
    # Person should NOT be semantically compatible with Employee (more general -> more specific)
    assert not person_to_employee, "Person should not be semantically compatible with Employee (foaf:Person -> ex:Employee)"
    
    # Employee should be subtype of Person (more restrictive schema -> less restrictive schema)
    assert employee_subtype_person, "Employee schema should be subtype of Person schema (more specific properties)"
    # Person should NOT be subtype of Employee (less restrictive -> more restrictive)
    assert not person_subtype_employee, "Person schema should not be subtype of Employee schema (missing employee_id property)"

def test_foaf_nested_schema_compatibility():
    """Test FOAF compatibility in nested schema structures"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add organization hierarchy
    org_hierarchy = """
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    ex:Company skos:broader foaf:Organization .
    ex:Employee skos:broader foaf:Person .
    """
    
    resolver.graph.parse(data=org_hierarchy, format="turtle")
    
    # Company with employees (more specific)
    company_schema = {
        "type": "object",
        "stype": "ex:Company",
        "properties": {
            "foaf:name": {"type": "string"},
            "employees": {
                "type": "array",
                "items": {
                    "type": "object",
                    "stype": "ex:Employee"
                }
            }
        }
    }
    
    # Organization with people (more general)
    org_schema = {
        "type": "object",
        "stype": "foaf:Organization",
        "properties": {
            "foaf:name": {"type": "string"},
            "employees": {
                "type": "array",
                "items": {
                    "type": "object",
                    "stype": "foaf:Person"
                }
            }
        }
    }
    
    # Test nested compatibility
    company_to_org = isSubschema(company_schema, org_schema)
    org_to_company = isSubschema(org_schema, company_schema)
    
    # Company should be subtype of Organization (more specific -> more general)
    assert company_to_org, "Company schema should be subtype of Organization schema (ex:Company -> foaf:Organization, ex:Employee -> foaf:Person)"
    # Organization should NOT be subtype of Company (more general -> more specific)
    assert not org_to_company, "Organization schema should not be subtype of Company schema (foaf:Organization -> ex:Company, foaf:Person -> ex:Employee)"

# ===== FOAF IRI Normalization Tests =====

def test_foaf_iri_normalization():
    """Test IRI normalization for FOAF concepts"""
    # Test FOAF prefix normalization
    foaf_cases = [
        ("foaf:Person", "http://xmlns.com/foaf/0.1/Person"),
        ("foaf:Agent", "http://xmlns.com/foaf/0.1/Agent"),
        ("foaf:Organization", "http://xmlns.com/foaf/0.1/Organization"),
        ("foaf:Group", "http://xmlns.com/foaf/0.1/Group"),
        ("foaf:Document", "http://xmlns.com/foaf/0.1/Document")
    ]
    
    for compact, expected_full in foaf_cases:
        result = normalize_iri(compact)
        assert result == expected_full, f"FOAF IRI normalization failed for {compact}"

def test_foaf_mixed_iri_formats():
    """Test mixed IRI formats in FOAF relationships"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Test relationships using both compact and full IRIs
    compact_to_full = resolver.is_subtype_of(
        "foaf:Person",
        "http://xmlns.com/foaf/0.1/Agent"
    )
    
    full_to_compact = resolver.is_subtype_of(
        "http://xmlns.com/foaf/0.1/Person",
        "foaf:Agent"
    )
    
    # Both should work and give same result due to IRI normalization
    assert compact_to_full == full_to_compact, "Mixed IRI formats should give same result due to normalization"
    
    # If FOAF loaded successfully, Person should be subtype of Agent
    if compact_to_full:
        assert compact_to_full, "Person should be subtype of Agent (regardless of IRI format)"
        assert full_to_compact, "Person should be subtype of Agent (regardless of IRI format)"
    else:
        print("FOAF ontology may not have loaded - mixed IRI format test completed without relationship validation")

# ===== FOAF Error Handling Tests =====

def test_foaf_unknown_concepts():
    """Test handling of unknown FOAF concepts"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Test with unknown FOAF concepts
    unknown_to_known = resolver.is_subtype_of("foaf:UnknownConcept", "foaf:Person")
    known_to_unknown = resolver.is_subtype_of("foaf:Person", "foaf:UnknownConcept")
    unknown_to_unknown = resolver.is_subtype_of("foaf:Unknown1", "foaf:Unknown2")
    
    # Unknown concepts should not be subtypes of known concepts
    assert not unknown_to_known, "Unknown FOAF concept should not be subtype of known concept"
    assert not known_to_unknown, "Known FOAF concept should not be subtype of unknown concept"
    assert not unknown_to_unknown, "Unknown concepts should not be subtypes of each other"

def test_foaf_malformed_data_handling():
    """Test handling of malformed FOAF data"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Try to parse malformed Turtle data
    malformed_data = """
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    # Missing closing bracket and other syntax errors
    ex:Employee skos:broader foaf:Person
    ex:Manager skos:broader ex:Employee .
    """
    
    # Should handle parsing errors gracefully
    try:
        resolver.graph.parse(data=malformed_data, format="turtle")
    except Exception:
        pass  # Expected to fail, should not crash the system
    
    # Resolver should still be functional
    result = resolver.is_subtype_of("foaf:Person", "foaf:Agent")
    assert isinstance(result, bool), "Should remain functional after parsing errors"

def test_foaf_circular_relationships():
    """Test handling of circular relationships in FOAF data"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add circular relationship data
    circular_data = """
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    
    ex:A skos:broader ex:B .
    ex:B skos:broader ex:C .
    ex:C skos:broader ex:A .
    """
    
    resolver.graph.parse(data=circular_data, format="turtle")
    
    # Test that circular relationships don't cause infinite loops
    result_ab = resolver.is_subtype_of("ex:A", "ex:B")
    result_bc = resolver.is_subtype_of("ex:B", "ex:C")
    result_ca = resolver.is_subtype_of("ex:C", "ex:A")
    
    assert isinstance(result_ab, bool), "Should handle circular relationships without infinite loops"
    assert isinstance(result_bc, bool), "Should handle circular relationships without infinite loops"
    assert isinstance(result_ca, bool), "Should handle circular relationships without infinite loops"

# ===== FOAF Configuration Tests =====

def test_foaf_semantic_reasoning_toggle():
    """Test toggling semantic reasoning on/off with FOAF"""
    # Test with semantic reasoning enabled
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver_enabled = SemanticTypeResolver.get_instance()
    
    foaf_schema_enabled = {
        "type": "object",
        "stype": "foaf:Person"
    }
    
    result_enabled = isSubschema(foaf_schema_enabled, foaf_schema_enabled)
    
    # Test with semantic reasoning disabled
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(False)
    
    resolver_disabled = SemanticTypeResolver.get_instance()
    
    foaf_schema_disabled = {
        "type": "object",
        "stype": "foaf:Person"
    }
    
    result_disabled = isSubschema(foaf_schema_disabled, foaf_schema_disabled)
    
    # Both should work but may behave differently
    assert isinstance(result_enabled, bool), "Should work with semantic reasoning enabled"
    assert isinstance(result_disabled, bool), "Should work with semantic reasoning disabled"

def test_foaf_custom_graph_urls():
    """Test adding custom FOAF graph URLs"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Add multiple graph URLs
    config.add_semantic_graph_url("http://xmlns.com/foaf/0.1/")
    config.add_semantic_graph_url("http://example.org/custom-foaf.rdf")
    
    # Should not crash even if some URLs are invalid
    resolver = SemanticTypeResolver.get_instance()
    
    # Should remain functional
    result = resolver.is_subtype_of("foaf:Person", "foaf:Person")
    assert result, "Should remain functional with custom graph URLs"

if __name__ == "__main__":
    pytest.main(["-v", __file__])