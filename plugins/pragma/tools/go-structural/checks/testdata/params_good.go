package testdata

// NoParams has zero parameters.
func NoParams() string {
	return "hello"
}

// OneParam has one parameter.
func OneParam(a string) string {
	return a
}

// FourParams has exactly four parameters (the max).
func FourParams(a string, b string, c string, d string) string {
	return a + b + c + d
}
