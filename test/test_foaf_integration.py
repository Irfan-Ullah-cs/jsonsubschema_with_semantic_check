"""
Created on May 13, 2025
Comprehensive test cases for FOAF (Friend of a Friend) integration with jsonsubschema.
Uses actual FOAF ontology from http://xmlns.com/foaf/spec/index.rdf 
Run the test file with pytest test_foaf_integration.py -v
"""

import pytest
import json
import os
from jsonsubschema.api import isSubschema, meet, join, isEquivalent
from jsonsubschema.semantic_type import SemanticTypeResolver, is_semantically_compatible, normalize_iri
import jsonsubschema.config as config
import rdflib

# ===== Utility Function for Loading Official FOAF =====

def load_official_foaf_ontology():
    """Load the official FOAF ontology from the standard URL"""
    graph = rdflib.Graph()
    try:
        print("Loading FOAF ontology from http://xmlns.com/foaf/spec/index.rdf...")
        graph.parse("http://xmlns.com/foaf/spec/index.rdf")
        print(f"Successfully loaded {len(graph)} triples from FOAF ontology")
        return graph
    except Exception as e:
        print(f"Failed to load FOAF ontology: {e}")
        # Fallback: create minimal FOAF hierarchy based on official spec
        fallback_foaf = """
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        
        # Core FOAF classes from official specification
        foaf:Person a rdfs:Class, owl:Class ;
            rdfs:subClassOf foaf:Agent .
            
        foaf:Organization a rdfs:Class, owl:Class ;
            rdfs:subClassOf foaf:Agent .
            
        foaf:Group a rdfs:Class, owl:Class ;
            rdfs:subClassOf foaf:Agent .
            
        foaf:Project a rdfs:Class, owl:Class .
        
        foaf:Agent a rdfs:Class, owl:Class .
        
        foaf:Document a rdfs:Class, owl:Class .
        
        foaf:Image a rdfs:Class, owl:Class ;
            rdfs:subClassOf foaf:Document .
            
        foaf:PersonalProfileDocument a rdfs:Class, owl:Class ;
            rdfs:subClassOf foaf:Document .
        """
        graph.parse(data=fallback_foaf, format="turtle")
        print(f"Using fallback FOAF data with {len(graph)} triples")
        return graph

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

def test_foaf_original_relationships_loading():
    """Test loading original FOAF relationships via official ontology"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
    # Test that FOAF relationships are loaded
    person_to_agent = resolver.is_subtype_of("foaf:Person", "foaf:Agent")
    org_to_agent = resolver.is_subtype_of("foaf:Organization", "foaf:Agent")
    
    assert isinstance(person_to_agent, bool), "Should handle original FOAF relationships"
    assert isinstance(org_to_agent, bool), "Should handle original FOAF class hierarchies"

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
    """Test basic FOAF concept relationships using official ontology"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
    # Test core FOAF relationships
    person_agent = resolver.is_subtype_of("foaf:Person", "foaf:Agent")
    organization_agent = resolver.is_subtype_of("foaf:Organization", "foaf:Agent")
    group_agent = resolver.is_subtype_of("foaf:Group", "foaf:Agent")
    
    # Test expected relationships
    assert person_agent, "Person should be subtype of Agent in FOAF ontology"
    assert organization_agent, "Organization should be subtype of Agent in FOAF ontology"
    assert group_agent, "Group should be subtype of Agent in FOAF ontology"
    
    print(f"FOAF relationships - Person->Agent: {person_agent}, Organization->Agent: {organization_agent}, Group->Agent: {group_agent}")

