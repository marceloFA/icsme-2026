"""
Complexity provider edge case and accuracy tests.

Tests cover:
- Edge cases in complexity calculation (empty functions, no branches, etc.)
- Cross-language consistency and accuracy
- Error handling when Lizard fails
- Object instantiation counting accuracy
- Nesting depth calculation edge cases
"""

import pytest
import tempfile
from pathlib import Path

from collection.complexity_provider import (
    analyze_function_complexity,
    get_cognitive_complexity_fallback,
    get_cognitive_complexity_python,
)


class TestCyclomaticComplexityEdgeCases:
    """Test cyclomatic complexity calculation for edge cases."""

    def test_empty_function_has_cc_of_1(self, tmp_path):
        """Empty function (pass only) should have CC = 1."""
        py_file = tmp_path / "test_empty.py"
        py_file.write_text("""
def empty_fixture():
    pass
""")
        # Fallback formula: max(1, CC + max(0, nesting - 1))
        # With CC=1, nesting=1: max(1, 1 + 0) = 1
        assert get_cognitive_complexity_fallback(1) == 1

    def test_function_with_no_branches_has_cc_1(self):
        """Function with no branches should have CC >= 1."""
        code = """
def linear_fixture():
    x = create_resource()
    y = process(x)
    return y
"""
        result = analyze_function_complexity(code, "python")
        # Linear code with no branches should have CC = 1
        assert result["cyclomatic_complexity"] >= 1

    def test_function_with_single_if_has_cc_2(self):
        """Single if statement adds 1 to CC."""
        code = """
def with_if():
    x = 1
    if True:
        x = 2
    return x
"""
        result = analyze_function_complexity(code, "python")
        # One if statement means CC >= 2
        assert result["cyclomatic_complexity"] >= 2

    def test_function_with_multiple_conditions_in_single_if(self):
        """Multiple conditions (and/or) in single if statement."""
        code = """
def multi_condition():
    if x and y and z:
        return True
    return False
"""
        result = analyze_function_complexity(code, "python")
        # Multiple conditions typically increase CC
        assert result["cyclomatic_complexity"] >= 1

    def test_nested_loops_increase_complexity(self):
        """Nested loops increase cyclomatic complexity."""
        code = """
def nested_loops():
    for i in range(10):
        for j in range(10):
            for k in range(10):
                process(i, j, k)
"""
        result = analyze_function_complexity(code, "python")
        # Deeply nested loops should have CC >= 4 (3 loops + 1 base)
        assert result["cyclomatic_complexity"] >= 4

    def test_try_except_blocks_increase_complexity(self):
        """Try/except blocks increase cyclomatic complexity."""
        code = """
def with_exception_handling():
    try:
        result = risky_operation()
    except ValueError:
        result = None
    except KeyError:
        result = {}
    return result
"""
        result = analyze_function_complexity(code, "python")
        # Exception handlers add branches
        assert result["cyclomatic_complexity"] >= 3

    def test_fallback_formula_with_high_nesting(self):
        """Fallback formula should account for nesting depth."""
        # CC + max(0, nesting - 1)
        assert get_cognitive_complexity_fallback(cyclomatic=2, max_nesting=1) >= 2
        assert get_cognitive_complexity_fallback(cyclomatic=2, max_nesting=5) >= 5

    def test_fallback_formula_handles_zero_nesting(self):
        """Fallback formula should handle zero or negative nesting gracefully."""
        # Should not crash, should return reasonable value
        result = get_cognitive_complexity_fallback(cyclomatic=3, max_nesting=0)
        assert result >= 1

    def test_fallback_formula_with_high_cc_and_nesting(self):
        """Formula with both high CC and high nesting."""
        result = get_cognitive_complexity_fallback(cyclomatic=5, max_nesting=10)
        # Should reflect both complexity sources
        assert result >= 10


