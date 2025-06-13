'''
Created on May 1, 2025
Semantic type checking extension for jsonsubschema with SKOS hierarchy support
'''

import rdflib
from rdflib.namespace import SKOS
from urllib.parse import urlparse
import jsonsubschema.config as config


class SemanticTypeResolver:
    """Class responsible for resolving semantic type IRIs and checking hierarchical relationships"""
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of the resolver"""
        if cls._instance is None:
            cls._instance = SemanticTypeResolver()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None
    
    def __init__(self, graph_urls=None):
        """Initialize the resolver with optional graph URLs"""
        self.graph = rdflib.Graph()
        # Bind common prefixes
        self.graph.bind('quantitykind', rdflib.Namespace('http://qudt.org/vocab/quantitykind/'))
        self.graph.bind('qudt', rdflib.Namespace('http://qudt.org/schema/qudt/'))
        self.graph.bind('skos', SKOS)
        self.graph.bind('foaf', rdflib.Namespace('http://xmlns.com/foaf/0.1/'))
        
        self.relation_cache = {}  # Cache for subtype relation checks
        self.supports_transitive_queries = None  # Will be tested on first use
        
        # Only load graphs if semantic reasoning is enabled
        if config.SEMANTIC_REASONING_ENABLED:
            self._load_default_graphs()
            self._load_additional_graphs(graph_urls)
    
    def _load_default_graphs(self):
        """Load default semantic graphs"""
        print("Loading default QUDT quantity kinds graph (this may take a moment)...")
        try:
            self.graph.parse("https://qudt.org/vocab/quantitykind/")
            print(f"Loaded {len(self.graph)} triples from QUDT quantity kinds")
        except Exception as e:
            print(f"Warning: Error loading QUDT graph: {e}")
            print("Continuing without QUDT quantity kinds")
    
    def _load_additional_graphs(self, graph_urls):
        """Load additional graphs from URLs or cache"""
        if not graph_urls:
            graph_urls = config.SEMANTIC_GRAPH_URLS
            
        for url in graph_urls:
            try:
                print(f"Loading graph from {url}")
                self.graph.parse(url)
                print(f"Successfully loaded graph from {url}")
            except Exception as e:
                print(f"Warning: Error loading graph from {url}: {e}")
    
    def _test_transitive_support(self):
        """Test if the RDF store supports transitive property path queries"""
        if self.supports_transitive_queries is not None:
            return self.supports_transitive_queries
            
        try:
            # Simple test query with property path
            test_query = """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            ASK { 
                ?x skos:broader* ?y .
            }
            LIMIT 1
            """
            self.graph.query(test_query)
            self.supports_transitive_queries = True
            print("RDF store supports transitive property path queries")
        except Exception as e:
            self.supports_transitive_queries = False
            print(f"RDF store does not support transitive queries: {e}")
            print("Falling back to manual traversal")
            
        return self.supports_transitive_queries
    
    def is_subtype_of(self, narrower_iri, broader_iri):
        """
        Check if narrower_iri is a subtype of broader_iri using SKOS broader relationship.
        Returns True if narrower_iri is the same as or narrower than broader_iri.
        """
        # Skip semantic checking if disabled
        if not config.SEMANTIC_REASONING_ENABLED:
            return narrower_iri == broader_iri
            
        # Normalize IRIs
        narrower_iri = normalize_iri(narrower_iri)
        broader_iri = normalize_iri(broader_iri)
        
        print(f"Checking if {narrower_iri} is a subtype of {broader_iri}")
        
        # Check cache first
        cache_key = (narrower_iri, broader_iri)
        if cache_key in self.relation_cache:
            return self.relation_cache[cache_key]
        
        # If they're the same IRI, return True
        if narrower_iri == broader_iri:
            self.relation_cache[cache_key] = True
            return True
        
        # Try the appropriate method based on RDF store capabilities
        if self._test_transitive_support():
            result = self._check_with_transitive_query(narrower_iri, broader_iri)
        else:
            result = self._check_with_manual_traversal(narrower_iri, broader_iri)
            
        # Cache and return result
        self.relation_cache[cache_key] = result
        return result
    
    def _check_with_transitive_query(self, narrower_iri, broader_iri):
        """Use SPARQL transitive query with property paths"""
        try:
            # Use transitive query with Kleene star to check direct OR transitive relationship
            transitive_query = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            ASK {{ 
                <{narrower_iri}> skos:broader* <{broader_iri}> .
            }}
            """
            result = bool(self.graph.query(transitive_query))
            print(f"Transitive query result: {result}")
            return result
            
        except Exception as e:
            print(f"Error during transitive query: {e}")
            # Fall back to manual traversal
            return self._check_with_manual_traversal(narrower_iri, broader_iri)
    
    def _check_with_manual_traversal(self, narrower_iri, broader_iri):
        """Fallback manual traversal for when SPARQL transitive queries fail"""
        narrower_ref = rdflib.URIRef(narrower_iri)
        broader_ref = rdflib.URIRef(broader_iri)
        
        visited = set()
        to_check = [narrower_ref]
        broader_prop = rdflib.URIRef("http://www.w3.org/2004/02/skos/core#broader")
        
        while to_check:
            current = to_check.pop(0)
            if current in visited:
                continue
                
            visited.add(current)
            
            for obj in self.graph.objects(current, broader_prop):
                if obj == broader_ref:
                    print(f"Manual traversal found path: {narrower_iri} -> {broader_iri}")
                    return True
                to_check.append(obj)
        
        print(f"No path found between {narrower_iri} and {broader_iri}")
        return False
    
    def add_test_relationship(self, narrower_iri, broader_iri):
        """Add a test relationship to the graph (useful for testing)"""
        narrower_ref = rdflib.URIRef(normalize_iri(narrower_iri))
        broader_ref = rdflib.URIRef(normalize_iri(broader_iri))
        broader_prop = rdflib.URIRef("http://www.w3.org/2004/02/skos/core#broader")
        
        self.graph.add((narrower_ref, broader_prop, broader_ref))
        print(f"Added test relationship: {narrower_iri} skos:broader {broader_iri}")
        
        # Clear cache to ensure fresh results
        self.relation_cache.clear()










