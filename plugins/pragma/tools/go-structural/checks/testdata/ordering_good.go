package testdata

import "fmt"

const defaultName = "world"

var greeting = "hello"

// Greeter defines the greeting interface.
type Greeter interface {
	Greet() string
}

// Person is a concrete type.
type Person struct {
	name string
}

// Greet returns a greeting.
func (p Person) Greet() string {
	return fmt.Sprintf("%s, %s", greeting, p.name)
}

// NewPerson creates a Person.
func NewPerson() Person {
	return Person{name: defaultName}
}