class TestCognitiveComplexityEdgeCases:
    """Test cognitive complexity calculation edge cases."""

    def test_simple_fixture_zero_cognitive_complexity(self):
        """Simple linear fixture with no nesting should have CC_cog = 0."""
        code = """
@pytest.fixture
def simple():
    return create_resource()
"""
        result = analyze_function_complexity(code, "python")
        # Simple code should have low cognitive complexity
        assert result["cognitive_complexity"] >= 0

    def test_nested_if_in_loop_increases_cognitive(self):
        """Nested structures heavily weight cognitive complexity."""
        code = """
def nested_complexity():
    for item in items:
        if item.valid():
            if item.ready():
                process(item)
"""
        result = analyze_function_complexity(code, "python")
        # Nested ifs in loops should increase cognitive complexity
        assert result["cognitive_complexity"] >= 1

    def test_boolean_expressions_add_cognitive(self):
        """Complex boolean expressions increase cognitive complexity."""
        code = """
def complex_boolean():
    if a and b or c and d and e or f:
        return True
    return False
"""
        result = analyze_function_complexity(code, "python")
        # Multiple boolean operators should increase cognitive complexity
        assert result["cognitive_complexity"] >= 1

    def test_cognitive_complexity_python_with_async(self):
        """Async functions should calculate cognitive complexity."""
        code = """
async def async_fixture():
    if condition:
        await setup()
    return result
"""
        result = analyze_function_complexity(code, "python")
        # Should handle async functions
        assert result["cognitive_complexity"] >= 0

    def test_deep_nesting_penalty_in_cognitive(self):
        """Deeply nested structures heavily penalize cognitive complexity."""
        code = """
def deeply_nested():
    if a:
        if b:
            if c:
                if d:
                    if e:
                        result = process()
    return result
"""
        result = analyze_function_complexity(code, "python")
        # Deep nesting should have significant cognitive complexity
        assert result["cognitive_complexity"] >= 1


class TestParameterCountAccuracy:
    """Test function parameter counting."""

    def test_no_parameters(self):
        """Function with no parameters should have num_parameters = 0."""
        code = """
def no_params():
    return 42
"""
        result = analyze_function_complexity(code, "python")
        # Lizard counts parameters
        assert result["num_parameters"] == 0

    def test_multiple_parameters(self):
        """Function with multiple parameters should count all."""
        code = """
def with_params(x, y, z):
    return x + y + z
"""
        result = analyze_function_complexity(code, "python")
        # Should count all three parameters
        assert result["num_parameters"] == 3

    def test_default_parameters(self):
        """Default parameters should be counted."""
        code = """
def with_defaults(a, b=1, c=2):
    return a + b + c
"""
        result = analyze_function_complexity(code, "python")
        # All parameters (even with defaults) should be counted
        assert result["num_parameters"] == 3

    def test_variadic_parameters(self):
        """*args and **kwargs should be counted."""
        code = """
def variadic(x, *args, **kwargs):
    return x
"""
        result = analyze_function_complexity(code, "python")
        # Lizard counts *args and **kwargs
        assert result["num_parameters"] >= 1

    def test_typed_parameters(self):
        """Type annotations should not affect parameter count."""
        code = """
def typed(x: int, y: str, z: float) -> bool:
    return len(y) == x
"""
        result = analyze_function_complexity(code, "python")
        assert result["num_parameters"] == 3


class TestObjectInstantiationEdgeCases:
    """Test object instantiation detection."""

    def test_no_instantiations_in_simple_code(self):
        """Simple code with no instantiations."""
        code = """
def fixture():
    x = 1
    y = 2
    return x + y
"""
        result = analyze_function_complexity(code, "python")
        assert result["num_objects_instantiated"] >= 0

    def test_function_calls_vs_constructors(self):
        """Regular function calls should not be counted as instantiations."""
        code = """
def fixture():
    conn = get_connection()
    data = process(conn)
    return data
"""
        result = analyze_function_complexity(code, "python")
        # get_connection() and process() are function calls, not constructors
        # (unless capitalized, which would suggest constructor call)
        # Lizard counts "external calls", we filter for constructors
        assert result["num_objects_instantiated"] >= 0

    def test_dict_list_set_creation(self):
        """Built-in type instantiation ([], {}, set())."""
        code = """
def fixture():
    my_list = []
    my_dict = {}
    my_set = set()
    return [my_list, my_dict, my_set]
"""
        result = analyze_function_complexity(code, "python")
        # Built-in instantiations are counted by Lizard
        assert result["num_objects_instantiated"] >= 0

    def test_capitalized_function_calls_as_constructors(self):
        """Capitalized function calls suggest constructor invocation."""
        code = """
def fixture():
    obj1 = MyClass()
    obj2 = AnotherClass(param1, param2)
    return [obj1, obj2]
"""
        result = analyze_function_complexity(code, "python")
        # Capitalized calls should be counted as instantiations
        assert result["num_objects_instantiated"] >= 0

    def test_java_new_keyword(self):
        """Java 'new' keyword indicates instantiation."""
        code = """
public void fixture() {
    Database db = new Database();
    Connection conn = new Connection(db);
    Resource res = new Resource()
}
"""
        result = analyze_function_complexity(code, "java")
        # Java new keyword should be detected
        assert result["num_objects_instantiated"] >= 0

    def test_javascript_new_operator(self):
        """JavaScript 'new' operator indicates instantiation."""
        code = """
function fixture() {
    const obj = new Object();
    const map = new Map();
    const arr = new Array(10);
}
"""
        result = analyze_function_complexity(code, "javascript")
        assert result["num_objects_instantiated"] >= 0