def normalize_iri(stype_value):
    """
    Normalize semantic type values to full IRIs.
    - Handles compact notation (e.g., 'quantitykind:Temperature')
    - Expands known prefixes
    - Returns the full IRI
    """
    if not stype_value:
        return stype_value
        
    # If it's already a full URI, just return it
    if stype_value.startswith('http://') or stype_value.startswith('https://'):
        return stype_value
        
    # Known prefixes
    prefixes = {
        "quantitykind": "http://qudt.org/vocab/quantitykind/",
        "qudt": "http://qudt.org/schema/qudt/",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "ex": "http://example.org/",  # Added for testing
        "foaf": "http://xmlns.com/foaf/0.1/"
    }
    
    # Handle compact notation (prefix:local)
    if ":" in stype_value:
        parts = stype_value.split(":", 1)
        if len(parts) == 2:
            prefix, local = parts
            if prefix in prefixes:
                full_iri = f"{prefixes[prefix]}{local}"
                return full_iri
    
    # If we can't expand it, return the original
    return stype_value








def is_semantically_compatible(s1, s2, resolver=None):
    '''
    Check if two schemas are semantically compatible, including deeply nested structures.
    Returns True if s1 can be considered a semantic subtype of s2.
    '''
    # Skip semantic checking if disabled
    import jsonsubschema.config as config
    if not config.SEMANTIC_REASONING_ENABLED:
        return True
    
    # Get the resolver instance if not provided
    if resolver is None:
        resolver = SemanticTypeResolver.get_instance()
    
    # Check root level semantic types
    if not _check_semantic_types_compatible(s1, s2, resolver):
        return False
    
    # Recursively check nested structures
    return _check_nested_semantic_compatibility(s1, s2, resolver)


def _check_semantic_types_compatible(s1, s2, resolver):
    """Check if the semantic types at the current level are compatible"""
    s1_stype = s1.get('stype')
    s2_stype = s2.get('stype')
    
    # If neither has semantic types, they're compatible at this level
    if s1_stype is None and s2_stype is None:
        return True
    
    # If s1 has stype but s2 doesn't, s1 is more specific than s2 (compatible)
    if s1_stype is not None and s2_stype is None:
        return True  # s1 (more specific) is subtype of s2 (more general)
    
    # If s1 doesn't have stype but s2 does, s1 is more general than s2 (incompatible)
    if s1_stype is None and s2_stype is not None:
        print(f"Semantic incompatibility: s1 has no stype but s2 requires {s2_stype}")
        return False
    
    # Both have semantic types - check if s1_stype is subtype of s2_stype
    compatible = resolver.is_subtype_of(s1_stype, s2_stype)
    if not compatible:
        print(f"Semantic incompatibility: {s1_stype} is not a subtype of {s2_stype}")
    return compatible


def _check_nested_semantic_compatibility(s1, s2, resolver):
    """Recursively check semantic compatibility in nested structures"""
    
    # Check object properties
    if not _check_object_properties_semantic_compatibility(s1, s2, resolver):
        return False
    
    # Check array items
    if not _check_array_items_semantic_compatibility(s1, s2, resolver):
        return False
    
    # Check additionalProperties for objects
    if not _check_additional_properties_semantic_compatibility(s1, s2, resolver):
        return False
    
    # Check pattern properties for objects
    if not _check_pattern_properties_semantic_compatibility(s1, s2, resolver):
        return False
    
    # Check allOf, anyOf, oneOf recursively
    if not _check_boolean_connectives_semantic_compatibility(s1, s2, resolver):
        return False
    
    return True


def _check_object_properties_semantic_compatibility(s1, s2, resolver):
    """Check semantic compatibility of object properties"""
    s1_props = s1.get('properties', {})
    s2_props = s2.get('properties', {})
    
    # For properties that exist in both schemas, check semantic compatibility
    common_props = set(s1_props.keys()) & set(s2_props.keys())
    for prop in common_props:
        if not is_semantically_compatible(s1_props[prop], s2_props[prop], resolver):
            print(f"Semantic incompatibility in property '{prop}'")
            return False
    
    return True



