package testdata

type User struct {
	name  string
	email string
	age   int
}

// GetName has a Get prefix and should be Name().
func (u User) GetName() string {
	return u.name
}

// GetEmail has a Get prefix and should be Email().
func (u User) GetEmail() string {
	return u.email
}

// GetAge has a Get prefix and should be Age().
func (u *User) GetAge() int {
	return u.age
}

// GetFreeFunction is a free function with Get prefix — also flagged.
func GetFreeFunction() string {
	return "free"
}
