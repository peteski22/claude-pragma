package testdata

import "fmt"

// DoSomething is a function declared before types.
func DoSomething() {
	fmt.Println("hello")
}

// BadOrder is a type declared after a function.
type BadOrder struct {
	name string
}
