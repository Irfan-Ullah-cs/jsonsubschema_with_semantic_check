'''
Created on June 24, 2019
@author: Andrew Habib
'''

import sys
import jsonref
from jsonsubschema.semantic_type import is_semantically_compatible, SemanticTypeResolver
from jsonsubschema._canonicalization import (
    canonicalize_schema,
    simplify_schema_and_embed_checkers
)
from jsonsubschema._utils import (
    validate_schema,
    print_db
)

from jsonsubschema.exceptions import UnsupportedRecursiveRef

def debug_subschema_check(s1, s2):
    """Debug function to print schema details before checking subtyping."""
    _s1, _s2 = prepare_operands(s1, s2)
    
    print("LHS schema:", s1)
    print("RHS schema:", s2)
    print("LHS canonicalized:", _s1)
    print("RHS canonicalized:", _s2)
    print("LHS has stype:", "stype" in s1)
    print("RHS has stype:", "stype" in s2)
    print("LHS stype value:", s1.get("stype"))
    print("RHS stype value:", s2.get("stype"))
    
    # Check semantic compatibility first
    resolver = SemanticTypeResolver.get_instance()
    semantic_compatible = is_semantically_compatible(s1, s2, resolver)
    print("Semantic compatibility:", semantic_compatible)
    
    if not semantic_compatible:
        print("Schemas are semantically incompatible")
        return False
    
    result = _s1.isSubtype(_s2)
    print("Structural subtype result:", result)
    return result

def prepare_operands(s1, s2):
    # First, we load schemas using jsonref to resolve $ref
    # before starting canonicalization.

    # s1 = jsonref.loads(json.dumps(s1))
    # s2 = jsonref.loads(json.dumps(s2))
    # This is not very efficient, should be done lazily maybe?
    s1 = jsonref.JsonRef.replace_refs(s1)
    s2 = jsonref.JsonRef.replace_refs(s2)

    # Canonicalize and embed checkers for both lhs
    # and rhs schemas  before starting the subtype checking.
    # This also validates input schemas and canonicalized schemas.

    # At the moment, recursive/circual refs are not supported and hence, canonicalization
    # throws a RecursionError.
    try:
        _s1 = simplify_schema_and_embed_checkers(
            canonicalize_schema(s1))
    except RecursionError:
        # avoid cluttering output by unchaining the recursion error
        raise UnsupportedRecursiveRef(s1, 'LHS') from None

    try:
        _s2 = simplify_schema_and_embed_checkers(
            canonicalize_schema(s2))
    except RecursionError:
        # avoid cluttering output by unchaining the recursion error
        raise UnsupportedRecursiveRef(s2, 'RHS') from None

    return _s1, _s2


def isSubschema(s1, s2):
    """
    Check if s1 is a subschema of s2.
    This includes both semantic and structural compatibility checking.
    """
    import jsonsubschema.config as config
    
    # First check semantic compatibility if enabled
    if config.SEMANTIC_REASONING_ENABLED:
        resolver = SemanticTypeResolver.get_instance()
        if not is_semantically_compatible(s1, s2, resolver):
            print_db("Schemas are semantically incompatible")
            return False
    
    # If semantically compatible (or semantic checking disabled), proceed with structural check
    s1_canonical, s2_canonical = prepare_operands(s1, s2)
    return s1_canonical.isSubtype(s2_canonical)


def meet(s1, s2):
    """
    Entry point for schema meet operation.
    Returns the most restrictive schema that accepts instances valid for both s1 and s2.
    """
    import jsonsubschema.config as config
    
    # Check semantic compatibility if enabled
    if config.SEMANTIC_REASONING_ENABLED:
        resolver = SemanticTypeResolver.get_instance()
        if not is_semantically_compatible(s1, s2, resolver):
            print_db("Schemas are semantically incompatible - returning bottom")
            return {"not": {}}
    
    # Extract semantic types before operations
    s1_stype = s1.get('stype')
    s2_stype = s2.get('stype')
    
    # Determine which semantic type to use for the result
    result_stype = None
    if config.SEMANTIC_REASONING_ENABLED and (s1_stype or s2_stype):
        result_stype = _determine_meet_semantic_type(s1_stype, s2_stype)
    
    # Perform structural operation
    s1_canonical, s2_canonical = prepare_operands(s1, s2)
    result = s1_canonical.meet(s2_canonical)
    
    # Apply semantic type if needed
    if result_stype is not None:
        result_dict = dict(result)
        result_dict['stype'] = result_stype
        return result_dict
    
    return result