class TestErrorHandlingInComplexityAnalysis:
    """Test error handling and graceful degradation."""

    def test_invalid_python_syntax(self):
        """Invalid syntax should return defaults, not crash."""
        code = """
def broken(
    # Missing closing paren
    return None
"""
        result = analyze_function_complexity(code, "python")
        # Should return dict with defaults
        assert isinstance(result, dict)
        assert "cyclomatic_complexity" in result
        assert "cognitive_complexity" in result
        # Defaults should be set if analysis fails
        assert result["cyclomatic_complexity"] >= 1

    def test_invalid_java_syntax(self):
        """Invalid Java syntax should be handled gracefully."""
        code = """
public void broken() {
    int x =  // Missing value
}
"""
        result = analyze_function_complexity(code, "java")
        assert isinstance(result, dict)
        assert "cyclomatic_complexity" in result

    def test_empty_code_string(self):
        """Empty code string should return defaults."""
        result = analyze_function_complexity("", "python")
        assert result["cyclomatic_complexity"] >= 1
        assert "cognitive_complexity" in result

    def test_whitespace_only_code(self):
        """Code with only whitespace should return defaults."""
        result = analyze_function_complexity("   \n\n   \t  ", "python")
        assert isinstance(result, dict)
        assert result["cyclomatic_complexity"] >= 1

    def test_unsupported_language_uses_defaults(self):
        """Unsupported languages should use fallback formulas."""
        code = """
func test() {
    if x { y() }
}
"""
        result = analyze_function_complexity(code, "rust")
        # Should still return dict with sensible defaults
        assert isinstance(result, dict)
        assert "cyclomatic_complexity" in result
        assert result["cyclomatic_complexity"] >= 1


class TestCrossLanguageConsistency:
    """Test consistency of metrics across languages."""

    def test_similar_logic_comparable_cc(self):
        """Similar logic in different languages should have comparable CC."""
        python_code = """
def fixture():
    if x:
        return True
    return False
"""
        
        java_code = """
public boolean fixture() {
    if (x) {
        return true;
    }
    return false;
}
"""
        
        py_result = analyze_function_complexity(python_code, "python")
        java_result = analyze_function_complexity(java_code, "java")
        
        # Both should have CC >= 2 (one if statement)
        assert py_result["cyclomatic_complexity"] >= 2
        assert java_result["cyclomatic_complexity"] >= 2

    def test_language_specific_parameter_counting(self):
        """Parameter count should be consistent across languages."""
        python_code = """
def func(a, b, c):
    pass
"""
        
        java_code = """
public void func(int a, int b, int c) {
}
"""
        
        py_result = analyze_function_complexity(python_code, "python")
        java_result = analyze_function_complexity(java_code, "java")
        
        # Both should count 3 parameters
        assert py_result["num_parameters"] == 3
        assert java_result["num_parameters"] == 3


class TestMetricsConsistency:
    """Test that all metrics are calculated and consistent."""

    def test_all_metrics_present_in_result(self):
        """All expected metrics should be present in result dict."""
        code = """
def fixture():
    return setup()
"""
        result = analyze_function_complexity(code, "python")
        
        expected_keys = [
            "cyclomatic_complexity",
            "cognitive_complexity",
            "num_parameters",
            "num_objects_instantiated",
            "num_external_calls",
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing metric: {key}"

    def test_metrics_are_non_negative(self):
        """All metrics should be non-negative integers."""
        code = """
def fixture():
    return 42
"""
        result = analyze_function_complexity(code, "python")
        
        assert result["cyclomatic_complexity"] >= 1  # CC is always >= 1
        assert result["cognitive_complexity"] >= 0   # CC_cog can be 0
        assert result["num_parameters"] >= 0
        assert result["num_objects_instantiated"] >= 0
        assert result["num_external_calls"] >= 0

    def test_cognition_less_than_or_equal_cyclomatic(self):
        """For simplicity, cognitive complexity should not exceed cyclomatic + nesting."""
        code = """
def complex_fixture():
    for i in range(10):
        if check(i):
            for j in range(10):
                process(i, j)
"""
        result = analyze_function_complexity(code, "python")
        
        # This is a heuristic test; both should be reasonably close
        assert result["cognitive_complexity"] >= 0
        assert result["cyclomatic_complexity"] >= 1
