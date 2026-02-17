package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/require"
)

func TestCollectGoFiles_SingleFile(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	goFile := filepath.Join(dir, "main.go")
	require.NoError(t, os.WriteFile(goFile, []byte("package main\n"), 0o644))

	files, err := collectGoFiles(goFile)
	require.NoError(t, err)
	require.Len(t, files, 1)
	require.Equal(t, goFile, files[0])
}

func TestCollectGoFiles_SkipsTestFiles(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	testFile := filepath.Join(dir, "main_test.go")
	require.NoError(t, os.WriteFile(testFile, []byte("package main\n"), 0o644))

	files, err := collectGoFiles(dir)
	require.NoError(t, err)
	require.Empty(t, files)
}

func TestCollectGoFiles_SkipsVendor(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	vendorDir := filepath.Join(dir, "vendor")
	require.NoError(t, os.MkdirAll(vendorDir, 0o755))
	vendorFile := filepath.Join(vendorDir, "dep.go")
	require.NoError(t, os.WriteFile(vendorFile, []byte("package vendor\n"), 0o644))

	files, err := collectGoFiles(dir)
	require.NoError(t, err)
	require.Empty(t, files)
}

func TestCollectGoFiles_Directory(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	require.NoError(t, os.WriteFile(filepath.Join(dir, "a.go"), []byte("package a\n"), 0o644))
	require.NoError(t, os.WriteFile(filepath.Join(dir, "b.go"), []byte("package a\n"), 0o644))
	require.NoError(t, os.WriteFile(filepath.Join(dir, "c.txt"), []byte("not go\n"), 0o644))

	files, err := collectGoFiles(dir)
	require.NoError(t, err)
	require.Len(t, files, 2)
}

func TestCollectGoFiles_RejectsNonGoFile(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	txtFile := filepath.Join(dir, "readme.txt")
	require.NoError(t, os.WriteFile(txtFile, []byte("hello\n"), 0o644))

	_, err := collectGoFiles(txtFile)
	require.Error(t, err)
	require.Contains(t, err.Error(), "not a Go source file")
}

func TestCollectGoFiles_RejectsTestFile(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	testFile := filepath.Join(dir, "main_test.go")
	require.NoError(t, os.WriteFile(testFile, []byte("package main\n"), 0o644))

	_, err := collectGoFiles(testFile)
	require.Error(t, err)
	require.Contains(t, err.Error(), "not a Go source file")
}

func TestOutputJSON_Format(t *testing.T) {
	t.Parallel()
	out := output{
		Tool:       "go-structural",
		Version:    version,
		Pass:       true,
		Violations: nil,
		Summary: summary{
			FilesChecked: 1,
			Errors:       0,
			Warnings:     0,
		},
	}

	data, err := json.Marshal(out)
	require.NoError(t, err)

	var decoded map[string]any
	require.NoError(t, json.Unmarshal(data, &decoded))
	require.Equal(t, "go-structural", decoded["tool"])
	require.Equal(t, true, decoded["pass"])
}

func TestRun_CleanFiles(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	require.NoError(t, os.WriteFile(
		filepath.Join(dir, "clean.go"),
		[]byte("package clean\n\nfunc Hello() string { return \"hello\" }\n"),
		0o644,
	))

	err := run([]string{dir})
	require.NoError(t, err)
}

func TestRun_ViolationsFound(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	require.NoError(t, os.WriteFile(
		filepath.Join(dir, "bad.go"),
		[]byte("package bad\n\nfunc GetName() string { return \"\" }\n"),
		0o644,
	))

	err := run([]string{dir})
	require.ErrorIs(t, err, errViolationsFound)
}

func TestRun_NoFilesFound(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	err := run([]string{dir})
	require.Error(t, err)
	require.Contains(t, err.Error(), "no Go files found")
}