def join(s1, s2):
    """
    Entry point for schema join operation.
    Returns the most permissive schema that accepts instances valid for either s1 or s2.
    """
    import jsonsubschema.config as config
    
    # Extract semantic types before operations
    s1_stype = s1.get('stype')
    s2_stype = s2.get('stype')
    
    # Determine which semantic type to use for the result
    result_stype = None
    if config.SEMANTIC_REASONING_ENABLED and (s1_stype or s2_stype):
        result_stype = _determine_join_semantic_type(s1_stype, s2_stype)
    
    # Prepare operands
    s1_canonical, s2_canonical = prepare_operands(s1, s2)
    
    try:
        # Perform structural operation
        result = s1_canonical.join(s2_canonical)
        
        # Apply semantic type if needed
        if result_stype is not None:
            result_dict = dict(result)
            result_dict['stype'] = result_stype
            return result_dict
        
        return result
        
    except ValueError as e:
        # Handle numeric join error case
        if "The truth value of a bound is ambiguous" in str(e) and all(s.get('type') == 'number' for s in [s1_canonical, s2_canonical]):
            # Create manual result for numeric types
            manual_result = {
                'type': 'number',
                'minimum': min(s1_canonical.get('minimum', float('-inf')), s2_canonical.get('minimum', float('-inf'))),
                'maximum': max(s1_canonical.get('maximum', float('inf')), s2_canonical.get('maximum', float('inf')))
            }
            
            if result_stype is not None:
                manual_result['stype'] = result_stype
                
            return manual_result
                
        # Re-raise other errors
        raise

    
def isEquivalent(s1, s2):
    """
    Entry point for schema equivalence check operation.
    Two schemas are equivalent if they accept exactly the same set of instances.
    """
    import jsonsubschema.config as config
    
    # Check semantic compatibility if enabled
    if config.SEMANTIC_REASONING_ENABLED:
        resolver = SemanticTypeResolver.get_instance()
        if not is_semantically_compatible(s1, s2, resolver) or not is_semantically_compatible(s2, s1, resolver):
            return False
        
        # Additionally, for equivalence, semantic types must be equivalent
        s1_stype = s1.get('stype')
        s2_stype = s2.get('stype')
        
        # Both must have same semantic type presence
        if (s1_stype is None) != (s2_stype is None):
            return False
            
        # If both have semantic types, they must be equivalent
        if s1_stype is not None and s2_stype is not None:
            if not (resolver.is_subtype_of(s1_stype, s2_stype) and resolver.is_subtype_of(s2_stype, s1_stype)):
                return False
    
    # Check structural equivalence
    return isSubschema(s1, s2) and isSubschema(s2, s1)


def _determine_meet_semantic_type(s1_stype, s2_stype):
    """
    Determine the semantic type for a meet operation result.
    For meet, we want the more specific (narrower) type.
    """
    if s1_stype == s2_stype:
        return s1_stype
    
    if s1_stype is None:
        return s2_stype
    if s2_stype is None:
        return s1_stype
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Return the more specific type
    if resolver.is_subtype_of(s1_stype, s2_stype):
        return s1_stype  # s1 is more specific
    elif resolver.is_subtype_of(s2_stype, s1_stype):
        return s2_stype  # s2 is more specific
    else:
        # Types are incompatible - this should have been caught earlier
        print_db(f"Warning: Incompatible semantic types in meet: {s1_stype}, {s2_stype}")
        return None


def _determine_join_semantic_type(s1_stype, s2_stype):
    """
    Determine the semantic type for a join operation result.
    For join, we want the more general (broader) type.
    """
    if s1_stype == s2_stype:
        return s1_stype
    
    if s1_stype is None or s2_stype is None:
        # If one doesn't have a semantic type, the join shouldn't have one either
        return None
    
    resolver = SemanticTypeResolver.get_instance()
    
    # Return the more general type
    if resolver.is_subtype_of(s1_stype, s2_stype):
        return s2_stype  # s2 is more general
    elif resolver.is_subtype_of(s2_stype, s1_stype):
        return s1_stype  # s1 is more general
    else:
        # Types are incompatible - result shouldn't have a semantic type
        print_db(f"Warning: Incompatible semantic types in join: {s1_stype}, {s2_stype}")
        return None