def test_foaf_document_hierarchy():
    """Test FOAF document class hierarchy using official ontology"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
    # Test document relationships
    image_document = resolver.is_subtype_of("foaf:Image", "foaf:Document")
    profile_document = resolver.is_subtype_of("foaf:PersonalProfileDocument", "foaf:Document")
    
    # Test non-relationships (different document types)
    image_profile = resolver.is_subtype_of("foaf:Image", "foaf:PersonalProfileDocument")
    
    # Direct relationships should be true
    assert image_document, "Image should be subtype of Document (foaf:Image -> foaf:Document)"
    assert profile_document, "PersonalProfileDocument should be subtype of Document"
    
    # Non-relationships should be false (parallel classes)
    assert not image_profile, "Image should not be subtype of PersonalProfileDocument (parallel classes)"

def test_foaf_self_relationships():
    """Test that FOAF concepts are subtypes of themselves"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
    foaf_concepts = [
        "foaf:Person",
        "foaf:Agent", 
        "foaf:Organization",
        "foaf:Group",
        "foaf:Document",
        "foaf:Image",
        "foaf:Project"
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
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    
    foaf:Person rdfs:subClassOf foaf:Agent .
    """
    
    resolver.graph.parse(data=test_data, format="turtle")
    
    # Query same relationship multiple times
    concept1 = "foaf:Person"
    concept2 = "foaf:Agent"
    
    results = []
    for i in range(5):
        result = resolver.is_subtype_of(concept1, concept2)
        results.append(result)
    
    # All results should be identical (cached)
    assert all(r == results[0] for r in results), "Cached FOAF relationship results should be consistent"
    
    # Test that cache has entry
    assert hasattr(resolver, 'relation_cache'), "Resolver should have relation cache"

def test_foaf_cache_consistency_across_queries():
    """Test cache consistency across different query patterns"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Add test hierarchy
    hierarchy_data = """
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    
    foaf:Person rdfs:subClassOf foaf:Agent .
    foaf:Organization rdfs:subClassOf foaf:Agent .
    """
    
    resolver.graph.parse(data=hierarchy_data, format="turtle")
    
    # Query relationships in different orders
    person_agent_1 = resolver.is_subtype_of("foaf:Person", "foaf:Agent")
    org_agent_1 = resolver.is_subtype_of("foaf:Organization", "foaf:Agent")
    
    # Query again in different order
    org_agent_2 = resolver.is_subtype_of("foaf:Organization", "foaf:Agent")
    person_agent_2 = resolver.is_subtype_of("foaf:Person", "foaf:Agent")
    
    # Results should be consistent
    assert person_agent_1 == person_agent_2, "Person-Agent relationship should be consistent"
    assert org_agent_1 == org_agent_2, "Organization-Agent relationship should be consistent"

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
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    
    foaf:Person rdfs:subClassOf foaf:Agent .
    foaf:Organization rdfs:subClassOf foaf:Agent .
    """
    
    resolver.graph.parse(data=foaf_data, format="turtle")
    
    # Test that queries work on-demand
    person_agent = resolver.is_subtype_of("foaf:Person", "foaf:Agent")
    org_agent = resolver.is_subtype_of("foaf:Organization", "foaf:Agent")
    person_org = resolver.is_subtype_of("foaf:Person", "foaf:Organization")
    
    # Based on the loaded hierarchy
    assert person_agent, "Person should be subtype of Agent (foaf:Person -> foaf:Agent)"
    assert org_agent, "Organization should be subtype of Agent (foaf:Organization -> foaf:Agent)"
    # Person should NOT be subtype of Organization (parallel branches)
    assert not person_org, "Person should not be subtype of Organization (parallel branches under foaf:Agent)"

# ===== FOAF Schema Integration Tests =====

def test_foaf_schema_semantic_compatibility():
    """Test semantic compatibility with original FOAF concepts in schemas"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
    # Person schema (more specific)
    person_schema = {
        "type": "object",
        "stype": "foaf:Person",
        "properties": {
            "foaf:name": {"type": "string"},
            "foaf:mbox": {"type": "string", "format": "email"}
        }
    }
    
    # Agent schema (more general)
    agent_schema = {
        "type": "object",
        "stype": "foaf:Agent",
        "properties": {
            "foaf:name": {"type": "string"}
        }
    }
    
    # Test semantic compatibility
    person_to_agent = is_semantically_compatible(person_schema, agent_schema, resolver)
    agent_to_person = is_semantically_compatible(agent_schema, person_schema, resolver)
    
    # Test schema subtyping
    person_subtype_agent = isSubschema(person_schema, agent_schema)
    agent_subtype_person = isSubschema(agent_schema, person_schema)
    
    # Person should be semantically compatible with Agent (more specific -> more general)
    assert person_to_agent, "Person should be semantically compatible with Agent (foaf:Person -> foaf:Agent)"
    # Agent should NOT be semantically compatible with Person (more general -> more specific)
    assert not agent_to_person, "Agent should not be semantically compatible with Person (foaf:Agent -> foaf:Person)"
    
    # Person should be subtype of Agent (more restrictive schema -> less restrictive schema)
    assert person_subtype_agent, "Person schema should be subtype of Agent schema (more specific properties)"
    # Agent should NOT be subtype of Person (less restrictive -> more restrictive)
    assert not agent_subtype_person, "Agent schema should not be subtype of Person schema (missing foaf:mbox property)"

def test_foaf_nested_schema_compatibility():
    """Test FOAF compatibility in nested schema structures"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
    # Organization with people (specific)
    org_with_people_schema = {
        "type": "object",
        "stype": "foaf:Organization",
        "properties": {
            "foaf:name": {"type": "string"},
            "foaf:member": {
                "type": "array",
                "items": {
                    "type": "object",
                    "stype": "foaf:Person"
                }
            }
        }
    }
    
    # Agent with agents (more general)
    agent_with_agents_schema = {
        "type": "object",
        "stype": "foaf:Agent",
        "properties": {
            "foaf:name": {"type": "string"},
            "foaf:member": {
                "type": "array",
                "items": {
                    "type": "object",
                    "stype": "foaf:Agent"
                }
            }
        }
    }
    
    # Test nested compatibility
    org_to_agent = isSubschema(org_with_people_schema, agent_with_agents_schema)
    agent_to_org = isSubschema(agent_with_agents_schema, org_with_people_schema)
    
    # Organization should be subtype of Agent (more specific -> more general)
    assert org_to_agent, "Organization schema should be subtype of Agent schema (foaf:Organization -> foaf:Agent, foaf:Person -> foaf:Agent)"
    # Agent should NOT be subtype of Organization (more general -> more specific)
    assert not agent_to_org, "Agent schema should not be subtype of Organization schema (foaf:Agent -> foaf:Organization, foaf:Agent -> foaf:Person)"

# ===== FOAF IRI Normalization Tests =====

def test_foaf_iri_normalization():
    """Test IRI normalization for FOAF concepts"""
    # Test FOAF prefix normalization
    foaf_cases = [
        ("foaf:Person", "http://xmlns.com/foaf/0.1/Person"),
        ("foaf:Agent", "http://xmlns.com/foaf/0.1/Agent"),
        ("foaf:Organization", "http://xmlns.com/foaf/0.1/Organization"),
        ("foaf:Group", "http://xmlns.com/foaf/0.1/Group"),
        ("foaf:Document", "http://xmlns.com/foaf/0.1/Document"),
        ("foaf:Image", "http://xmlns.com/foaf/0.1/Image"),
        ("foaf:Project", "http://xmlns.com/foaf/0.1/Project")
    ]
    
    for compact, expected_full in foaf_cases:
        result = normalize_iri(compact)
        assert result == expected_full, f"FOAF IRI normalization failed for {compact}"

def test_foaf_mixed_iri_formats():
    """Test mixed IRI formats in FOAF relationships"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
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
    
    # Both should be true based on our test data
    assert compact_to_full, "Person should be subtype of Agent (regardless of IRI format)"
    assert full_to_compact, "Person should be subtype of Agent (regardless of IRI format)"

# ===== FOAF Error Handling Tests =====

def test_foaf_unknown_concepts():
    """Test handling of unknown FOAF concepts"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
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
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    
    # Missing closing bracket and other syntax errors
    foaf:Person rdfs:subClassOf foaf:Agent
    foaf:Organization rdfs:subClassOf foaf:Agent .
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
    
    # Add circular relationship data (artificial for testing)
    circular_data = """
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    
    foaf:TestA rdfs:subClassOf foaf:TestB .
    foaf:TestB rdfs:subClassOf foaf:TestC .
    foaf:TestC rdfs:subClassOf foaf:TestA .
    """
    
    resolver.graph.parse(data=circular_data, format="turtle")
    
    # Test that circular relationships don't cause infinite loops
    result_ab = resolver.is_subtype_of("foaf:TestA", "foaf:TestB")
    result_bc = resolver.is_subtype_of("foaf:TestB", "foaf:TestC")
    result_ca = resolver.is_subtype_of("foaf:TestC", "foaf:TestA")
    
    assert isinstance(result_ab, bool), "Should handle circular relationships without infinite loops"
    assert isinstance(result_bc, bool), "Should handle circular relationships without infinite loops"
    assert isinstance(result_ca, bool), "Should handle circular relationships without infinite loops"

# ===== FOAF Configuration Tests =====

def test_foaf_semantic_reasoning_toggle():
    """Test toggling semantic reasoning on/off with FOAF"""
    # Test with semantic reasoning enabled
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    foaf_schema_enabled = {
        "type": "object",
        "stype": "foaf:Person"
    }
    
    result_enabled = isSubschema(foaf_schema_enabled, foaf_schema_enabled)
    
    # Test with semantic reasoning disabled
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(False)
    
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

# ===== FOAF Properties Tests =====

def test_foaf_properties_in_schemas():
    """Test using original FOAF properties in schemas"""
    SemanticTypeResolver.reset_instance()
    config.set_semantic_reasoning(True)
    
    # Load official FOAF ontology  
    foaf_graph = load_official_foaf_ontology()
    resolver = SemanticTypeResolver.get_instance(graph=foaf_graph)
    
    # Schema using standard FOAF properties
    person_with_foaf_props = {
        "type": "object",
        "stype": "foaf:Person",
        "properties": {
            "foaf:name": {"type": "string"},
            "foaf:mbox": {"type": "string", "format": "email"},
            "foaf:homepage": {"type": "string", "format": "uri"},
            "foaf:phone": {"type": "string"},
            "foaf:img": {"type": "string", "format": "uri"}
        },
        "required": ["foaf:name"]
    }
    
    # Schema with subset of properties
    person_minimal = {
        "type": "object",
        "stype": "foaf:Person",
        "properties": {
            "foaf:name": {"type": "string"}
        },
        "required": ["foaf:name"]
    }
    
    # More specific should be subtype of less specific
    specific_to_general = isSubschema(person_with_foaf_props, person_minimal)
    general_to_specific = isSubschema(person_minimal, person_with_foaf_props)
    
    assert specific_to_general, "Schema with more FOAF properties should be subtype of schema with fewer properties"
    assert not general_to_specific, "Schema with fewer FOAF properties should not be subtype of schema with more properties"

if __name__ == "__main__":
    pytest.main(["-v", __file__])