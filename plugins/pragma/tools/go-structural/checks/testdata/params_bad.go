package testdata

// TooManyParams has 5 parameters.
func TooManyParams(a string, b string, c string, d string, e string) string {
	return a + b + c + d + e
}

// WayTooMany has 7 parameters.
func WayTooMany(a int, b int, c int, d int, e int, f int, g int) int {
	return a + b + c + d + e + f + g
}
