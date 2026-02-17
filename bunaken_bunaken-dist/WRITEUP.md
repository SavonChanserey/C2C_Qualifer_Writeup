# Bunaken CTF Challenge Writeup

**Challenge:** bunaken (100 points)  
**Author:** vidner  
**Category:** Reverse Engineering / Cryptography

## Challenge Overview

The challenge provides two files:
- `bunaken`: A Bun JavaScript runtime executable (ELF 64-bit)
- `flag.txt.bunakencrypted`: Base64-encoded encrypted flag

## Solution Steps

### 1. Initial Analysis

Running the `bunaken` binary reveals it's built with Bun v1.3.6 and attempts to encrypt `flag.txt`:

```
$ ./bunaken
error: No such file or directory opening 'flag.txt'
```

This confirms the binary is the encryption tool that created the `.bunakencrypted` file.

### 2. Extracting Embedded JavaScript

Bun executables embed JavaScript source code within the binary. Using `strings` command:

```bash
strings bunaken | grep -E "readFileSync|crypto|encrypt"
```

This reveals obfuscated JavaScript code at the end of the output. The key line contains:

```javascript
function w(){let n=["WR0tF8oezmkl","toString",...]}
```

### 3. Deobfuscation

The embedded code uses heavy obfuscation techniques:
- Array-based string lookup
- RC4-like cipher for string decryption
- Two-level obfuscation functions (`l()` and `c()`)

By extracting and running the deobfuscation functions, key strings were revealed:

| Obfuscated Call | Decoded Value |
|----------------|---------------|
| `s(391, "9Dnx")` | `"file"` |
| `s(377, "R69F")` | `"flag.txt"` |
| `s(373, "rG]G")` | **`"sulawesi"`** ← Encryption key! |
| `s(387, "f]pG")` | `"zstdCompre"` (compression) |
| `c(375, "dHTh")` | `"AES-CBC"` |
| `l(399)` | `"SHA-256"` |

### 4. Understanding the Encryption Algorithm

Deobfuscated encryption process:

```javascript
// 1. Read flag.txt
const S = Bun.file("flag.txt");
const k = await S.text();

// 2. Compress with zstd
const v = await Bun.zstdCompress(k);

// 3. Encrypt with AES-CBC
// Key derivation: SHA-256("sulawesi") → take first 16 bytes
// Generate random 16-byte IV
// Encrypt: AES-128-CBC with IV and derived key

// 4. Prepend IV to ciphertext and base64 encode
// Output format: base64(IV || ciphertext)
```

Key findings:
- **Encryption:** AES-128-CBC
- **Key:** SHA-256("sulawesi") truncated to 16 bytes = `7049c447b8379cacc611361b43b0d2c7`
- **IV:** Random 16 bytes prepended to ciphertext
- **Compression:** zstd before encryption
- **Encoding:** Base64 final output

### 5. Decryption

The decryption process reverses the encryption:

```javascript
// 1. Base64 decode
const encryptedData = Buffer.from(base64String, 'base64');

// 2. Extract IV and ciphertext
const iv = encryptedData.slice(0, 16);
const ciphertext = encryptedData.slice(16);

// 3. Derive AES key
const keyHash = crypto.createHash('sha256').update('sulawesi').digest();
const aesKey = keyHash.slice(0, 16);

// 4. Decrypt
const decipher = crypto.createDecipheriv('aes-128-cbc', aesKey, iv);
const decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()]);

// 5. Decompress zstd (flag visible in ASCII even without full decompression)
```

### 6. Flag Extraction

The decrypted data is zstd-compressed (magic bytes: `28 B5 2F FD`). Even without full zstd decompression, the flag is visible in the ASCII representation:

```
C2C{BUN_AwKward_ENcryption_compression_obfuscation}
```

## Key Insights

1. **Bun Binary Analysis:** Bun executables embed JavaScript source code that can be extracted with `strings`
2. **Obfuscation:** Multi-level obfuscation using array lookups and custom cipher
3. **Key Reference:** "sulawesi" refers to Bunaken Island in Indonesia, tying to the challenge name
4. **Layered Protection:** Compression + Encryption + Obfuscation
5. **Weak Point:** Heavy obfuscation in embedded code was reversible through static analysis

## Tools Used

- `strings` - Binary string extraction
- Node.js - JavaScript deobfuscation and decryption
- `crypto` module - AES-CBC decryption and SHA-256 hashing

## Flag

```
C2C{BUN_AwKward_ENcryption_compression_obfuscation}
```

## References

- Bun: https://bun.sh/
- Bunaken: Indonesian island and marine park
- AES-CBC: Symmetric block cipher with Cipher Block Chaining mode
- zstd: Zstandard compression algorithm by Facebook

---

**Difficulty Assessment:** Medium
- Requires binary analysis skills
- JavaScript deobfuscation knowledge
- Understanding of AES-CBC encryption
- Creative thinking to extract flag from partially-decompressed data

**Time to Solve:** ~30-45 minutes for experienced CTF players
