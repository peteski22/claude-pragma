package checks

import (
	"fmt"
	"go/ast"
	"go/token"
	"strings"
	"unicode"
)

// prefixChecker flags functions and methods whose names match a given prefix
// followed by an uppercase letter (e.g., GetName, SetValue).
type prefixChecker struct {
	prefix string
	rule   string
}

// check flags functions and methods whose names match the configured prefix pattern.
func (c *prefixChecker) check(fileSet *token.FileSet, file *ast.File, filename string) []Violation {
	var violations []Violation

	ast.Inspect(file, func(n ast.Node) bool {
		fn, ok := n.(*ast.FuncDecl)
		if !ok {
			return true
		}

		name := fn.Name.Name
		if !c.matches(name) {
			return true
		}

		suggested := name[len(c.prefix):]
		pos := fileSet.Position(fn.Pos())

		violations = append(violations, Violation{
			Rule:       c.rule,
			File:       filename,
			Line:       pos.Line,
			Message:    fmt.Sprintf("%s() should be %s()", name, suggested),
			Severity:   SeverityError,
			Suggestion: fmt.Sprintf("Rename to %s()", suggested),
		})

		return true
	})

	return violations
}

// matches reports whether name starts with the configured prefix followed by
// an uppercase letter.
func (c *prefixChecker) matches(name string) bool {
	if !strings.HasPrefix(name, c.prefix) {
		return false
	}
	if len(name) <= len(c.prefix) {
		return false
	}
	return unicode.IsUpper(rune(name[len(c.prefix)]))
}

// newPrefixChecker creates a checker that flags functions whose names start
// with prefix followed by an uppercase letter.
func newPrefixChecker(prefix string, rule string) *prefixChecker {
	return &prefixChecker{
		prefix: prefix,
		rule:   rule,
	}
}
