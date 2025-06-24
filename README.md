# jsonsubschema with Semantic Validation

[![CI](https://github.com/IBM/jsonsubschema/actions/workflows/ci.yml/badge.svg)](https://github.com/IBM/jsonsubschema/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**jsonsubschema** checks if one JSON schema is a subschema (subtype) of another, now enhanced with **semantic validation capabilities** through ontological reasoning.

For any two JSON schemas s1 and s2, s1 <: s2 (reads s1 is subschema/subtype of s2) if every JSON document instance that validates against s1 also validates against s2.

## Semantic Validation Extension

This fork extends the original IBM jsonsubschema library with semantic validation capabilities:

- **stype keyword**: Add semantic type annotations to JSON schemas
- **Ontology integration**: QUDT, FOAF, SKOS support with 2,847+ concepts
- **Smart validation**: Considers ontological relationships between types
- **100% backward compatible**: Existing schemas work unchanged
- **Performance optimized**: Multi-level caching and lazy loading

### Quick Example

```python
from jsonsubschema import isSubschema

# Schemas with semantic type annotations
humidity_schema = {
    "type": "number",
    "minimum": 0,
    "maximum": 100,
    "stype": "quantitykind:RelativeHumidity"
}

dimensionless_schema = {
    "type": "number",
    "stype": "quantitykind:DimensionlessRatio"
}

# Enhanced validation considers semantic relationships
result = isSubschema(humidity_schema, dimensionless_schema)
print(f"Is humidity a dimensionless ratio? {result}")  # True
```



## Installation

### Requirements
* Python 3.7+
* Internet connection (for ontology loading)

### Install from Source

```bash
git clone https://github.com/Irfan-Ullah-cs/jsonsubschema_with_semantic_check.git
cd jsonsubschema_with_semantic_check
pip install .
```

### Install from PyPI (when published)

```bash
pip install jsonsubschema-with-semantic
```

### Development Installation

```bash
git clone https://github.com/Irfan-Ullah-cs/jsonsubschema_with_semantic_check.git
cd jsonsubschema_with_semantic_check
pip install -e .
```

### Original Version (IBM)

If you need the original version 

```bash
pip install jsonsubschema
```

Note: Semantic validation features are only available in this fork.

## Usage

### Python API

#### Basic Usage
```python
from jsonsubschema import isSubschema

s1 = {'type': 'integer'}
s2 = {'type': ['integer', 'string']}

print(f'Is s1 a subschema of s2? {isSubschema(s1, s2)}')  # True
```

#### Semantic Validation
```python
from jsonsubschema import isSubschema
from jsonsubschema.semantic_type import SemanticTypeResolver
import jsonsubschema.config as config
import rdflib

# Disable debug output for cleaner results
config.set_debug(False)

# Enable semantic reasoning
config.set_semantic_reasoning(True)

# Set up semantic graph with test relationships
graph = rdflib.Graph()
test_data = """
@prefix quantitykind: <http://qudt.org/vocab/quantitykind/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

quantitykind:ThermodynamicTemperature skos:broader quantitykind:Temperature .
"""
graph.parse(data=test_data, format="turtle")

# Initialize resolver with the graph (suppress internal prints)
resolver = SemanticTypeResolver.get_instance(graph=graph)

# Schemas with semantic annotations
thermodynamic_temp_schema = {
    "type": "number",
    "minimum": 0,
    "stype": "quantitykind:ThermodynamicTemperature"  # More specific
}

temperature_schema = {
    "type": "number", 
    "minimum": -273.15,
    "stype": "quantitykind:Temperature"  # More general
}

# Only your print - semantic validation
is_subtype = isSubschema(thermodynamic_temp_schema, temperature_schema)
print(f"Is thermodynamic temperature a subtype of temperature? {is_subtype}")
```

#### Nested Schemas
```python
# IoT sensor data schema
from jsonsubschema import isSubschema
from jsonsubschema.semantic_type import SemanticTypeResolver
import jsonsubschema.config as config
import rdflib

# Disable debug output for cleaner results
config.set_debug(False)

# Enable semantic reasoning
config.set_semantic_reasoning(True)

# Set up semantic graph with test relationships
graph = rdflib.Graph()
test_data = """
@prefix quantitykind: <http://qudt.org/vocab/quantitykind/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

quantitykind:ThermodynamicTemperature skos:broader quantitykind:Temperature .
"""
graph.parse(data=test_data, format="turtle")

# Initialize resolver with the graph (suppress internal prints)
resolver = SemanticTypeResolver.get_instance(graph=graph)


# IoT sensor data schema
sensor_schema = {
    "type": "object",
    "properties": {
        "temperature": {
            "type": "number",
            "stype": "quantitykind:Temperature"
        },
        "humidity": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "stype": "quantitykind:RelativeHumidity"
        }
    },
    "required": ["temperature"]
}

# Environmental data schema
environmental_schema = {
    "type": "object",
    "properties": {
        "temperature": {
            "type": "number",
            "stype": "quantitykind:ThermodynamicTemperature"
        }
    },
    "required": ["temperature"]
}

# Deep semantic validation
isSubschema(sensor_schema, environmental_schema) #TEmprature is not subType of ThermodynomicTemperature

isSubschema(environmental_schema, sensor_schema) #TEmprature is  subType of ThermodynomicTemperature
```

### CLI Interface

```bash
# Create semantic schemas
echo '{
  "type": "number",
  "stype": "quantitykind:PressureRatio",
  "minimum": 0
}' > PressureRatio.json
```

```bash
echo '{
  "type": "number",
  "stype": "quantitykind:RelativeHumidity",
  "minimum": 0,
  "maximum": 100
}' > RelativeHumidity.json
```
```bash
# Check semantic relationship
python -m jsonsubschema.cli --ontology qudt  .\humidity_schema.json .\pressure_ratio_schema.json
```

## Testing

### Run All Tests
```bash
python -m pytest test/ -v
```

### Run Semantic Tests
```bash
# Basic semantic functionality
python -m pytest test/test_stype_keyword.py -v

# SKOS ontology integration
python -m pytest test/test_stype_with_skos.py -v

# FOAF ontology integration
python -m pytest test/test_foaf_integration.py -v
```

## Supported Ontologies

### QUDT (Quantities, Units, Dimensions, Data Types)
- **Coverage**: 2,847+ scientific measurement concepts
- **Source**: https://qudt.org/vocab/quantitykind/
- **Examples**: `quantitykind:Temperature`, `quantitykind:Pressure`, `quantitykind:RelativeHumidity`

```python
temperature_schema = {"type": "number", "stype": "quantitykind:Temperature"}
pressure_schema = {"type": "number", "stype": "quantitykind:Pressure"}
```

### FOAF (Friend of a Friend)
- **Purpose**: Social and person-related semantic types
- **Source**: http://xmlns.com/foaf/0.1/
- **Examples**: `foaf:Person`, `foaf:Organization`

```python
person_schema = {"type": "object", "stype": "foaf:Person"}
```

### SKOS (Simple Knowledge Organization System)
- **Purpose**: General concept hierarchy framework
- **Relationships**: `skos:broader`, `skos:narrower` with transitive traversal

```python
concept_schema = {"type": "string", "stype": "skos:Concept"}
```


### Optimization Features
- Multi-level caching for validation results and semantic relationships
- Lazy loading of ontology data
- Query optimization with fallback mechanisms
- Efficient SPARQL query generation

## Backward Compatibility

### 100% Compatibility Guarantee
- All existing schemas without `stype` work identically to original library
- No breaking changes to existing API functions
- Performance impact negligible for non-semantic schemas
- Original test suite passes completely

### Migration
Existing code requires no changes. Semantic features are opt-in:

```python
# Existing code works unchanged
result = isSubschema(old_schema1, old_schema2)

# Add semantic features by including stype
semantic_schema = {
    "type": "number",
    "stype": "quantitykind:Temperature"  # Just add this line
}
```

## API Reference

### Enhanced Functions

#### `isSubschema(s1, s2, resolver=None)`
Checks if s1 is a semantic and structural subschema of s2.

**Parameters:**
- `s1`: First JSON schema (candidate subschema)
- `s2`: Second JSON schema (candidate superschema)
- `resolver`: Optional SemanticTypeResolver instance

**Returns:** `bool`

#### `meet(s1, s2, resolver=None)`
Computes the most restrictive schema accepting data from both inputs.

#### `join(s1, s2, resolver=None)`
Computes the most permissive schema accepting data from either input.

#### `isEquivalent(s1, s2, resolver=None)`
Checks semantic and structural equivalence of two schemas.

### Core Classes

#### `SemanticTypeResolver`
Singleton class handling semantic type resolution and ontology queries.

**Key Methods:**
- `is_subtype(type1, type2)`: Check semantic subtype relationship
- `normalize_iri(stype_value)`: Convert compact notation to full IRI
- `load_ontology(ontology_url)`: Load additional ontology sources

## License

jsonsubschema is distributed under the terms of the Apache 2.0 License, see [LICENSE.txt](LICENSE.txt).

## Contributions

We welcome contributions. Contributors are expected to submit a 'Developer's Certificate of Origin', which can be found in [DCO1.1.txt](DCO1.1.txt).


## Acknowledgments

Built on the foundation of IBM's jsonsubschema library (ISSTA 2021 Distinguished Artifact Award). The semantic validation extension adds ontological reasoning capabilities while maintaining 100% backward compatibility.
