# 📚 Fresh Standard Library & Built-ins Reference

This document provides a comprehensive API reference for all standard library and built-in functions available in Fresh.

---

## 1. Core I/O & Terminal Functions

### `print(...args)`
Prints one or more values to standard output separated by spaces without a trailing newline.
- **Parameters**: `...args: any` — Variadic arguments of any printable type.
- **Returns**: `nil`
- **Example**:
  ```fresh
  print("Loading: ", 42, "%");
  ```

### `println(...args)`
Prints one or more values to standard output separated by spaces, followed by a newline.
- **Parameters**: `...args: any` — Variadic arguments of any printable type.
- **Returns**: `nil`
- **Example**:
  ```fresh
  println("Hello, World!");
  println("Count:", 1, "Status:", true);
  ```

### `input([prompt: string]) -> string`
Reads a single line of text from standard input.
- **Parameters**: `prompt` *(optional)* — String displayed to the user before reading input.
- **Returns**: `string` — The input line.
- **Example**:
  ```fresh
  let name = input("Enter your name: ");
  println("Hello, " + name);
  ```

### `read_int() -> int`
Reads standard input and parses the trimmed text into an integer.
- **Returns**: `int`
- **Errors**: Raises `[E5001]` runtime error if input is not a valid decimal integer.
- **Example**:
  ```fresh
  let age = read_int();
  ```

---

## 2. Collections & Array Functions

### `len(obj: [T] | string) -> int`
Returns the number of elements in a dynamic array or the byte length of a string.
- **Parameters**: `obj` — Array or string.
- **Returns**: `int` — Length count ($\ge 0$).
- **Errors**: Raises `[E5001]` if `obj` is not an array or string.
- **Example**:
  ```fresh
  let items = [10, 20, 30];
  println(len(items)); // 3
  println(len("Fresh")); // 5
  ```

### `push(arr: [T], item: T) -> nil`
Appends an element to the end of a dynamic array in-place.
- **Parameters**:
  - `arr`: The target array.
  - `item`: Element to append.
- **Returns**: `nil`
- **Example**:
  ```fresh
  let fruits = ["apple", "banana"];
  push(fruits, "cherry");
  println(len(fruits)); // 3
  ```

### `pop(arr: [T]) -> T`
Removes and returns the last element from an array.
- **Parameters**: `arr` — The target array.
- **Returns**: The popped element.
- **Errors**: Raises `[E5001]` if called on an empty array or a non-array value.
- **Example**:
  ```fresh
  let stack = [1, 2, 3];
  let top = pop(stack); // top is 3
  ```

---

## 3. Type Conversion & Reflection

### `type(val: any) -> string`
Returns the runtime type name of a value.
- **Parameters**: `val: any`
- **Returns**: `"nil"`, `"bool"`, `"int"`, `"float"`, `"string"`, `"array"`, `"fn"`, or the declared struct name.
- **Example**:
  ```fresh
  println(type(42));       // "int"
  println(type(3.14));     // "float"
  println(type([1, 2]));   // "array"
  ```

### `to_string(val: any) -> string`
Converts any value into its canonical string representation.
- **Parameters**: `val: any`
- **Returns**: `string`

### `to_int(val: string | float | bool) -> int`
Converts a numeric string, float, or boolean into a signed 64-bit integer.
- **Parameters**: `val` — Target value.
- **Returns**: `int`
- **Errors**: Raises `[E5001]` if string cannot be parsed as an integer.

### `to_float(val: string | int) -> float`
Converts a numeric string or integer into an IEEE 754 double precision float.
- **Parameters**: `val` — Target value.
- **Returns**: `float`

---

## 4. File System & OS Functions

### `read_file(path: string) -> string`
Reads the entire contents of a UTF-8 encoded text file into a string.
- **Parameters**: `path` — File system path.
- **Returns**: `string`
- **Errors**: Raises `[E5001]` if the file does not exist or cannot be read.
- **Example**:
  ```fresh
  let content = read_file("config.txt");
  println(content);
  ```

### `write_file(path: string, content: string) -> bool`
Writes text content to a file, creating it if it does not exist or overwriting it if it does.
- **Parameters**:
  - `path`: Target file path.
  - `content`: Text to write.
- **Returns**: `true` on success.
- **Errors**: Raises `[E5001]` on I/O or permission errors.
- **Example**:
  ```fresh
  write_file("output.txt", "Fresh Language v0.1.0\n");
  ```

### `file_exists(path: string) -> bool`
Checks whether a file or directory exists at the specified path.
- **Parameters**: `path` — Target path.
- **Returns**: `true` if path exists, `false` otherwise.

### `clock() -> float`
Returns the current system time in seconds as a high-resolution floating-point timestamp.
- **Returns**: `float`
- **Example**:
  ```fresh
  let start = clock();
  // ... run benchmark work ...
  let elapsed = clock() - start;
  println("Elapsed:", elapsed, "seconds");
  ```

---

## 5. Math Library Functions

All math library functions operate with strict error boundary checks, converting arithmetic exceptions into informative `FreshRuntimeError` diagnostics.

| Function | Signature | Description | Example |
|:---|:---|:---|:---|
| `abs(x)` | `(int \| float) -> int \| float` | Returns the absolute value of `x`. | `abs(-42) // 42` |
| `sqrt(x)` | `(float \| int) -> float` | Computes the square root of `x` ($\ge 0$). | `sqrt(81.0) // 9.0` |
| `pow(x, y)` | `(float, float) -> float` | Raises base `x` to the exponent `y` ($x^y$). | `pow(2.0, 10.0) // 1024.0` |
| `min(a, b)` | `(int \| float, int \| float) -> same` | Returns the smaller of two numbers. | `min(10, 4) // 4` |
| `max(a, b)` | `(int \| float, int \| float) -> same` | Returns the larger of two numbers. | `max(10, 4) // 10` |
| `floor(x)` | `(float) -> int` | Largest integer less than or equal to `x`. | `floor(7.89) // 7` |
| `ceil(x)` | `(float) -> int` | Smallest integer greater than or equal to `x`. | `ceil(7.12) // 8` |
| `round(x)` | `(float) -> int` | Rounds `x` to the nearest integer. | `round(7.50) // 8` |
