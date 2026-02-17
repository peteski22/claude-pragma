package checks

import (
	"fmt"
	"go/ast"
	"go/token"
)

const (
	// sectionNone represents no section classification or an initial state.
	sectionNone sectionKind = iota

	// sectionImport represents the import declaration block.
	sectionImport

	// sectionConst represents the const declaration block.
	sectionConst

	// sectionVar represents the var declaration block.
	sectionVar

	// sectionInterface represents interface type declarations.
	sectionInterface

	// sectionType represents non-interface type declarations.
	sectionType

	// sectionFunc represents function and method declarations.
	sectionFunc
)

// fileOrderingChecker verifies that top-level declarations follow the expected
// section order: package -> imports -> const -> var -> interface -> type -> func.
type fileOrderingChecker struct {
	rule string
}

// sectionKind represents a category of top-level declaration.
type sectionKind int

// check verifies that top-level declarations appear in the expected section order.
// Each violation is reported relative to the highest section seen so far. The
// high-water mark advances only when a higher section is encountered, so
// multiple regressions are all reported against the true maximum.
//
// Note: this enforces strict section grouping (all types before all functions).
// Methods placed immediately after their receiver type will be flagged if a
// non-function section follows. This is intentional per the project convention
// of grouping by section rather than by type-with-methods.
func (c *fileOrderingChecker) check(fileSet *token.FileSet, file *ast.File, filename string) []Violation {
	var violations []Violation
	lastSection := sectionNone

	for _, decl := range file.Decls {
		section, pos := classify(fileSet, decl)
		if section == sectionNone {
			continue
		}

		// init() functions are allowed anywhere after imports.
		if fn, ok := decl.(*ast.FuncDecl); ok && fn.Name.Name == "init" {
			continue
		}

		if section < lastSection {
			violations = append(violations, Violation{
				Rule: c.rule,
				File: filename,
				Line: pos.Line,
				Message: fmt.Sprintf(
					"%s section appears after %s section",
					sectionName(section),
					sectionName(lastSection),
				),
				Severity: SeverityError,
			})
		}

		// Advance the high-water mark when a higher section is seen.
		if section > lastSection {
			lastSection = section
		}
	}

	return violations
}

// classify determines which section a declaration belongs to.
func classify(fileSet *token.FileSet, decl ast.Decl) (sectionKind, token.Position) {
	switch d := decl.(type) {
	case *ast.GenDecl:
		pos := fileSet.Position(d.Pos())
		switch d.Tok {
		case token.IMPORT:
			return sectionImport, pos
		case token.CONST:
			return sectionConst, pos
		case token.VAR:
			return sectionVar, pos
		case token.TYPE:
			if isInterface(d) {
				return sectionInterface, pos
			}
			return sectionType, pos
		default:
			return sectionNone, pos
		}
	case *ast.FuncDecl:
		return sectionFunc, fileSet.Position(d.Pos())
	default:
		return sectionNone, token.Position{}
	}
}

// isInterface checks whether a type declaration contains only interface types.
// For grouped type declarations containing a mix of interfaces and non-interfaces
// (e.g., type ( Foo interface{...}; Bar struct{...} )), the entire block is
// classified as a non-interface type. This is a known simplification; ungrouped
// type declarations are recommended per the project's ordering convention.
func isInterface(d *ast.GenDecl) bool {
	for _, spec := range d.Specs {
		ts, ok := spec.(*ast.TypeSpec)
		if !ok {
			return false
		}
		if _, ok := ts.Type.(*ast.InterfaceType); !ok {
			return false
		}
	}
	return true
}

// sectionName returns a human-readable name for the section.
func sectionName(s sectionKind) string {
	switch s {
	case sectionNone:
		return "none"
	case sectionImport:
		return "imports"
	case sectionConst:
		return "constants"
	case sectionVar:
		return "variables"
	case sectionInterface:
		return "interfaces"
	case sectionType:
		return "types"
	case sectionFunc:
		return "functions"
	default:
		return "unknown"
	}
}
