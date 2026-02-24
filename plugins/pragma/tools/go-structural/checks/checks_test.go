package checks_test

import (
	"go/parser"
	"go/token"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/require"

	"github.com/peteski22/claude-pragma/tools/go-structural/checks"
)

// parseTestFile parses a testdata fixture and runs all checks against it.
func parseTestFile(t *testing.T, name string) []checks.Violation {
	t.Helper()
	path := filepath.Join("testdata", name)
	fileSet := token.NewFileSet()
	file, err := parser.ParseFile(fileSet, path, nil, parser.ParseComments)
	require.NoError(t, err)
	return checks.Run(fileSet, file, path)
}

// filterByRule returns only violations matching the given rule name.
func filterByRule(violations []checks.Violation, rule string) []checks.Violation {
	var filtered []checks.Violation
	for _, v := range violations {
		if v.Rule == rule {
			filtered = append(filtered, v)
		}
	}
	return filtered
}

func TestGetterPrefix_Bad(t *testing.T) {
	t.Parallel()
	violations := parseTestFile(t, "getters_bad.go")

	getterViolations := filterByRule(violations, "no-get-prefix")
	require.Len(t, getterViolations, 4)

	expected := []struct {
		message    string
		suggestion string
	}{
		{message: "GetName() should be Name()", suggestion: "Rename to Name()"},
		{message: "GetEmail() should be Email()", suggestion: "Rename to Email()"},
		{message: "GetAge() should be Age()", suggestion: "Rename to Age()"},
		{message: "GetFreeFunction() should be FreeFunction()", suggestion: "Rename to FreeFunction()"},
	}

	for i, tc := range expected {
		require.Equal(t, tc.message, getterViolations[i].Message)
		require.Equal(t, tc.suggestion, getterViolations[i].Suggestion)
		require.Equal(t, checks.SeverityError, getterViolations[i].Severity)
	}
}

func TestGetterPrefix_Good(t *testing.T) {
	t.Parallel()
	violations := parseTestFile(t, "getters_good.go")

	getterViolations := filterByRule(violations, "no-get-prefix")
	require.Empty(t, getterViolations)
}

func TestParamCount_Bad(t *testing.T) {
	t.Parallel()
	violations := parseTestFile(t, "params_bad.go")

	paramViolations := filterByRule(violations, "param-count")
	require.Len(t, paramViolations, 2)
	require.Equal(t, "TooManyParams() has 5 parameters (max 4)", paramViolations[0].Message)
	require.Equal(t, "WayTooMany() has 7 parameters (max 4)", paramViolations[1].Message)
}

func TestParamCount_Good(t *testing.T) {
	t.Parallel()
	violations := parseTestFile(t, "params_good.go")

	paramViolations := filterByRule(violations, "param-count")
	require.Empty(t, paramViolations)
}

func TestFileOrdering_Bad(t *testing.T) {
	t.Parallel()
	violations := parseTestFile(t, "ordering_bad.go")

	orderViolations := filterByRule(violations, "file-ordering")
	require.Len(t, orderViolations, 1)
	require.Equal(t, "types section appears after functions section", orderViolations[0].Message)
}

func TestFileOrdering_Good(t *testing.T) {
	t.Parallel()
	violations := parseTestFile(t, "ordering_good.go")

	orderViolations := filterByRule(violations, "file-ordering")
	require.Empty(t, orderViolations)
}

func TestFileOrdering_InitAllowed(t *testing.T) {
	t.Parallel()
	violations := parseTestFile(t, "ordering_init.go")

	orderViolations := filterByRule(violations, "file-ordering")
	require.Empty(t, orderViolations)
}

func TestRun_CleanFile(t *testing.T) {
	t.Parallel()
	violations := parseTestFile(t, "ordering_good.go")

	// ordering_good.go should have zero violations from any check.
	require.Empty(t, violations)
}