def _check_array_items_semantic_compatibility(s1, s2, resolver):
    """Check semantic compatibility of array items"""
    s1_items = s1.get('items')
    s2_items = s2.get('items')
    
    if s1_items and s2_items:
        # If items are schema objects (the most common case)
        if isinstance(s1_items, dict) and isinstance(s2_items, dict):
            if not is_semantically_compatible(s1_items, s2_items, resolver):
                print("Semantic incompatibility in array items")
                return False
        
        # If items are arrays of schemas (tuple validation)
        elif isinstance(s1_items, list) and isinstance(s2_items, list):
            # Check each position
            for i, (i1, i2) in enumerate(zip(s1_items, s2_items)):
                if not is_semantically_compatible(i1, i2, resolver):
                    print(f"Semantic incompatibility in array items at position {i}")
                    return False
        
        # Mixed types (one dict, one list) - only incompatible if semantic types involved
        elif (isinstance(s1_items, dict) and isinstance(s2_items, list)) or \
             (isinstance(s1_items, list) and isinstance(s2_items, dict)):
            
            # Check if semantic types are actually involved
            s1_has_stype = _has_semantic_types_in_items(s1_items)
            s2_has_stype = _has_semantic_types_in_items(s2_items)
            
            if s1_has_stype or s2_has_stype:
                print("Semantic incompatibility: mixed array item types with semantic constraints")
                return False
            # If no semantic types, let structural validation handle it
    
    return True

def _has_semantic_types_in_items(items):
    """Check if items schema(s) contain semantic types"""
    if isinstance(items, dict):
        return 'stype' in items or any('stype' in v for v in items.values() if isinstance(v, dict))
    elif isinstance(items, list):
        return any('stype' in item for item in items if isinstance(item, dict))
    return False

def _check_additional_properties_semantic_compatibility(s1, s2, resolver):
    """Check semantic compatibility of additionalProperties"""
    s1_additional = s1.get('additionalProperties')
    s2_additional = s2.get('additionalProperties')
    
    # If both have additionalProperties schemas
    if (isinstance(s1_additional, dict) and isinstance(s2_additional, dict)):
        if not is_semantically_compatible(s1_additional, s2_additional, resolver):
            print("Semantic incompatibility in additionalProperties")
            return False
    
    return True


def _check_pattern_properties_semantic_compatibility(s1, s2, resolver):
    """Check semantic compatibility of patternProperties"""
    s1_pattern_props = s1.get('patternProperties', {})
    s2_pattern_props = s2.get('patternProperties', {})
    
    # For now, check pattern properties with exact pattern matches
    # More sophisticated regex pattern matching could be added later
    common_patterns = set(s1_pattern_props.keys()) & set(s2_pattern_props.keys())
    for pattern in common_patterns:
        if not is_semantically_compatible(s1_pattern_props[pattern], s2_pattern_props[pattern], resolver):
            print(f"Semantic incompatibility in patternProperty '{pattern}'")
            return False
    
    return True


def _check_boolean_connectives_semantic_compatibility(s1, s2, resolver):
    """Check semantic compatibility in boolean connectives (allOf, anyOf, oneOf)"""
    
    # Check allOf
    s1_all_of = s1.get('allOf', [])
    s2_all_of = s2.get('allOf', [])
    
    if s1_all_of and s2_all_of:
        # Each schema in s1's allOf should be compatible with at least one in s2's allOf
        for s1_schema in s1_all_of:
            if not any(is_semantically_compatible(s1_schema, s2_schema, resolver) 
                      for s2_schema in s2_all_of):
                print("Semantic incompatibility in allOf")
                return False
    
    # Check anyOf
    s1_any_of = s1.get('anyOf', [])
    s2_any_of = s2.get('anyOf', [])
    
    if s1_any_of and s2_any_of:
        # At least one schema in s1's anyOf should be compatible with at least one in s2's anyOf
        compatible_found = False
        for s1_schema in s1_any_of:
            if any(is_semantically_compatible(s1_schema, s2_schema, resolver) 
                  for s2_schema in s2_any_of):
                compatible_found = True
                break
        if not compatible_found:
            print("Semantic incompatibility in anyOf")
            return False
    
    # oneOf is more complex and might require special handling
    # For now, treat it similarly to anyOf
    s1_one_of = s1.get('oneOf', [])
    s2_one_of = s2.get('oneOf', [])
    
    if s1_one_of and s2_one_of:
        # At least one schema in s1's oneOf should be compatible with exactly one in s2's oneOf
        for s1_schema in s1_one_of:
            compatible_count = sum(1 for s2_schema in s2_one_of 
                                 if is_semantically_compatible(s1_schema, s2_schema, resolver))
            if compatible_count > 0:
                return True
        print("Semantic incompatibility in oneOf")
        return False
    
    return True