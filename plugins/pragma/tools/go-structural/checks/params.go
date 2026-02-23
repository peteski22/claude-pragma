package checks

import (
	"fmt"
	"go/ast"
	"go/token"
)

// paramCountChecker flags functions with more than maxParams parameters.
type paramCountChecker struct {
	maxParams int
	rule      string
}

// check flags functions and methods that exceed the maximum parameter count.
func (c *paramCountChecker) check(fileSet *token.FileSet, file *ast.File, filename string) []Violation {
	var violations []Violation

	ast.Inspect(file, func(n ast.Node) bool {
		fn, ok := n.(*ast.FuncDecl)
		if !ok {
			return true
		}

		count := countParams(fn.Type.Params)
		if count <= c.maxParams {
			return true
		}

		pos := fileSet.Position(fn.Pos())
		violations = append(violations, Violation{
			Rule:       c.rule,
			File:       filename,
			Line:       pos.Line,
			Message:    fmt.Sprintf("%s() has %d parameters (max %d)", fn.Name.Name, count, c.maxParams),
			Severity:   SeverityError,
			Suggestion: "Use options pattern or config struct",
		})

		return true
	})

	return violations
}

// countParams counts the total number of individual parameters in a field list.
func countParams(params *ast.FieldList) int {
	if params == nil {
		return 0
	}
	count := 0
	for _, field := range params.List {
		if len(field.Names) == 0 {
			// Unnamed parameter (e.g., in interface methods).
			count++
			continue
		}
		count += len(field.Names)
	}
	return count
}
