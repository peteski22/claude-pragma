// go-structural performs deterministic structural checks on Go source files.
//
// Usage:
//
//	go-structural [file or directory...]
//
// Exit codes: 0 = pass, 1 = violations found, 2 = tool error.
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"slices"
	"strings"

	"github.com/peteski22/agent-pragma/tools/go-structural/checks"
)

// version is the semantic version of go-structural.
const version = "0.1.0"

// errViolationsFound is returned by run when structural violations are detected.
var errViolationsFound = errors.New("violations found")

// output is the top-level JSON output structure.
type output struct {
	Tool       string             `json:"tool"`
	Version    string             `json:"version"`
	Pass       bool               `json:"pass"`
	Violations []checks.Violation `json:"violations"`
	Summary    summary            `json:"summary"`
}

// summary holds aggregate counts.
type summary struct {
	FilesChecked int `json:"files_checked"`
	Errors       int `json:"errors"`
	Warnings     int `json:"warnings"`
}

// collectGoFiles finds .go files from a path. If path is a file, returns it
// directly. If path is a directory, walks it recursively collecting .go files
// (excluding test files, vendor, and testdata directories). Returns an error
// if an explicit file path is not a Go source file.
func collectGoFiles(path string) ([]string, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}

	if !info.IsDir() {
		if strings.HasSuffix(path, "_test.go") {
			return nil, fmt.Errorf("not a Go source file (test file): %s", path)
		}
		if !strings.HasSuffix(path, ".go") {
			return nil, fmt.Errorf("not a Go source file: %s", path)
		}
		return []string{path}, nil
	}

	var files []string
	err = filepath.WalkDir(path, func(p string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}

		if d.IsDir() {
			name := d.Name()
			if name == "vendor" || name == "testdata" || name == ".git" {
				return filepath.SkipDir
			}
			return nil
		}

		if strings.HasSuffix(p, ".go") && !strings.HasSuffix(p, "_test.go") {
			files = append(files, p)
		}

		return nil
	})

	return files, err
}

func main() {
	err := run(os.Args[1:])
	if err == nil {
		return
	}

	if errors.Is(err, errViolationsFound) {
		os.Exit(1)
	}

	_, _ = fmt.Fprintf(os.Stderr, "go-structural: %s\n", err)
	os.Exit(2)
}

// run parses the given paths, executes all checks, and writes JSON results to stdout.
func run(args []string) error {
	if len(args) == 0 {
		args = []string{"."}
	}

	var allFiles []string
	for _, arg := range args {
		files, err := collectGoFiles(arg)
		if err != nil {
			return fmt.Errorf("collecting files from %s: %s", arg, err)
		}
		allFiles = append(allFiles, files...)
	}

	slices.Sort(allFiles)

	if len(allFiles) == 0 {
		return fmt.Errorf("no Go files found in %v", args)
	}

	fileSet := token.NewFileSet()
	allViolations := make([]checks.Violation, 0)

	for _, filename := range allFiles {
		file, err := parser.ParseFile(fileSet, filename, nil, parser.ParseComments)
		if err != nil {
			return fmt.Errorf("parsing %s: %s", filename, err)
		}

		violations := checks.Run(fileSet, file, filename)
		allViolations = append(allViolations, violations...)
	}

	errorCount := 0
	warningCount := 0
	for _, v := range allViolations {
		switch v.Severity {
		case checks.SeverityError:
			errorCount++
		case checks.SeverityWarning:
			warningCount++
		}
	}

	out := output{
		Tool:       "go-structural",
		Version:    version,
		Pass:       errorCount == 0,
		Violations: allViolations,
		Summary: summary{
			FilesChecked: len(allFiles),
			Errors:       errorCount,
			Warnings:     warningCount,
		},
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(out); err != nil {
		return fmt.Errorf("encoding output: %s", err)
	}

	if errorCount > 0 {
		return errViolationsFound
	}

	return nil
}
