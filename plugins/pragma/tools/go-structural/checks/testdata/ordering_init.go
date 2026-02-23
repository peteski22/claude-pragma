package testdata

import "fmt"

// init is allowed anywhere after imports.
func init() {
	fmt.Println("initializing")
}

const initConst = "value"

type InitType struct {
	field string
}

func InitFunc() string {
	return initConst
}
