"""
Test wrappers for semantic verification.

Each entry maps a function name to a list of main() test cases.
Each case is a complete `int main() { ... }` body that returns 0 on success, non-zero on failure.

Coverage target: ≥5 cases per function covering:
  - 2+ normal inputs
  - 1+ boundary/edge values (0, 1, empty, max)
  - 1+ negative/overflow inputs where applicable
  - 1+ larger inputs
"""

TEST_WRAPPERS: dict[str, list[str]] = {
    "fibonacci": [
        "\nint main() { if (fibonacci(0) != 0) return 1; return 0; }\n",
        "\nint main() { if (fibonacci(1) != 1) return 1; return 0; }\n",
        "\nint main() { if (fibonacci(5) != 5) return 1; return 0; }\n",
        "\nint main() { if (fibonacci(10) != 55) return 1; return 0; }\n",
        "\nint main() { if (fibonacci(2) != 1) return 1; return 0; }\n",
        "\nint main() { if (fibonacci(15) != 610) return 1; return 0; }\n",
    ],
    "fibonacci_iter": [
        "\nint main() { if (fibonacci_iter(0) != 0) return 1; return 0; }\n",
        "\nint main() { if (fibonacci_iter(1) != 1) return 1; return 0; }\n",
        "\nint main() { if (fibonacci_iter(5) != 5) return 1; return 0; }\n",
        "\nint main() { if (fibonacci_iter(10) != 55) return 1; return 0; }\n",
        "\nint main() { if (fibonacci_iter(2) != 1) return 1; return 0; }\n",
        "\nint main() { if (fibonacci_iter(15) != 610) return 1; return 0; }\n",
    ],
    "max": [
        "\nint main() { if (max(10, 20) != 20) return 1; return 0; }\n",
        "\nint main() { if (max(30, 15) != 30) return 1; return 0; }\n",
        "\nint main() { if (max(-5, -10) != -5) return 1; return 0; }\n",
        "\nint main() { if (max(7, 7) != 7) return 1; return 0; }\n",       # equal values
        "\nint main() { if (max(0, -1) != 0) return 1; return 0; }\n",     # zero vs negative
        "\nint main() { if (max(2147483647, 0) != 2147483647) return 1; return 0; }\n",  # INT_MAX
    ],
    "bubble_sort": [
        "\nint main() { int a[] = {5,2,4,1,3}; bubble_sort(a,5); if (a[0]!=1||a[1]!=2||a[2]!=3||a[3]!=4||a[4]!=5) return 1; return 0; }\n",
        "\nint main() { int a[] = {1}; bubble_sort(a,1); if (a[0]!=1) return 1; return 0; }\n",        # single element
        "\nint main() { int a[] = {1,2,3}; bubble_sort(a,3); if (a[0]!=1||a[1]!=2||a[2]!=3) return 1; return 0; }\n",  # already sorted
        "\nint main() { int a[] = {3,2,1}; bubble_sort(a,3); if (a[0]!=1||a[1]!=2||a[2]!=3) return 1; return 0; }\n",  # reverse sorted
        "\nint main() { int a[] = {-3,0,2,-1}; bubble_sort(a,4); if (a[0]!=-3||a[1]!=-1||a[2]!=0||a[3]!=2) return 1; return 0; }\n",  # negatives
    ],
    "linear_search": [
        "\nint main() { int a[] = {10,20,30,40,50}; if (linear_search(a,5,30)!=2) return 1; return 0; }\n",
        "\nint main() { int a[] = {10,20,30,40,50}; if (linear_search(a,5,60)!=-1) return 1; return 0; }\n",
        "\nint main() { int a[] = {10,20,30,40,50}; if (linear_search(a,5,10)!=0) return 1; return 0; }\n",  # first element
        "\nint main() { int a[] = {10,20,30,40,50}; if (linear_search(a,5,50)!=4) return 1; return 0; }\n",  # last element
        "\nint main() { int a[] = {42}; if (linear_search(a,1,42)!=0) return 1; return 0; }\n",              # single element found
        "\nint main() { int a[] = {42}; if (linear_search(a,1,99)!=-1) return 1; return 0; }\n",            # single element not found
    ],
    "binary_search": [
        "\nint main() { int a[] = {10,20,30,40,50}; if (binary_search(a,5,30)!=2) return 1; return 0; }\n",
        "\nint main() { int a[] = {10,20,30,40,50}; if (binary_search(a,5,60)!=-1) return 1; return 0; }\n",
        "\nint main() { int a[] = {10,20,30,40,50}; if (binary_search(a,5,10)!=0) return 1; return 0; }\n",  # first element
        "\nint main() { int a[] = {10,20,30,40,50}; if (binary_search(a,5,50)!=4) return 1; return 0; }\n",  # last element
        "\nint main() { int a[] = {7}; if (binary_search(a,1,7)!=0) return 1; return 0; }\n",               # single element found
        "\nint main() { int a[] = {7}; if (binary_search(a,1,8)!=-1) return 1; return 0; }\n",              # single element not found
    ],
    "factorial": [
        "\nint main() { if (factorial(0) != 1) return 1; return 0; }\n",
        "\nint main() { if (factorial(1) != 1) return 1; return 0; }\n",
        "\nint main() { if (factorial(5) != 120) return 1; return 0; }\n",
        "\nint main() { if (factorial(3) != 6) return 1; return 0; }\n",
        "\nint main() { if (factorial(10) != 3628800) return 1; return 0; }\n",   # larger input
    ],
    "gcd": [
        "\nint main() { if (gcd(54, 24) != 6) return 1; return 0; }\n",
        "\nint main() { if (gcd(17, 3) != 1) return 1; return 0; }\n",
        "\nint main() { if (gcd(0, 5) != 5) return 1; return 0; }\n",
        "\nint main() { if (gcd(12, 12) != 12) return 1; return 0; }\n",          # same values
        "\nint main() { if (gcd(100, 75) != 25) return 1; return 0; }\n",
        "\nint main() { if (gcd(1, 999) != 1) return 1; return 0; }\n",           # coprime
    ],
    "power": [
        "\nint main() { if (power(2, 10) != 1024) return 1; return 0; }\n",
        "\nint main() { if (power(3, 3) != 27) return 1; return 0; }\n",
        "\nint main() { if (power(5, 0) != 1) return 1; return 0; }\n",
        "\nint main() { if (power(1, 100) != 1) return 1; return 0; }\n",         # base 1
        "\nint main() { if (power(2, 0) != 1) return 1; return 0; }\n",           # exponent 0
        "\nint main() { if (power(7, 2) != 49) return 1; return 0; }\n",
    ],
    "process_code": [
        "\nint main() { if (process_code(0) != 1) return 1; return 0; }\n",
        "\nint main() { if (process_code(50) != 2) return 1; return 0; }\n",
        "\nint main() { if (process_code(150) != 3) return 1; return 0; }\n",
        "\nint main() { if (process_code(450) != -1) return 1; return 0; }\n",
        "\nint main() { if (process_code(999) != 0) return 1; return 0; }\n",
    ],
    "count_bits": [
        "\nint main() { if (count_bits(0) != 0) return 1; return 0; }\n",
        "\nint main() { if (count_bits(7) != 3) return 1; return 0; }\n",
        "\nint main() { if (count_bits(10) != 2) return 1; return 0; }\n",
        "\nint main() { if (count_bits(1) != 1) return 1; return 0; }\n",         # single bit
        "\nint main() { if (count_bits(255) != 8) return 1; return 0; }\n",       # all bits in byte
        "\nint main() { if (count_bits(0xFFFFFFFF) != 32) return 1; return 0; }\n",  # all bits
    ],
    "clamp": [
        "\nint main() { if (clamp(5, 10, 20) != 10) return 1; return 0; }\n",     # below min
        "\nint main() { if (clamp(25, 10, 20) != 20) return 1; return 0; }\n",    # above max
        "\nint main() { if (clamp(15, 10, 20) != 15) return 1; return 0; }\n",    # in range
        "\nint main() { if (clamp(10, 10, 20) != 10) return 1; return 0; }\n",    # exactly min
        "\nint main() { if (clamp(20, 10, 20) != 20) return 1; return 0; }\n",    # exactly max
        "\nint main() { if (clamp(-5, -10, 0) != -5) return 1; return 0; }\n",   # negative range
    ],
    "signum": [
        "\nint main() { if (signum(5) != 1) return 1; return 0; }\n",
        "\nint main() { if (signum(-5) != -1) return 1; return 0; }\n",
        "\nint main() { if (signum(0) != 0) return 1; return 0; }\n",
        "\nint main() { if (signum(1000) != 1) return 1; return 0; }\n",
        "\nint main() { if (signum(-1000) != -1) return 1; return 0; }\n",
    ],
    "checksum": [
        "\nint main() { unsigned char d[] = {10,20,30,40}; if (checksum(d,4) != 100) return 1; return 0; }\n",
        "\nint main() { unsigned char d[] = {0}; if (checksum(d,1) != 0) return 1; return 0; }\n",     # zero element
        "\nint main() { unsigned char d[] = {255}; if (checksum(d,1) != 255) return 1; return 0; }\n", # max byte
        "\nint main() { unsigned char d[] = {1,2,3}; if (checksum(d,3) != 6) return 1; return 0; }\n",
        "\nint main() { unsigned char d[] = {100,100}; if (checksum(d,2) != 200) return 1; return 0; }\n",
    ],
    "classify_range": [
        "\nint main() { if (classify_range(0) != 0) return 1; return 0; }\n",
        "\nint main() { if (classify_range(2) != 1) return 1; return 0; }\n",
        "\nint main() { if (classify_range(10) != 2) return 1; return 0; }\n",
        "\nint main() { if (classify_range(-5) != -1) return 1; return 0; }\n",
        "\nint main() { if (classify_range(100) != 3) return 1; return 0; }\n",
    ],
    "saturating_add": [
        "\nint main() { if (saturating_add(10, 20) != 30) return 1; return 0; }\n",
        "\nint main() { if (saturating_add(2147483640, 10) != 2147483647) return 1; return 0; }\n",
        "\nint main() { if (saturating_add(-2147483640, -10) != -2147483648) return 1; return 0; }\n",
        "\nint main() { if (saturating_add(0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (saturating_add(1, -1) != 0) return 1; return 0; }\n",
    ],
    "rc4_init": [
        "\nint main() { uint8_t s[256]; uint8_t key[] = {1,2,3,4}; rc4_init(s,key,4); uint8_t e[] = {194,82,8,12,50,235,33,44}; for (int i=0;i<8;i++) if (s[i]!=e[i]) return i+1; return 0; }\n",
        "\nint main() { uint8_t s[256]; uint8_t key[] = {1}; rc4_init(s,key,1); uint8_t e[] = {0,2,3,4,5,6,7,8}; for (int i=0;i<8;i++) if (s[i]!=e[i]) return i+1; return 0; }\n",
        "\nint main() { uint8_t s[256]; uint8_t key[] = {0,0,0}; rc4_init(s,key,3); uint8_t e[] = {0,35,3,43,9,11,65,229}; for (int i=0;i<8;i++) if (s[i]!=e[i]) return i+1; return 0; }\n",
        "\nint main() { uint8_t s[256]; uint8_t key[] = {65,66,67}; rc4_init(s,key,3); uint8_t e[] = {84,132,201,55,83,155,226,96}; for (int i=0;i<8;i++) if (s[i]!=e[i]) return i+1; return 0; }\n",
        "\nint main() { uint8_t s[256]; uint8_t key[] = {1,2,3,4}; rc4_init(s,key,4); int seen[256]={0}; for (int i=0;i<256;i++) { seen[s[i]]++; } for (int i=0;i<256;i++) if (seen[i]!=1) return 1; return 0; }\n",
    ],
    "rc4_crypt": [
        "\nint main() { uint8_t s[256] = {194, 82, 8, 12, 50, 235, 33, 44, 251, 165, 149, 141, 87, 163, 119, 188, 19, 161, 11, 57, 226, 249, 180, 45, 156, 114, 107, 130, 2, 49, 231, 9, 43, 253, 25, 127, 10, 203, 244, 109, 72, 215, 108, 26, 204, 176, 95, 54, 77, 128, 36, 191, 38, 134, 75, 123, 216, 205, 131, 4, 16, 93, 15, 59, 55, 14, 71, 96, 179, 250, 133, 243, 122, 105, 151, 168, 174, 221, 214, 79, 210, 172, 80, 41, 173, 17, 74, 142, 106, 73, 135, 129, 126, 150, 146, 177, 40, 21, 245, 222, 147, 89, 162, 117, 92, 197, 63, 189, 160, 153, 220, 3, 195, 100, 171, 56, 112, 213, 167, 20, 186, 184, 84, 241, 52, 219, 124, 83, 209, 182, 166, 185, 6, 110, 207, 88, 240, 223, 140, 62, 159, 29, 46, 234, 113, 125, 35, 152, 202, 178, 218, 239, 118, 158, 94, 67, 120, 183, 212, 255, 187, 230, 28, 170, 238, 217, 68, 31, 97, 246, 102, 206, 232, 70, 145, 99, 148, 48, 247, 237, 208, 85, 137, 169, 23, 39, 136, 111, 157, 37, 236, 224, 199, 154, 1, 30, 190, 7, 98, 76, 196, 211, 229, 53, 225, 61, 78, 192, 143, 198, 242, 121, 66, 18, 252, 115, 34, 101, 155, 201, 103, 116, 200, 27, 233, 69, 91, 254, 64, 104, 193, 132, 164, 65, 0, 24, 13, 139, 181, 248, 227, 60, 42, 81, 175, 86, 138, 32, 22, 144, 58, 47, 90, 5, 51, 228}; uint8_t data[] = {10,20,30}; rc4_crypt(s,data,3); uint8_t e[] = {22,254,143}; for (int i=0;i<3;i++) if (data[i]!=e[i]) return i+1; return 0; }\n",
        "\nint main() { uint8_t s[256] = {194, 82, 8, 12, 50, 235, 33, 44, 251, 165, 149, 141, 87, 163, 119, 188, 19, 161, 11, 57, 226, 249, 180, 45, 156, 114, 107, 130, 2, 49, 231, 9, 43, 253, 25, 127, 10, 203, 244, 109, 72, 215, 108, 26, 204, 176, 95, 54, 77, 128, 36, 191, 38, 134, 75, 123, 216, 205, 131, 4, 16, 93, 15, 59, 55, 14, 71, 96, 179, 250, 133, 243, 122, 105, 151, 168, 174, 221, 214, 79, 210, 172, 80, 41, 173, 17, 74, 142, 106, 73, 135, 129, 126, 150, 146, 177, 40, 21, 245, 222, 147, 89, 162, 117, 92, 197, 63, 189, 160, 153, 220, 3, 195, 100, 171, 56, 112, 213, 167, 20, 186, 184, 84, 241, 52, 219, 124, 83, 209, 182, 166, 185, 6, 110, 207, 88, 240, 223, 140, 62, 159, 29, 46, 234, 113, 125, 35, 152, 202, 178, 218, 239, 118, 158, 94, 67, 120, 183, 212, 255, 187, 230, 28, 170, 238, 217, 68, 31, 97, 246, 102, 206, 232, 70, 145, 99, 148, 48, 247, 237, 208, 85, 137, 169, 23, 39, 136, 111, 157, 37, 236, 224, 199, 154, 1, 30, 190, 7, 98, 76, 196, 211, 229, 53, 225, 61, 78, 192, 143, 198, 242, 121, 66, 18, 252, 115, 34, 101, 155, 201, 103, 116, 200, 27, 233, 69, 91, 254, 64, 104, 193, 132, 164, 65, 0, 24, 13, 139, 181, 248, 227, 60, 42, 81, 175, 86, 138, 32, 22, 144, 58, 47, 90, 5, 51, 228}; uint8_t data[] = {0,0,0,0}; rc4_crypt(s,data,4); uint8_t e[] = {28,234,145,97}; for (int i=0;i<4;i++) if (data[i]!=e[i]) return i+1; return 0; }\n",
        "\nint main() { uint8_t s[256] = {84, 132, 201, 55, 83, 155, 226, 96, 220, 192, 12, 90, 57, 234, 111, 119, 221, 49, 1, 50, 137, 77, 161, 56, 145, 236, 179, 10, 13, 99, 194, 35, 21, 208, 46, 174, 23, 239, 31, 70, 181, 232, 140, 63, 68, 18, 76, 131, 42, 38, 160, 122, 5, 209, 138, 28, 230, 215, 64, 71, 128, 2, 17, 34, 248, 164, 126, 115, 45, 88, 9, 74, 87, 202, 185, 41, 133, 134, 85, 36, 159, 252, 238, 130, 65, 151, 228, 203, 98, 121, 235, 16, 173, 110, 224, 102, 141, 170, 93, 163, 198, 108, 146, 78, 229, 143, 135, 184, 172, 48, 197, 61, 120, 168, 54, 67, 250, 97, 213, 32, 158, 127, 19, 125, 106, 249, 62, 254, 225, 89, 183, 242, 113, 8, 162, 0, 167, 251, 182, 195, 86, 129, 37, 196, 253, 205, 24, 103, 171, 136, 245, 218, 92, 166, 30, 123, 214, 40, 66, 200, 191, 222, 104, 156, 4, 15, 75, 26, 219, 204, 59, 58, 187, 175, 188, 52, 177, 53, 22, 189, 199, 95, 25, 247, 190, 152, 114, 94, 227, 73, 153, 176, 112, 44, 107, 33, 241, 217, 148, 244, 6, 117, 100, 80, 223, 82, 255, 139, 39, 79, 72, 211, 20, 60, 240, 165, 51, 193, 212, 3, 118, 178, 180, 124, 105, 246, 116, 7, 237, 207, 69, 186, 169, 101, 91, 150, 142, 233, 243, 216, 154, 14, 149, 157, 43, 206, 47, 81, 147, 27, 210, 109, 11, 29, 231, 144}; uint8_t data[] = {1,2,3,4,5}; rc4_crypt(s,data,5); uint8_t e[] = {207,38,93,151,74}; for (int i=0;i<5;i++) if (data[i]!=e[i]) return i+1; return 0; }\n",
        "\nint main() { uint8_t s[256] = {194, 82, 8, 12, 50, 235, 33, 44, 251, 165, 149, 141, 87, 163, 119, 188, 19, 161, 11, 57, 226, 249, 180, 45, 156, 114, 107, 130, 2, 49, 231, 9, 43, 253, 25, 127, 10, 203, 244, 109, 72, 215, 108, 26, 204, 176, 95, 54, 77, 128, 36, 191, 38, 134, 75, 123, 216, 205, 131, 4, 16, 93, 15, 59, 55, 14, 71, 96, 179, 250, 133, 243, 122, 105, 151, 168, 174, 221, 214, 79, 210, 172, 80, 41, 173, 17, 74, 142, 106, 73, 135, 129, 126, 150, 146, 177, 40, 21, 245, 222, 147, 89, 162, 117, 92, 197, 63, 189, 160, 153, 220, 3, 195, 100, 171, 56, 112, 213, 167, 20, 186, 184, 84, 241, 52, 219, 124, 83, 209, 182, 166, 185, 6, 110, 207, 88, 240, 223, 140, 62, 159, 29, 46, 234, 113, 125, 35, 152, 202, 178, 218, 239, 118, 158, 94, 67, 120, 183, 212, 255, 187, 230, 28, 170, 238, 217, 68, 31, 97, 246, 102, 206, 232, 70, 145, 99, 148, 48, 247, 237, 208, 85, 137, 169, 23, 39, 136, 111, 157, 37, 236, 224, 199, 154, 1, 30, 190, 7, 98, 76, 196, 211, 229, 53, 225, 61, 78, 192, 143, 198, 242, 121, 66, 18, 252, 115, 34, 101, 155, 201, 103, 116, 200, 27, 233, 69, 91, 254, 64, 104, 193, 132, 164, 65, 0, 24, 13, 139, 181, 248, 227, 60, 42, 81, 175, 86, 138, 32, 22, 144, 58, 47, 90, 5, 51, 228}; uint8_t data[] = {10,20,30}; rc4_crypt(s,data,0); if (data[0]!=10||data[1]!=20||data[2]!=30) return 1; return 0; }\n",
        # single-byte stream from first S-box state (same key schedule as case 0)
        "\nint main() { uint8_t s[256] = {194, 82, 8, 12, 50, 235, 33, 44, 251, 165, 149, 141, 87, 163, 119, 188, 19, 161, 11, 57, 226, 249, 180, 45, 156, 114, 107, 130, 2, 49, 231, 9, 43, 253, 25, 127, 10, 203, 244, 109, 72, 215, 108, 26, 204, 176, 95, 54, 77, 128, 36, 191, 38, 134, 75, 123, 216, 205, 131, 4, 16, 93, 15, 59, 55, 14, 71, 96, 179, 250, 133, 243, 122, 105, 151, 168, 174, 221, 214, 79, 210, 172, 80, 41, 173, 17, 74, 142, 106, 73, 135, 129, 126, 150, 146, 177, 40, 21, 245, 222, 147, 89, 162, 117, 92, 197, 63, 189, 160, 153, 220, 3, 195, 100, 171, 56, 112, 213, 167, 20, 186, 184, 84, 241, 52, 219, 124, 83, 209, 182, 166, 185, 6, 110, 207, 88, 240, 223, 140, 62, 159, 29, 46, 234, 113, 125, 35, 152, 202, 178, 218, 239, 118, 158, 94, 67, 120, 183, 212, 255, 187, 230, 28, 170, 238, 217, 68, 31, 97, 246, 102, 206, 232, 70, 145, 99, 148, 48, 247, 237, 208, 85, 137, 169, 23, 39, 136, 111, 157, 37, 236, 224, 199, 154, 1, 30, 190, 7, 98, 76, 196, 211, 229, 53, 225, 61, 78, 192, 143, 198, 242, 121, 66, 18, 252, 115, 34, 101, 155, 201, 103, 116, 200, 27, 233, 69, 91, 254, 64, 104, 193, 132, 164, 65, 0, 24, 13, 139, 181, 248, 227, 60, 42, 81, 175, 86, 138, 32, 22, 144, 58, 47, 90, 5, 51, 228}; uint8_t data[] = {255}; rc4_crypt(s,data,1); if (data[0]!=227) return 1; return 0; }\n",
    ],
    "crc32": [
        "\nint main() { uint8_t d[] = {10,20,30}; if (crc32(d,3) != 0x2677b6f2u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {0}; if (crc32(d,0) != 0u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {'1','2','3','4','5','6','7','8','9'}; if (crc32(d,9) != 0xcbf43926u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {0}; if (crc32(d,1) != 0xd202ef8du) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {255}; if (crc32(d,1) != 0xff000000u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {1,2,3}; if (crc32(d,3) != 0x55bc801du) return 1; return 0; }\n",
    ],
    "sum_array": [
        "\nint main() { int a[] = {1,2,3,4,5}; if (sum_array(a,5) != 15) return 1; return 0; }\n",
        "\nint main() { int a[] = {0}; if (sum_array(a,1) != 0) return 1; return 0; }\n",              # single zero
        "\nint main() { int a[] = {42}; if (sum_array(a,1) != 42) return 1; return 0; }\n",            # single element
        "\nint main() { int a[] = {-1,-2,-3}; if (sum_array(a,3) != -6) return 1; return 0; }\n",     # all negative
        "\nint main() { int a[] = {100,200,300}; if (sum_array(a,3) != 600) return 1; return 0; }\n",
    ],
    "reverse_in_place": [
        "\nint main() { int a[] = {1,2,3,4,5}; if (reverse_in_place(a,5)!=5) return 1; if (a[0]!=5||a[4]!=1) return 2; return 0; }\n",
        "\nint main() { int a[] = {1}; reverse_in_place(a,1); if (a[0]!=1) return 1; return 0; }\n",   # single element
        "\nint main() { int a[] = {2,1}; reverse_in_place(a,2); if (a[0]!=1||a[1]!=2) return 1; return 0; }\n",  # two elements
        "\nint main() { int a[] = {1,2,3,4}; reverse_in_place(a,4); if (a[0]!=4||a[3]!=1) return 1; return 0; }\n",  # even count
        "\nint main() { int a[] = {5,5,5}; reverse_in_place(a,3); if (a[0]!=5||a[1]!=5||a[2]!=5) return 1; return 0; }\n",  # all same
    ],
    "find_pair_value": [
        "\nint main() { Pair p[] = {{1,10},{2,20},{3,30}}; if (find_pair_value(p,3,2)!=20) return 1; return 0; }\n",
        "\nint main() { Pair p[] = {{1,10},{2,20},{3,30}}; if (find_pair_value(p,3,4)!=-1) return 1; return 0; }\n",
        "\nint main() { Pair p[] = {{1,10}}; if (find_pair_value(p,1,1)!=10) return 1; return 0; }\n",  # single entry found
        "\nint main() { Pair p[] = {{1,10}}; if (find_pair_value(p,1,2)!=-1) return 1; return 0; }\n", # single entry not found
        "\nint main() { Pair p[] = {{1,10},{2,20},{3,30}}; if (find_pair_value(p,3,1)!=10) return 1; return 0; }\n",  # first element
    ],
    "accumulate_pairs": [
        "\nint main() { Pair p[] = {{1,5},{2,10},{3,15}}; if (accumulate_pairs(p,3)!=70) return 1; return 0; }\n",
        "\nint main() { Pair p[] = {{1,0}}; if (accumulate_pairs(p,1)!=0) return 1; return 0; }\n",    # zero value
        "\nint main() { Pair p[] = {{2,3}}; if (accumulate_pairs(p,1)!=6) return 1; return 0; }\n",   # single pair
        "\nint main() { Pair p[] = {{1,1},{2,2}}; if (accumulate_pairs(p,2)!=5) return 1; return 0; }\n",  # two pairs: 1*1 + 2*2 = 5
        "\nint main() { Pair p[] = {{3,0},{0,5}}; if (accumulate_pairs(p,2)!=0) return 1; return 0; }\n",  # zeros: 3*0 + 0*5 = 0
    ],
    "pointer_stride_sum": [
        "\nint main() { int a[] = {1,2,3,4,5,6,7}; if (pointer_stride_sum(a,7)!=16) return 1; return 0; }\n",
        "\nint main() { int a[] = {1}; if (pointer_stride_sum(a,1)!=1) return 1; return 0; }\n",       # single element
        "\nint main() { int a[] = {5,10}; if (pointer_stride_sum(a,2)!=5) return 1; return 0; }\n",    # two elements, stride picks first
        "\nint main() { int a[] = {2,99,4,99,6}; if (pointer_stride_sum(a,5)!=12) return 1; return 0; }\n",  # stride=2: 2+4+6=12
        "\nint main() { int a[] = {0,0,0,0}; if (pointer_stride_sum(a,4)!=0) return 1; return 0; }\n", # all zeros
    ],
    "reverse_string": [
        "\nint main() { char s[] = \"hello\"; reverse_string(s, 5); if (s[0]!='o'||s[1]!='l'||s[2]!='l'||s[3]!='e'||s[4]!='h') return 1; return 0; }\n",
        "\nint main() { char s[] = \"a\"; reverse_string(s, 1); if (s[0]!='a') return 1; return 0; }\n",  # single char
        "\nint main() { char s[] = \"ab\"; reverse_string(s, 2); if (s[0]!='b'||s[1]!='a') return 1; return 0; }\n",  # two chars
        "\nint main() { char s[] = \"abcd\"; reverse_string(s, 0); if (s[0]!='a'||s[3]!='d') return 1; return 0; }\n",  # length 0 no-op
        "\nint main() { char s[] = \"racecar\"; reverse_string(s, 7); if (s[0]!='r'||s[3]!='e'||s[6]!='r') return 1; return 0; }\n",  # palindrome
    ],
    "find_substring": [
        "\nint main() { if (find_substring(\"hello world\", \"world\") != 6) return 1; return 0; }\n",
        "\nint main() { if (find_substring(\"hello\", \"xyz\") != -1) return 1; return 0; }\n",  # not found
        "\nint main() { if (find_substring(\"hello\", \"\") != 0) return 1; return 0; }\n",  # empty needle
        "\nint main() { if (find_substring(\"abcabc\", \"abc\") != 0) return 1; return 0; }\n",  # first match
        "\nint main() { if (find_substring(\"abcdef\", \"def\") != 3) return 1; return 0; }\n",  # suffix
        "\nint main() { if (find_substring(\"\", \"a\") != -1) return 1; return 0; }\n",  # empty haystack
    ],
    # Return value is privilege_level + (is_admin ? 100 : 0), not the raw val.
    "manipulate_bitfields": [
        "\nint main() { struct ConfigNode n = {0}; if (manipulate_bitfields(&n, 42) != 10) return 1; if (n.flags.is_active != 1) return 2; if (n.val.int_val != 42) return 3; return 0; }\n",
        "\nint main() { struct ConfigNode n = {0}; if (manipulate_bitfields(&n, 101) != 105) return 1; if (n.flags.is_admin != 1) return 2; return 0; }\n",  # admin path
        "\nint main() { struct ConfigNode n = {0}; if (manipulate_bitfields(&n, 0) != 0) return 1; if (n.flags.is_admin != 0) return 2; return 0; }\n",  # zero
        "\nint main() { struct ConfigNode n = {0}; if (manipulate_bitfields(&n, 15) != 15) return 1; if (n.flags.privilege_level != 15) return 2; return 0; }\n",  # max nibble
        "\nint main() { struct ConfigNode n = {0}; if (manipulate_bitfields(&n, 100) != 4) return 1; if (n.flags.is_admin != 0) return 2; return 0; }\n",  # boundary not admin
    ],
    "matrix_multiply": [
        "\nint main() { float a[]={1,2,3,4}; float b[]={1,0,0,1}; float c[4]={0}; matrix_multiply(a,b,c,2); if (c[0]!=1||c[1]!=2||c[2]!=3||c[3]!=4) return 1; return 0; }\n",  # identity
        "\nint main() { float a[]={1,2,3,4}; float b[]={5,6,7,8}; float c[4]={0}; matrix_multiply(a,b,c,2); if (c[0]!=19||c[1]!=22||c[2]!=43||c[3]!=50) return 1; return 0; }\n",
        "\nint main() { float a[]={2}; float b[]={3}; float c[1]={0}; matrix_multiply(a,b,c,1); if (c[0]!=6) return 1; return 0; }\n",  # 1x1
        "\nint main() { float a[]={0,0,0,0}; float b[]={1,2,3,4}; float c[4]={9,9,9,9}; matrix_multiply(a,b,c,2); if (c[0]!=0||c[1]!=0||c[2]!=0||c[3]!=0) return 1; return 0; }\n",  # zero A
        "\nint main() { float a[]={1,0,0,1}; float b[]={9,8,7,6}; float c[4]={0}; matrix_multiply(a,b,c,2); if (c[0]!=9||c[1]!=8||c[2]!=7||c[3]!=6) return 1; return 0; }\n",  # identity A
    ],
    "rolling_hash32": [
        "\nint main() { uint8_t d[] = {99}; if (rolling_hash32(d,0,0) != 0x9e3779b9u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {0}; if (rolling_hash32(d,1,0) != 0x45f165c1u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {1,2,3,4}; if (rolling_hash32(d,4,0) != 0xfb41438fu) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {'a','b','c'}; if (rolling_hash32(d,3,0x12345678u) != 0x8e9e445cu) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {255,0,128,64}; if (rolling_hash32(d,4,0xffffffffu) != 0xe7efa1deu) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}; if (rolling_hash32(d,16,7) != 0x96e1db7du) return 1; return 0; }\n",
    ],
    "bounded_tlv_sum": [
        "\nint main() { uint8_t d[] = {99}; if (bounded_tlv_sum(d,0) != 0u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {1}; if (bounded_tlv_sum(d,1) != 0u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {1,0}; if (bounded_tlv_sum(d,2) != 0x100u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {1,2,3,4}; if (bounded_tlv_sum(d,4) != 0x107u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {1,2,3,4,2,1,5}; if (bounded_tlv_sum(d,7) != 0x30cu) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {7,3,1,2}; if (bounded_tlv_sum(d,4) != 0u) return 1; return 0; }\n",
        "\nint main() { uint8_t d[] = {255,1,255,2,2,128,129}; if (bounded_tlv_sum(d,7) != 0x10300u) return 1; return 0; }\n",
    ],
    "state_machine_score": [
        "\nint main() { uint8_t e[] = {0}; if (state_machine_score(e,0) != 0) return 1; return 0; }\n",
        "\nint main() { uint8_t e[] = {1}; if (state_machine_score(e,1) != 1) return 1; return 0; }\n",
        "\nint main() { uint8_t e[] = {1,2}; if (state_machine_score(e,2) != 5) return 1; return 0; }\n",
        "\nint main() { uint8_t e[] = {1,2,3}; if (state_machine_score(e,3) != 10) return 1; return 0; }\n",
        "\nint main() { uint8_t e[] = {3,2,1}; if (state_machine_score(e,3) != -4) return 1; return 0; }\n",
        "\nint main() { uint8_t e[] = {1,1,2,3}; if (state_machine_score(e,4) != 9) return 1; return 0; }\n",
        "\nint main() { uint8_t e[] = {1,2,9,1,2,3}; if (state_machine_score(e,6) != 12) return 1; return 0; }\n",
    ],
    "overlap_move": [
        "\nint main() { uint8_t b[] = {0,1,2,3}; if (overlap_move(b,1,0,0) != 0) return 1; if (b[0]!=0||b[1]!=1||b[2]!=2||b[3]!=3) return 2; return 0; }\n",
        "\nint main() { uint8_t b[] = {0,1,2,3}; if (overlap_move(b,1,1,3) != 3) return 1; if (b[0]!=0||b[1]!=1||b[2]!=2||b[3]!=3) return 2; return 0; }\n",
        "\nint main() { uint8_t b[] = {0,1,2,3,4,5,6,7}; if (overlap_move(b,0,4,3) != 3) return 1; if (b[0]!=4||b[1]!=5||b[2]!=6||b[3]!=3||b[4]!=4||b[5]!=5||b[6]!=6||b[7]!=7) return 2; return 0; }\n",
        "\nint main() { uint8_t b[] = {'a','b','c','d','e','f'}; if (overlap_move(b,0,2,4) != 4) return 1; if (b[0]!='c'||b[1]!='d'||b[2]!='e'||b[3]!='f'||b[4]!='e'||b[5]!='f') return 2; return 0; }\n",
        "\nint main() { uint8_t b[] = {'a','b','c','d','e','f'}; if (overlap_move(b,2,0,4) != 4) return 1; if (b[0]!='a'||b[1]!='b'||b[2]!='a'||b[3]!='b'||b[4]!='c'||b[5]!='d') return 2; return 0; }\n",
        "\nint main() { uint8_t b[] = {1,2,3,4,5,6}; if (overlap_move(b,1,0,5) != 5) return 1; if (b[0]!=1||b[1]!=1||b[2]!=2||b[3]!=3||b[4]!=4||b[5]!=5) return 2; return 0; }\n",
    ],
    "mixed_width_accumulate": [
        "\nint main() { int16_t v[] = {99}; if (mixed_width_accumulate(v,0,5) != 5) return 1; return 0; }\n",
        "\nint main() { int16_t v[] = {0}; if (mixed_width_accumulate(v,1,0) != 0) return 1; return 0; }\n",
        "\nint main() { int16_t v[] = {1,2,3}; if (mixed_width_accumulate(v,3,0) != 12) return 1; return 0; }\n",
        "\nint main() { int16_t v[] = {-1,-2,-3}; if (mixed_width_accumulate(v,3,0) != 6) return 1; return 0; }\n",
        "\nint main() { int16_t v[] = {-32768,32767}; if (mixed_width_accumulate(v,2,10) != 98312) return 1; return 0; }\n",
        "\nint main() { int16_t v[] = {-3,4,-5,6}; if (mixed_width_accumulate(v,4,10) != 38) return 1; return 0; }\n",
    ],
    "rotate_words": [
        "\nint main() { uint32_t v[] = {99}; if (rotate_words(v,0,1) != 0u) return 1; if (v[0]!=99u) return 2; return 0; }\n",
        "\nint main() { uint32_t v[] = {0}; if (rotate_words(v,1,0) != 0u) return 1; if (v[0]!=0u) return 2; return 0; }\n",
        "\nint main() { uint32_t v[] = {0x12345678u}; if (rotate_words(v,1,4) != 0x23456781u) return 1; if (v[0]!=0x23456781u) return 2; return 0; }\n",
        "\nint main() { uint32_t v[] = {0x80000001u}; if (rotate_words(v,1,1) != 3u) return 1; if (v[0]!=3u) return 2; return 0; }\n",
        "\nint main() { uint32_t v[] = {0xdeadbeefu,0x01020304u}; if (rotate_words(v,2,8) != 0xafbdebdcu) return 1; if (v[0]!=0xadbeefdeu||v[1]!=0x02030401u) return 2; return 0; }\n",
        "\nint main() { uint32_t v[] = {0xffffffffu,0u,1u}; if (rotate_words(v,3,33) != 0xfffffffau) return 1; if (v[0]!=0xffffffffu||v[1]!=0u||v[2]!=2u) return 2; return 0; }\n",
    ],
    # advanced_patterns.c — list / struct / indirect call / stride
    "list_sum": [
        "\nint main() { if (list_sum(0) != 0) return 1; return 0; }\n",
        "\nint main() { Node c={3,0}; Node b={2,&c}; Node a={1,&b}; if (list_sum(&a) != 6) return 1; return 0; }\n",
        "\nint main() { Node a={-5,0}; if (list_sum(&a) != -5) return 1; return 0; }\n",
        "\nint main() { Node d={4,0}; Node c={3,&d}; Node b={2,&c}; Node a={1,&b}; if (list_sum(&a) != 10) return 1; return 0; }\n",
        "\nint main() { Node b={0,0}; Node a={0,&b}; if (list_sum(&a) != 0) return 1; return 0; }\n",
    ],
    "kv_lookup": [
        "\nint main() { Kv t[]={{1,10},{2,20}}; if (kv_lookup(t,2,1) != 10) return 1; return 0; }\n",
        "\nint main() { Kv t[]={{1,10},{2,20},{3,30}}; if (kv_lookup(t,3,2) != 20) return 1; return 0; }\n",
        "\nint main() { Kv t[]={{1,10},{2,20}}; if (kv_lookup(t,2,99) != -1) return 1; return 0; }\n",
        "\nint main() { Kv t[]={{7,0}}; if (kv_lookup(t,1,7) != 0) return 1; return 0; }\n",
        "\nint main() { if (kv_lookup(0,0,1) != -1) return 1; return 0; }\n",
        "\nint main() { Kv t[]={{-1,-9},{0,5}}; if (kv_lookup(t,2,-1) != -9) return 1; return 0; }\n",
    ],
    # Cast fn pointers through integer: recovered signatures often use ulonglong
    # for the first param (register CallInd carrier) rather than a C function type.
    "apply_binop": [
        "\nint main() { if (apply_binop(0, 3, 4) != 0) return 1; return 0; }\n",
        "\nint main() { if (apply_binop((ulonglong)(uintptr_t)bench_add_ints, 3, 4) != 7) return 1; return 0; }\n",
        "\nint main() { if (apply_binop((ulonglong)(uintptr_t)bench_mul_ints, 2, 5) != 10) return 1; return 0; }\n",
        "\nint main() { if (apply_binop((ulonglong)(uintptr_t)bench_add_ints, -3, 8) != 5) return 1; return 0; }\n",
        "\nint main() { if (apply_binop((ulonglong)(uintptr_t)bench_mul_ints, -2, -4) != 8) return 1; return 0; }\n",
        "\nint main() { if (apply_binop((ulonglong)(uintptr_t)bench_add_ints, 0, 0) != 0) return 1; return 0; }\n",
    ],
    "add_ints": [
        "\nint main() { if (add_ints(1, 2) != 3) return 1; return 0; }\n",
        "\nint main() { if (add_ints(-1, 1) != 0) return 1; return 0; }\n",
        "\nint main() { if (add_ints(100, 200) != 300) return 1; return 0; }\n",
        "\nint main() { if (add_ints(0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (add_ints(-5, -7) != -12) return 1; return 0; }\n",
    ],
    "mul_ints": [
        "\nint main() { if (mul_ints(2, 3) != 6) return 1; return 0; }\n",
        "\nint main() { if (mul_ints(-2, 3) != -6) return 1; return 0; }\n",
        "\nint main() { if (mul_ints(0, 99) != 0) return 1; return 0; }\n",
        "\nint main() { if (mul_ints(7, 1) != 7) return 1; return 0; }\n",
        "\nint main() { if (mul_ints(-4, -5) != 20) return 1; return 0; }\n",
    ],
    "dot_product_stride": [
        "\nint main() { int a[]={1,2,3,4}; int b[]={5,6,7,8}; if (dot_product_stride(a,b,2,2) != 70) return 1; return 0; }\n",
        "\nint main() { int a[]={1}; int b[]={9}; if (dot_product_stride(a,b,1,1) != 9) return 1; return 0; }\n",
        "\nint main() { int a[]={0,0,0,0}; int b[]={1,2,3,4}; if (dot_product_stride(a,b,2,2) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={1,0,0,1}; int b[]={2,0,0,3}; if (dot_product_stride(a,b,2,2) != 5) return 1; return 0; }\n",
        "\nint main() { int a[]={-1,2}; int b[]={3,-4}; if (dot_product_stride(a,b,1,2) != -3) return 1; return 0; }\n",
    ],
    "bounded_checksum": [
        "\nint main() { unsigned char p[]={1,2,3}; if (bounded_checksum(p,3,0) != 0u) return 1; return 0; }\n",
        "\nint main() { unsigned char p[]={1,2,3}; if (bounded_checksum(p,3,1) != 1u) return 1; return 0; }\n",
        "\nint main() { unsigned char p[]={1,2,3}; if (bounded_checksum(p,3,3) != 1158u) return 1; return 0; }\n",
        "\nint main() { unsigned char p[]={1,2,3,4,5}; if (bounded_checksum(p,5,3) != 1158u) return 1; return 0; }\n",
        "\nint main() { unsigned char p[]={0}; if (bounded_checksum(p,1,1) != 0u) return 1; return 0; }\n",
        "\nint main() { unsigned char p[]={10,20}; if (bounded_checksum(p,2,2) != 350u) return 1; return 0; }\n",
    ],
    # realworld util_lib.c
    "util_hash": [
        "\nint main() { if (util_hash(0) != 0u) return 1; return 0; }\n",
        "\nint main() { if (util_hash(\"\") != 2166136261u) return 1; return 0; }\n",
        "\nint main() { if (util_hash(\"a\") != 3826002220u) return 1; return 0; }\n",
        "\nint main() { uint32_t h=util_hash(\"ab\"); if (h==0u) return 1; return 0; }\n",
        "\nint main() { if (util_hash(\"a\") == util_hash(\"b\")) return 1; return 0; }\n",
    ],
    "util_clamp": [
        "\nint main() { if (util_clamp(5,0,10) != 5) return 1; return 0; }\n",
        "\nint main() { if (util_clamp(-1,0,10) != 0) return 1; return 0; }\n",
        "\nint main() { if (util_clamp(99,0,10) != 10) return 1; return 0; }\n",
        "\nint main() { if (util_clamp(0,0,10) != 0) return 1; return 0; }\n",
        "\nint main() { if (util_clamp(10,0,10) != 10) return 1; return 0; }\n",
        "\nint main() { if (util_clamp(-100,-5,5) != -5) return 1; return 0; }\n",
    ],
    "util_count_bits": [
        "\nint main() { if (util_count_bits(0u) != 0) return 1; return 0; }\n",
        "\nint main() { if (util_count_bits(1u) != 1) return 1; return 0; }\n",
        "\nint main() { if (util_count_bits(0xffffffffu) != 32) return 1; return 0; }\n",
        "\nint main() { if (util_count_bits(0x0fu) != 4) return 1; return 0; }\n",
        "\nint main() { if (util_count_bits(0x80000000u) != 1) return 1; return 0; }\n",
        "\nint main() { if (util_count_bits(0xaaaaaaaau) != 16) return 1; return 0; }\n",
    ],
    # C++ PE family (extern "C" exports; C++ body)
    "cpp_add_ints": [
        "\nint main() { if (cpp_add_ints(1, 2) != 3) return 1; return 0; }\n",
        "\nint main() { if (cpp_add_ints(0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (cpp_add_ints(-5, 5) != 0) return 1; return 0; }\n",
        "\nint main() { if (cpp_add_ints(100, -30) != 70) return 1; return 0; }\n",
        "\nint main() { if (cpp_add_ints(-1, -1) != -2) return 1; return 0; }\n",
        "\nint main() { if (cpp_add_ints(2147483646, 1) != 2147483647) return 1; return 0; }\n",
    ],
    "cpp_clamp_int": [
        "\nint main() { if (cpp_clamp_int(5, 0, 10) != 5) return 1; return 0; }\n",
        "\nint main() { if (cpp_clamp_int(-1, 0, 10) != 0) return 1; return 0; }\n",
        "\nint main() { if (cpp_clamp_int(99, 0, 10) != 10) return 1; return 0; }\n",
        "\nint main() { if (cpp_clamp_int(0, 0, 10) != 0) return 1; return 0; }\n",
        "\nint main() { if (cpp_clamp_int(10, 0, 10) != 10) return 1; return 0; }\n",
        "\nint main() { if (cpp_clamp_int(-100, -5, 5) != -5) return 1; return 0; }\n",
    ],
    "cpp_max3": [
        "\nint main() { if (cpp_max3(1, 2, 3) != 3) return 1; return 0; }\n",
        "\nint main() { if (cpp_max3(9, 1, 2) != 9) return 1; return 0; }\n",
        "\nint main() { if (cpp_max3(0, 0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (cpp_max3(-1, -5, -3) != -1) return 1; return 0; }\n",
        "\nint main() { if (cpp_max3(5, 5, 1) != 5) return 1; return 0; }\n",
        "\nint main() { if (cpp_max3(1, 100, 50) != 100) return 1; return 0; }\n",
    ],
    "cpp_count_bits": [
        "\nint main() { if (cpp_count_bits(0u) != 0u) return 1; return 0; }\n",
        "\nint main() { if (cpp_count_bits(1u) != 1u) return 1; return 0; }\n",
        "\nint main() { if (cpp_count_bits(0xffffffffu) != 32u) return 1; return 0; }\n",
        "\nint main() { if (cpp_count_bits(0x0fu) != 4u) return 1; return 0; }\n",
        "\nint main() { if (cpp_count_bits(0x80000000u) != 1u) return 1; return 0; }\n",
        "\nint main() { if (cpp_count_bits(0xaaaaaaaau) != 16u) return 1; return 0; }\n",
    ],
    "cpp_dot_product": [
        "\nint main() { int a[]={1,2,3}; int b[]={4,5,6}; if (cpp_dot_product(a,b,3) != 32) return 1; return 0; }\n",
        "\nint main() { int a[]={0,0}; int b[]={1,2}; if (cpp_dot_product(a,b,2) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={1}; int b[]={7}; if (cpp_dot_product(a,b,1) != 7) return 1; return 0; }\n",
        "\nint main() { int a[]={-1,2}; int b[]={3,-4}; if (cpp_dot_product(a,b,2) != -11) return 1; return 0; }\n",
        "\nint main() { int a[]={1,1,1,1}; int b[]={1,1,1,1}; if (cpp_dot_product(a,b,4) != 4) return 1; return 0; }\n",
        "\nint main() { if (cpp_dot_product(0,0,0) != 0) return 1; return 0; }\n",
    ],
    "cpp_cstr_len": [
        "\nint main() { if (cpp_cstr_len(\"\") != 0) return 1; return 0; }\n",
        "\nint main() { if (cpp_cstr_len(\"a\") != 1) return 1; return 0; }\n",
        "\nint main() { if (cpp_cstr_len(\"hi\") != 2) return 1; return 0; }\n",
        "\nint main() { if (cpp_cstr_len(\"hello\") != 5) return 1; return 0; }\n",
        "\nint main() { if (cpp_cstr_len(0) != 0) return 1; return 0; }\n",
        "\nint main() { if (cpp_cstr_len(\"x\") == cpp_cstr_len(\"xy\")) return 1; return 0; }\n",
    ],
    "cpp_sum_range": [
        "\nint main() { int a[]={1,2,3}; if (cpp_sum_range(a,3) != 6) return 1; return 0; }\n",
        "\nint main() { int a[]={0}; if (cpp_sum_range(a,1) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={-1,1}; if (cpp_sum_range(a,2) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={5,5,5,5}; if (cpp_sum_range(a,4) != 20) return 1; return 0; }\n",
        "\nint main() { if (cpp_sum_range(0,0) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={10,-3,1}; if (cpp_sum_range(a,3) != 8) return 1; return 0; }\n",
    ],
    # Rust PE family (no_mangle extern "C")
    "rust_add_ints": [
        "\nint main() { if (rust_add_ints(1, 2) != 3) return 1; return 0; }\n",
        "\nint main() { if (rust_add_ints(0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (rust_add_ints(-5, 5) != 0) return 1; return 0; }\n",
        "\nint main() { if (rust_add_ints(100, -30) != 70) return 1; return 0; }\n",
        "\nint main() { if (rust_add_ints(-1, -1) != -2) return 1; return 0; }\n",
        "\nint main() { if (rust_add_ints(2147483646, 1) != 2147483647) return 1; return 0; }\n",
    ],
    "rust_clamp_int": [
        "\nint main() { if (rust_clamp_int(5, 0, 10) != 5) return 1; return 0; }\n",
        "\nint main() { if (rust_clamp_int(-1, 0, 10) != 0) return 1; return 0; }\n",
        "\nint main() { if (rust_clamp_int(99, 0, 10) != 10) return 1; return 0; }\n",
        "\nint main() { if (rust_clamp_int(0, 0, 10) != 0) return 1; return 0; }\n",
        "\nint main() { if (rust_clamp_int(10, 0, 10) != 10) return 1; return 0; }\n",
        "\nint main() { if (rust_clamp_int(-100, -5, 5) != -5) return 1; return 0; }\n",
    ],
    "rust_max3": [
        "\nint main() { if (rust_max3(1, 2, 3) != 3) return 1; return 0; }\n",
        "\nint main() { if (rust_max3(9, 1, 2) != 9) return 1; return 0; }\n",
        "\nint main() { if (rust_max3(0, 0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (rust_max3(-1, -5, -3) != -1) return 1; return 0; }\n",
        "\nint main() { if (rust_max3(5, 5, 1) != 5) return 1; return 0; }\n",
        "\nint main() { if (rust_max3(1, 100, 50) != 100) return 1; return 0; }\n",
    ],
    "rust_count_bits": [
        "\nint main() { if (rust_count_bits(0u) != 0u) return 1; return 0; }\n",
        "\nint main() { if (rust_count_bits(1u) != 1u) return 1; return 0; }\n",
        "\nint main() { if (rust_count_bits(0xffffffffu) != 32u) return 1; return 0; }\n",
        "\nint main() { if (rust_count_bits(0x0fu) != 4u) return 1; return 0; }\n",
        "\nint main() { if (rust_count_bits(0x80000000u) != 1u) return 1; return 0; }\n",
        "\nint main() { if (rust_count_bits(0xaaaaaaaau) != 16u) return 1; return 0; }\n",
    ],
    "rust_dot_product": [
        "\nint main() { int a[]={1,2,3}; int b[]={4,5,6}; if (rust_dot_product(a,b,3) != 32) return 1; return 0; }\n",
        "\nint main() { int a[]={0,0}; int b[]={1,2}; if (rust_dot_product(a,b,2) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={1}; int b[]={7}; if (rust_dot_product(a,b,1) != 7) return 1; return 0; }\n",
        "\nint main() { int a[]={-1,2}; int b[]={3,-4}; if (rust_dot_product(a,b,2) != -11) return 1; return 0; }\n",
        "\nint main() { int a[]={1,1,1,1}; int b[]={1,1,1,1}; if (rust_dot_product(a,b,4) != 4) return 1; return 0; }\n",
        "\nint main() { if (rust_dot_product(0,0,0) != 0) return 1; return 0; }\n",
    ],
    "rust_cstr_len": [
        "\nint main() { if (rust_cstr_len(\"\") != 0) return 1; return 0; }\n",
        "\nint main() { if (rust_cstr_len(\"a\") != 1) return 1; return 0; }\n",
        "\nint main() { if (rust_cstr_len(\"hi\") != 2) return 1; return 0; }\n",
        "\nint main() { if (rust_cstr_len(\"hello\") != 5) return 1; return 0; }\n",
        "\nint main() { if (rust_cstr_len(0) != 0) return 1; return 0; }\n",
        "\nint main() { if (rust_cstr_len(\"x\") == rust_cstr_len(\"xy\")) return 1; return 0; }\n",
    ],
    "rust_sum_range": [
        "\nint main() { int a[]={1,2,3}; if (rust_sum_range(a,3) != 6) return 1; return 0; }\n",
        "\nint main() { int a[]={0}; if (rust_sum_range(a,1) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={-1,1}; if (rust_sum_range(a,2) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={5,5,5,5}; if (rust_sum_range(a,4) != 20) return 1; return 0; }\n",
        "\nint main() { if (rust_sum_range(0,0) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={10,-3,1}; if (rust_sum_range(a,3) != 8) return 1; return 0; }\n",
    ],
    "rust_saturating_add": [
        "\nint main() { if (rust_saturating_add(1, 2) != 3) return 1; return 0; }\n",
        "\nint main() { if (rust_saturating_add(0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (rust_saturating_add(-1, -1) != -2) return 1; return 0; }\n",
        "\nint main() { if (rust_saturating_add(2147483647, 1) != 2147483647) return 1; return 0; }\n",
        "\nint main() { if (rust_saturating_add(-2147483647-1, -1) != (-2147483647-1)) return 1; return 0; }\n",
        "\nint main() { if (rust_saturating_add(100, -30) != 70) return 1; return 0; }\n",
    ],
    # Go PE family (CGO //export)
    "go_add_ints": [
        "\nint main() { if (go_add_ints(1, 2) != 3) return 1; return 0; }\n",
        "\nint main() { if (go_add_ints(0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (go_add_ints(-5, 5) != 0) return 1; return 0; }\n",
        "\nint main() { if (go_add_ints(100, -30) != 70) return 1; return 0; }\n",
        "\nint main() { if (go_add_ints(-1, -1) != -2) return 1; return 0; }\n",
        "\nint main() { if (go_add_ints(2147483646, 1) != 2147483647) return 1; return 0; }\n",
    ],
    "go_clamp_int": [
        "\nint main() { if (go_clamp_int(5, 0, 10) != 5) return 1; return 0; }\n",
        "\nint main() { if (go_clamp_int(-1, 0, 10) != 0) return 1; return 0; }\n",
        "\nint main() { if (go_clamp_int(99, 0, 10) != 10) return 1; return 0; }\n",
        "\nint main() { if (go_clamp_int(0, 0, 10) != 0) return 1; return 0; }\n",
        "\nint main() { if (go_clamp_int(10, 0, 10) != 10) return 1; return 0; }\n",
        "\nint main() { if (go_clamp_int(-100, -5, 5) != -5) return 1; return 0; }\n",
    ],
    "go_max3": [
        "\nint main() { if (go_max3(1, 2, 3) != 3) return 1; return 0; }\n",
        "\nint main() { if (go_max3(9, 1, 2) != 9) return 1; return 0; }\n",
        "\nint main() { if (go_max3(0, 0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (go_max3(-1, -5, -3) != -1) return 1; return 0; }\n",
        "\nint main() { if (go_max3(5, 5, 1) != 5) return 1; return 0; }\n",
        "\nint main() { if (go_max3(1, 100, 50) != 100) return 1; return 0; }\n",
    ],
    "go_count_bits": [
        "\nint main() { if (go_count_bits(0u) != 0u) return 1; return 0; }\n",
        "\nint main() { if (go_count_bits(1u) != 1u) return 1; return 0; }\n",
        "\nint main() { if (go_count_bits(0xffffffffu) != 32u) return 1; return 0; }\n",
        "\nint main() { if (go_count_bits(0x0fu) != 4u) return 1; return 0; }\n",
        "\nint main() { if (go_count_bits(0x80000000u) != 1u) return 1; return 0; }\n",
        "\nint main() { if (go_count_bits(0xaaaaaaaau) != 16u) return 1; return 0; }\n",
    ],
    "go_dot_product": [
        "\nint main() { int a[]={1,2,3}; int b[]={4,5,6}; if (go_dot_product(a,b,3) != 32) return 1; return 0; }\n",
        "\nint main() { int a[]={0,0}; int b[]={1,2}; if (go_dot_product(a,b,2) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={1}; int b[]={7}; if (go_dot_product(a,b,1) != 7) return 1; return 0; }\n",
        "\nint main() { int a[]={-1,2}; int b[]={3,-4}; if (go_dot_product(a,b,2) != -11) return 1; return 0; }\n",
        "\nint main() { int a[]={1,1,1,1}; int b[]={1,1,1,1}; if (go_dot_product(a,b,4) != 4) return 1; return 0; }\n",
        "\nint main() { if (go_dot_product(0,0,0) != 0) return 1; return 0; }\n",
    ],
    "go_cstr_len": [
        "\nint main() { if (go_cstr_len(\"\") != 0) return 1; return 0; }\n",
        "\nint main() { if (go_cstr_len(\"a\") != 1) return 1; return 0; }\n",
        "\nint main() { if (go_cstr_len(\"hi\") != 2) return 1; return 0; }\n",
        "\nint main() { if (go_cstr_len(\"hello\") != 5) return 1; return 0; }\n",
        "\nint main() { if (go_cstr_len(0) != 0) return 1; return 0; }\n",
        "\nint main() { if (go_cstr_len(\"x\") == go_cstr_len(\"xy\")) return 1; return 0; }\n",
    ],
    "go_sum_range": [
        "\nint main() { int a[]={1,2,3}; if (go_sum_range(a,3) != 6) return 1; return 0; }\n",
        "\nint main() { int a[]={0}; if (go_sum_range(a,1) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={-1,1}; if (go_sum_range(a,2) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={5,5,5,5}; if (go_sum_range(a,4) != 20) return 1; return 0; }\n",
        "\nint main() { if (go_sum_range(0,0) != 0) return 1; return 0; }\n",
        "\nint main() { int a[]={10,-3,1}; if (go_sum_range(a,3) != 8) return 1; return 0; }\n",
    ],
    "go_saturating_add": [
        "\nint main() { if (go_saturating_add(1, 2) != 3) return 1; return 0; }\n",
        "\nint main() { if (go_saturating_add(0, 0) != 0) return 1; return 0; }\n",
        "\nint main() { if (go_saturating_add(-1, -1) != -2) return 1; return 0; }\n",
        "\nint main() { if (go_saturating_add(2147483647, 1) != 2147483647) return 1; return 0; }\n",
        "\nint main() { if (go_saturating_add(-2147483647-1, -1) != (-2147483647-1)) return 1; return 0; }\n",
        "\nint main() { if (go_saturating_add(100, -30) != 70) return 1; return 0; }\n",
    ],
    "file_size": [
        '\nint main() { FILE *f = tmpfile(); if (!f) return 0; fputs("hello", f); rewind(f); if (file_size(f) != 5) return 1; fclose(f); return 0; }\n',
        '\nint main() { FILE *f = tmpfile(); if (!f) return 0; if (file_size(f) != 0) return 1; fclose(f); return 0; }\n',
        "\nint main() { FILE *f = tmpfile(); if (!f) return 0; for (int i = 0; i < 100; i++) fputc('x', f); rewind(f); if (file_size(f) != 100) return 1; fclose(f); return 0; }\n",
        '\nint main() { FILE *f = tmpfile(); if (!f) return 0; fputs("abcdefgh", f); fseek(f, 3, SEEK_SET); if (file_size(f) != 8) return 1; if (ftell(f) != 3) return 1; fclose(f); return 0; }\n',
        "\nint main() { FILE *f = tmpfile(); if (!f) return 0; fputc('z', f); rewind(f); if (file_size(f) != 1) return 1; fclose(f); return 0; }\n",
    ],
    "open_reader": [
        '\nint main() { FILE *f = open_reader("/nonexistent_path_for_semantic_check_xyz"); if (f != NULL) return 1; return 0; }\n',
        '\nint main() { FILE *w = fopen("sem_open_reader_a.tmp", "wb"); if (!w) return 0; fputs("data", w); fclose(w); FILE *f = open_reader("sem_open_reader_a.tmp"); if (f == NULL) return 1; fclose(f); remove("sem_open_reader_a.tmp"); return 0; }\n',
        '\nint main() { FILE *w = fopen("sem_open_reader_b.tmp", "wb"); if (!w) return 0; fclose(w); FILE *f = open_reader("sem_open_reader_b.tmp"); if (f == NULL) return 1; fclose(f); remove("sem_open_reader_b.tmp"); return 0; }\n',
        '\nint main() { FILE *w = fopen("sem_open_reader_c.tmp", "wb"); if (!w) return 0; fputs("xyz", w); fclose(w); FILE *f = open_reader("sem_open_reader_c.tmp"); if (f == NULL) return 1; if (fgetc(f) != \'x\') return 1; fclose(f); remove("sem_open_reader_c.tmp"); return 0; }\n',
        '\nint main() { FILE *f = open_reader(""); if (f != NULL) return 1; return 0; }\n',
    ],
    "count_spaces": [
        '\nint main() { if (count_spaces("a b c") != 2) return 1; return 0; }\n',
        '\nint main() { if (count_spaces("") != 0) return 1; return 0; }\n',
        '\nint main() { if (count_spaces("nospaces") != 0) return 1; return 0; }\n',
        '\nint main() { if (count_spaces("   ") != 3) return 1; return 0; }\n',
        '\nint main() { if (count_spaces(" lead and trail ") != 4) return 1; return 0; }\n',
        '\nint main() { if (count_spaces("\\tno\\nspace\\tchars") != 0) return 1; return 0; }\n',
    ],
    "tm_year_of": [
        '\n#include <time.h>\nint main() { struct tm t; memset(&t, 0, sizeof t); t.tm_year = 70; if (tm_year_of(&t) != 1970) return 1; return 0; }\n',
        '\n#include <time.h>\nint main() { struct tm t; memset(&t, 0, sizeof t); t.tm_year = 0; if (tm_year_of(&t) != 1900) return 1; return 0; }\n',
        '\n#include <time.h>\nint main() { struct tm t; memset(&t, 0, sizeof t); t.tm_year = 126; if (tm_year_of(&t) != 2026) return 1; return 0; }\n',
        '\n#include <time.h>\nint main() { struct tm t; memset(&t, 0, sizeof t); t.tm_year = 200; if (tm_year_of(&t) != 2100) return 1; return 0; }\n',
        '\n#include <time.h>\nint main() { struct tm t; memset(&t, 0, sizeof t); t.tm_year = -100; if (tm_year_of(&t) != 1800) return 1; return 0; }\n',
    ],
    "days_between": [
        '\n#include <time.h>\nint main() { if (days_between((time_t)0, (time_t)86400) != 1) return 1; return 0; }\n',
        '\n#include <time.h>\nint main() { if (days_between((time_t)0, (time_t)0) != 0) return 1; return 0; }\n',
        '\n#include <time.h>\nint main() { if (days_between((time_t)0, (time_t)(86400 * 7)) != 7) return 1; return 0; }\n',
        '\n#include <time.h>\nint main() { if (days_between((time_t)86400, (time_t)0) != -1) return 1; return 0; }\n',
        '\n#include <time.h>\nint main() { if (days_between((time_t)0, (time_t)86399) != 0) return 1; return 0; }\n',
    ],
    "quotient_of": [
        '\nint main() { if (quotient_of(17, 5) != 5) return 1; return 0; }\n',
        '\nint main() { if (quotient_of(10, 2) != 5) return 1; return 0; }\n',
        '\nint main() { if (quotient_of(0, 7) != 0) return 1; return 0; }\n',
        '\nint main() { if (quotient_of(7, 10) != 7) return 1; return 0; }\n',
        '\nint main() { if (quotient_of(-17, 5) != -5) return 1; return 0; }\n',
        '\nint main() { if (quotient_of(1, 1) != 1) return 1; return 0; }\n',
    ],
    "make_range": [
        '\nint main() { int *p = make_range(4); if (p == NULL) return 1; for (int i = 0; i < 4; i++) if (p[i] != i) return 1; free(p); return 0; }\n',
        '\nint main() { int *p = make_range(1); if (p == NULL) return 1; if (p[0] != 0) return 1; free(p); return 0; }\n',
        '\nint main() { int *p = make_range(100); if (p == NULL) return 1; if (p[0] != 0 || p[99] != 99) return 1; free(p); return 0; }\n',
        '\nint main() { int *p = make_range(2); if (p == NULL) return 1; if (p[0] != 0 || p[1] != 1) return 1; free(p); return 0; }\n',
        '\nint main() { int *p = make_range(10); if (p == NULL) return 1; int sum = 0; for (int i = 0; i < 10; i++) sum += p[i]; free(p); if (sum != 45) return 1; return 0; }\n',
    ],
    "copy_prefix": [
        '\nint main() { char b[16]; copy_prefix(b, "hello world", 5); if (strcmp(b, "hello") != 0) return 1; return 0; }\n',
        '\nint main() { char b[16]; copy_prefix(b, "abc", 0); if (b[0] != \'\\0\') return 1; return 0; }\n',
        '\nint main() { char b[16]; copy_prefix(b, "abc", 3); if (strcmp(b, "abc") != 0) return 1; return 0; }\n',
        '\nint main() { char b[16]; memset(b, \'Z\', sizeof b); copy_prefix(b, "ab", 2); if (b[2] != \'\\0\') return 1; return 0; }\n',
        '\nint main() { char b[64]; copy_prefix(b, "0123456789abcdef", 16); if (strcmp(b, "0123456789abcdef") != 0) return 1; return 0; }\n',
    ],
    "read_line": [
        '\nint main() { char buf[32]; FILE *f = tmpfile(); if (!f) return 0; fputs("line one\\n", f); rewind(f); char *r = read_line(f, buf, (int)sizeof buf); if (r == NULL) return 1; if (strcmp(r, "line one") != 0) return 1; fclose(f); return 0; }\n',
        '\nint main() { char buf[32]; FILE *f = tmpfile(); if (!f) return 0; rewind(f); char *r = read_line(f, buf, (int)sizeof buf); if (r != NULL) return 1; fclose(f); return 0; }\n',
        '\nint main() { char buf[32]; FILE *f = tmpfile(); if (!f) return 0; fputs("no newline", f); rewind(f); char *r = read_line(f, buf, (int)sizeof buf); if (r == NULL) return 1; if (strcmp(r, "no newline") != 0) return 1; fclose(f); return 0; }\n',
        '\nint main() { char buf[32]; FILE *f = tmpfile(); if (!f) return 0; fputs("\\n", f); rewind(f); char *r = read_line(f, buf, (int)sizeof buf); if (r == NULL) return 1; if (r[0] != \'\\0\') return 1; fclose(f); return 0; }\n',
        '\nint main() { char buf[8]; FILE *f = tmpfile(); if (!f) return 0; fputs("abcdefghij\\n", f); rewind(f); char *r = read_line(f, buf, (int)sizeof buf); if (r == NULL) return 1; if (strcmp(r, "abcdefg") != 0) return 1; fclose(f); return 0; }\n',
    ],
    "parse_prefix": [
        '\nint main() { if (parse_prefix("0x2a", 16) != 42) return 1; return 0; }\n',
        '\nint main() { if (parse_prefix("123", 10) != 123) return 1; return 0; }\n',
        '\nint main() { if (parse_prefix("zz", 10) != -1) return 1; return 0; }\n',
        '\nint main() { if (parse_prefix("", 10) != -1) return 1; return 0; }\n',
        '\nint main() { if (parse_prefix("42abc", 10) != 42) return 1; return 0; }\n',
        '\nint main() { if (parse_prefix("777", 8) != 511) return 1; return 0; }\n',
    ],
    "buffer_too_small": [
        '\nint main() { if (buffer_too_small(64, 16) != (long)0x8007007A) return 1; return 0; }\n',
        '\nint main() { if (buffer_too_small(16, 64) != 0) return 1; return 0; }\n',
        '\nint main() { if (buffer_too_small(32, 32) != 0) return 1; return 0; }\n',
        '\nint main() { if (buffer_too_small(1, 0) != (long)0x8007007A) return 1; return 0; }\n',
        '\nint main() { if (buffer_too_small(0, 0) != 0) return 1; return 0; }\n',
        '\nint main() { if (buffer_too_small(4294967295UL, 1) != (long)0x8007007A) return 1; return 0; }\n',
    ],
    "describe_error": [
        '\nint main() { if (strcmp(describe_error(5), "denied") != 0) return 1; return 0; }\n',
        '\nint main() { if (strcmp(describe_error(6), "handle") != 0) return 1; return 0; }\n',
        '\nint main() { if (strcmp(describe_error(8), "memory") != 0) return 1; return 0; }\n',
        '\nint main() { if (strcmp(describe_error(32), "sharing") != 0) return 1; return 0; }\n',
        '\nint main() { if (strcmp(describe_error(0), "other") != 0) return 1; return 0; }\n',
        '\nint main() { if (strcmp(describe_error(999999), "other") != 0) return 1; return 0; }\n',
    ],
}


# Corpus functions the Linux semantic harness cannot run, with the reason.
#
# `verify_semantic_correctness` compiles the decompiled C with gcc and executes
# it. A function whose behaviour *is* a Windows API call has no meaning under
# that harness: the decompilation references an import that does not exist on
# the host, so it fails to link no matter how correct the recovery was.
#
# They are still in the corpus on purpose -- they exist to measure Win32
# constant-name recovery, an axis semantic execution does not cover. Listing
# them here keeps that debt named rather than silent: `runner/semantic.py`
# reports them as `no_wrapper`, which the ranking already excludes from
# correctness.
SEMANTIC_UNTESTABLE: dict[str, str] = {
    "open_missing_is_not_found": "calls CreateFileA/CloseHandle/GetLastError",
    "reserve_guarded": "calls VirtualAlloc/VirtualProtect",
    "probe_registry_key": "calls RegOpenKeyExA/RegCloseKey",
    "wait_for_one": "calls WaitForSingleObject",
}
