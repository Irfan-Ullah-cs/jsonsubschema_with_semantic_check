'''
Created on June 24, 2019
@author: Andrew Habib
Updated to support semantic ontology loading via CLI parameters
'''

import argparse
import rdflib
from jsonsubschema._utils import load_json_file
from jsonsubschema.api import isSubschema
from jsonsubschema.semantic_type import SemanticTypeResolver


def load_ontology(ontology_name, graph):
    """
    Load a specific ontology into the graph.
    
    Args:
        ontology_name: Name of the ontology to load ('qudt', 'foaf', 'skos')
        graph: rdflib.Graph to load the ontology into
    
    Returns:
        bool: True if loaded successfully, False otherwise
    """
    ontology_urls = {
        'qudt': 'https://qudt.org/vocab/quantitykind/',
        'foaf': 'http://xmlns.com/foaf/0.1/',
        'skos': 'http://www.w3.org/2004/02/skos/core#'
    }
    
    if ontology_name.lower() not in ontology_urls:
        print(f"Error: Unknown ontology '{ontology_name}'. Supported: {list(ontology_urls.keys())}")
        return False
    
    url = ontology_urls[ontology_name.lower()]
    
    try:
        print(f"Loading {ontology_name.upper()} ontology from {url}...")
        initial_count = len(graph)
        graph.parse(url)
        final_count = len(graph)
        print(f"Successfully loaded {final_count - initial_count} triples from {ontology_name.upper()}")
        return True
    except Exception as e:
        print(f"Warning: Could not load {ontology_name.upper()} ontology: {e}")
        return False


def setup_semantic_graph(ontologies, custom_graph_file, lazy_load):
    """
    Setup semantic graph based on user parameters.
    
    Args:
        ontologies: List of ontology names to load
        custom_graph_file: Path to custom RDF file
        lazy_load: Whether to enable lazy loading
    
    Returns:
        rdflib.Graph or None
    """
    if not ontologies and not custom_graph_file:
        # No semantic graphs requested
        return None
    
    graph = rdflib.Graph()
    
    # Load requested ontologies
    if ontologies:
        for ontology in ontologies:
            load_ontology(ontology, graph)
    
    # Load custom graph file
    if custom_graph_file:
        try:
            print(f"Loading custom graph from {custom_graph_file}...")
            initial_count = len(graph)
            graph.parse(custom_graph_file)
            final_count = len(graph)
            print(f"Successfully loaded {final_count - initial_count} triples from custom file")
        except Exception as e:
            print(f"Error: Could not load custom graph file '{custom_graph_file}': {e}")
            return None
    
    return graph if len(graph) > 0 else None


def check_schemas_for_stype(s1, s2):
    """Check if schemas contain stype fields"""
    def has_stype_recursive(schema):
        if isinstance(schema, dict):
            if 'stype' in schema:
                return True
            for key, value in schema.items():
                if key in ['properties', 'items', 'anyOf', 'allOf', 'oneOf']:
                    if isinstance(value, dict) and has_stype_recursive(value):
                        return True
                    elif isinstance(value, list):
                        for item in value:
                            if has_stype_recursive(item):
                                return True
        elif isinstance(schema, list):
            for item in schema:
                if has_stype_recursive(item):
                    return True
        return False
    
    return has_stype_recursive(s1) or has_stype_recursive(s2)


def main():



    """CLI entry point for jsonsubschema with semantic ontology support"""
    
    parser = argparse.ArgumentParser(
        description='CLI for jsonsubschema tool which checks whether a LHS JSON schema is a subschema (<:) of another RHS JSON schema.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic structural validation (no semantic types)
  python -m jsonsubschema.cli schema1.json schema2.json
  
  # With QUDT ontology for scientific measurements
  python -m jsonsubschema.cli --ontology qudt schema1.json schema2.json
  
  # With FOAF ontology for social/person data
  python -m jsonsubschema.cli --ontology foaf schema1.json schema2.json
  
  # With multiple ontologies
  python -m jsonsubschema.cli --ontology qudt --ontology foaf schema1.json schema2.json
  
  # With custom RDF graph file
  python -m jsonsubschema.cli --graph my_ontology.ttl schema1.json schema2.json
  
  # With lazy loading (fetch unknown semantic types on-demand)
  python -m jsonsubschema.cli --ontology qudt --lazy-load schema1.json schema2.json
        """
    )
    
    # Required arguments
    parser.add_argument('LHS', metavar='lhs', type=str, 
                       help='Path to the JSON file which has the LHS JSON schema')
    parser.add_argument('RHS', metavar='rhs', type=str, 
                       help='Path to the JSON file which has the RHS JSON schema')
    
    # Semantic ontology arguments
    parser.add_argument('--ontology', action='append', choices=['qudt', 'foaf', 'skos'],
                       help='Load semantic ontology (can be specified multiple times). Choices: qudt, foaf, skos')
    parser.add_argument('--graph', type=str, 
                       help='Path to custom RDF graph file (Turtle, RDF/XML, N3, etc.)')
    parser.add_argument('--lazy-load', action='store_true',
                       help='Enable lazy loading of unknown semantic types from web')
    
    # Parse arguments
    args = parser.parse_args()
        # Load and validate schemas
    s1 = load_json_file(args.LHS, "LHS file:")
    s2 = load_json_file(args.RHS, "RHS file:")

    # Check if schemas contain stype but no ontology provided
    if check_schemas_for_stype(s1, s2):
        if not args.ontology and not args.graph:
            print("ERROR: Schemas contain semantic types (stype) but no ontology provided!")
            print("       Use --ontology flag to specify an ontology:")
            print("       --ontology foaf    (for FOAF types like foaf:Person)")
            print("       --ontology qudt    (for QUDT types like quantitykind:Temperature)")
            print("       --ontology skos    (for SKOS types)")
            print("       OR use --graph to load custom RDF file")
            print("       OR remove stype fields for structural-only validation")
            return 1
        



        
    # Setup semantic graph based on user preferences
    semantic_graph = setup_semantic_graph(args.ontology, args.graph, args.lazy_load)
    
    

    # Initialize semantic resolver if semantic features are requested
    if semantic_graph is not None or args.lazy_load:
        SemanticTypeResolver.get_instance(graph=semantic_graph, lazy_load=args.lazy_load)
        print(f"Semantic validation enabled with {len(semantic_graph) if semantic_graph else 0} loaded triples")
    else:
        # Don't initialize semantic resolver - this will make semantic validation fall back to structural
        print("Using structural validation only (no semantic types)")
        # Note: We intentionally don't call SemanticTypeResolver.get_instance() here
    
    # Load and validate schemas
    try:
        s1 = load_json_file(args.LHS, "LHS file:")
        s2 = load_json_file(args.RHS, "RHS file:")
    except Exception as e:
        print(f"Error loading schema files: {e}")
        return 1
    
    # Perform subschema check
    try:
        result = isSubschema(s1, s2)
        print("LHS <: RHS", result)
        return 0 if result else 1
    except Exception as e:
        print(f"Error during subschema check: {e}")
        return 1


if __name__ == "__main__":
    exit(main())