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
    def get_instance(cls, graph=None, lazy_load=False):
        """
        Get or create the singleton instance of the resolver
        
        Args:
            graph: Pre-initialized rdflib.Graph with user's definitions
            lazy_load: If True, fetch unknown semantic types on-demand
        """
        # If no instance exists, create one
        if cls._instance is None:
            cls._instance = SemanticTypeResolver(graph=graph, lazy_load=lazy_load)
            return cls._instance
        
        # If instance exists but parameters differ significantly, reset and recreate
        current_graph_id = id(cls._instance.graph) if hasattr(cls._instance, 'graph') else None
        new_graph_id = id(graph) if graph is not None else None
        current_lazy_load = getattr(cls._instance, 'lazy_load', False)
        
        # Reset if different graph provided or lazy_load setting changed
        if (graph is not None and current_graph_id != new_graph_id) or current_lazy_load != lazy_load:
            cls._instance = SemanticTypeResolver(graph=graph, lazy_load=lazy_load)
        
        return cls._instance
        
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None
    
    def __init__(self, graph=None, lazy_load=False):
        """
        Initialize the resolver with optional graph and lazy loading.

        Args:
            graph: Pre-initialized rdflib.Graph with user's definitions
            lazy_load: If True, fetch unknown semantic types on-demand
        """
        self.lazy_load = lazy_load

        # Initialize graph
        if graph is not None:
            self.graph = graph
        else:
            self.graph = rdflib.Graph()
       
       


        # Bind common prefixes
        self.graph.bind('quantitykind', rdflib.Namespace('http://qudt.org/vocab/quantitykind/'))
        self.graph.bind('qudt', rdflib.Namespace('http://qudt.org/schema/qudt/'))
        self.graph.bind('skos', SKOS)
        self.graph.bind('foaf', rdflib.Namespace('http://xmlns.com/foaf/0.1/'))
        
        self.relation_cache = {}  # Cache for subtype relation checks
        self.supports_transitive_queries = None  # Will be tested on first use
        
        self.fetched_namespaces = set()  # Track what namespaces we've already fetched

        print(f"SemanticTypeResolver initialized with {len(self.graph)} triples, lazy_load={lazy_load}")
    


    def _extract_namespace(self, iri):
        """Extract namespace URL from IRI for lazy loading."""
        if '#' in iri:
            return iri.split('#')[0] + '#'
        else:
            parts = iri.rstrip('/').split('/')
            return '/'.join(parts[:-1]) + '/'

    def _type_exists_in_graph(self, uri_ref):
        """Check if a semantic type exists in the graph."""
        return (uri_ref, None, None) in self.graph or (None, None, uri_ref) in self.graph

    def _lazy_load_semantic_type(self, stype_iri):
        """Attempt to fetch and load RDF graph for unknown semantic type."""
        if not self.lazy_load:
            return False
            
        namespace = self._extract_namespace(stype_iri)
        
        if namespace in self.fetched_namespaces:
            return False
            
        try:
            print(f"Lazy loading namespace: {namespace}")
            initial_count = len(self.graph)
            self.graph.parse(namespace)
            final_count = len(self.graph)
            
            print(f"Loaded {final_count - initial_count} triples from {namespace}")
            self.fetched_namespaces.add(namespace)
            self.relation_cache.clear()
            self.supports_transitive_queries = None
            return True
            
        except Exception as e:
            print(f"Failed to lazy load {namespace}: {e}")
            self.fetched_namespaces.add(namespace)
            return False
    

    
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
        
        
        cache_key = (narrower_iri, broader_iri)       

        
        # If they're the same IRI, return True
        if narrower_iri == broader_iri:
            self.relation_cache[cache_key] = True
            return True
        
         # Check cache first

        if cache_key in self.relation_cache:
            return self.relation_cache[cache_key]
        

        print(f"Checking if {narrower_iri} is a subtype of {broader_iri}")

        # Check if types exist in graph, lazy load if needed
        narrower_ref = rdflib.URIRef(narrower_iri)
        broader_ref = rdflib.URIRef(broader_iri)

        if self.lazy_load:
            if not self._type_exists_in_graph(narrower_ref):
                self._lazy_load_semantic_type(narrower_iri)
            if not self._type_exists_in_graph(broader_ref):
                self._lazy_load_semantic_type(broader_iri)



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
            # Updated query to check both skos:broader and rdfs:subClassOf relationships
            transitive_query = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            ASK {{ 
                {{ <{narrower_iri}> skos:broader* <{broader_iri}> . }}
                UNION
                {{ <{narrower_iri}> rdfs:subClassOf* <{broader_iri}> . }}
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
        
        # Check both skos:broader and rdfs:subClassOf relationships
        broader_prop = rdflib.URIRef("http://www.w3.org/2004/02/skos/core#broader")
        subclass_prop = rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
        
        while to_check:
            current = to_check.pop(0)
            if current in visited:
                continue
                
            visited.add(current)
            
            # Check skos:broader relationships
            for obj in self.graph.objects(current, broader_prop):
                if obj == broader_ref:
                    print(f"Manual traversal found path via skos:broader: {narrower_iri} -> {broader_iri}")
                    return True
                to_check.append(obj)
                
            # Check rdfs:subClassOf relationships
            for obj in self.graph.objects(current, subclass_prop):
                if obj == broader_ref:
                    print(f"Manual traversal found path via rdfs:subClassOf: {narrower_iri} -> {broader_iri}")
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