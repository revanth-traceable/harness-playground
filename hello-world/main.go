package main

import (
	"fmt"
	"github.com/google/uuid"
	"github.com/revanth/hello-world/mathutil"
)

func main() {
	fmt.Println("Hello, World! This is a test CI application.")
	
	result := mathutil.Add(5, 3)
	fmt.Printf("5 + 3 = %d\n", result)
	
	id := uuid.New()
	fmt.Printf("Generated UUID: %s\n", id.String())
}
