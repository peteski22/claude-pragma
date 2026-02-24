package testdata

type Account struct {
	name    string
	balance int
}

// Name is a proper getter without Get prefix.
func (a Account) Name() string {
	return a.name
}

// Balance is a proper getter without Get prefix.
func (a Account) Balance() int {
	return a.balance
}

// SetName is an acceptable setter.
func (a *Account) SetName(name string) {
	a.name = name
}

// GettysburgAddress is not a getter — "Get" is part of the word.
func (a Account) GettysburgAddress() string {
	return "Gettysburg"
}

// Getaway is not a getter — lowercase after "Get".
func (a Account) Getaway() string {
	return "getaway"
}
