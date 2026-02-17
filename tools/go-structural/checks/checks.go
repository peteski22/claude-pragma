// Package checks provides deterministic structural checks for Go source files.
package checks

import (
	"go/ast"
	"go/token"
)

const (
	// SeverityError indicates a violation that must be fixed.
	SeverityError Severity = "error"

	// SeverityWarning indicates a violation that should be reviewed.
	SeverityWarning Severity = "warning"

	// ruleFileOrdering is the rule name for file section ordering violations.
	ruleFileOrdering = "file-ordering"

	// ruleNoGetPrefix is the rule name for Get-prefix naming violations.
	ruleNoGetPrefix = "no-get-prefix"

	// ruleParamCount is the rule name for excessive parameter count violations.
	ruleParamCount = "param-count"
)

// allCheckers is the ordered list of checks to run, initialized once at package load.
var allCheckers = []checker{
	newPrefixChecker("Get", ruleNoGetPrefix),
	&paramCountChecker{maxParams: 4, rule: ruleParamCount},
	&fileOrderingChecker{rule: ruleFileOrdering},
}

// checker defines the interface for a structural check.
type checker interface {
	// check runs the check against the given file and returns violations.
	check(fileSet *token.FileSet, file *ast.File, filename string) []Violation
}

// Severity represents the severity of a violation.
type Severity string

// Violation represents a single structural check failure.
type Violation struct {
	Rule       string   `json:"rule"`
	File       string   `json:"file"`
	Line       int      `json:"line"`
	Message    string   `json:"message"`
	Severity   Severity `json:"severity"`
	Suggestion string   `json:"suggestion,omitempty"`
}

// Run executes all structural checks on the given parsed file and returns violations.
func Run(fileSet *token.FileSet, file *ast.File, filename string) []Violation {
	var violations []Violation
	for _, c := range allCheckers {
		violations = append(violations, c.check(fileSet, file, filename)...)
	}
	return violations
}
