#!/usr/bin/env node
/**
 * CTF Challenge: bunaken (100 pts)
 * Author: vidner
 * 
 * Solution: Decrypt flag.txt.bunakencrypted
 * 
 * Encryption process (from deobfuscated embedded JS):
 * 1. Read flag.txt
 * 2. Compress with zstd
 * 3. Encrypt with AES-128-CBC using key derived from SHA-256("sulawesi")
 * 4. Prepend 16-byte random IV to ciphertext
 * 5. Base64 encode
 */

const crypto = require('crypto');
const fs = require('fs');

console.log("=== Bunaken CTF Solution ===\n");

// Read the encrypted file
const encryptedBase64 = fs.readFileSync('/mnt/user-data/uploads/flag_txt.bunakencrypted', 'utf8').trim();
console.log("[1] Read encrypted file (base64)");

// Base64 decode
const encryptedData = Buffer.from(encryptedBase64, 'base64');
console.log("[2] Base64 decoded:", encryptedData.length, "bytes");

// Extract IV (first 16 bytes) and ciphertext (rest)
const iv = encryptedData.slice(0, 16);
const ciphertext = encryptedData.slice(16);
console.log("[3] Extracted IV:", iv.toString('hex'));
console.log("[4] Ciphertext length:", ciphertext.length, "bytes");

// Derive the AES key from "sulawesi" using SHA-256 (take first 16 bytes)
const keyPassword = "sulawesi";
const keyHash = crypto.createHash('sha256').update(keyPassword).digest();
const aesKey = keyHash.slice(0, 16);
console.log("[5] Derived AES key from SHA-256('sulawesi'):", aesKey.toString('hex'));

// Decrypt using AES-128-CBC
const decipher = crypto.createDecipheriv('aes-128-cbc', aesKey, iv);
let decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
console.log("[6] AES-CBC decrypted:", decrypted.length, "bytes");

// The data is zstd compressed, but the flag is visible in ASCII
console.log("[7] Data is zstd compressed (magic: 28 B5 2F FD)");
console.log("[8] Extracting flag from compressed data...\n");

// Extract flag
const text = decrypted.toString('ascii');
const match = text.match(/C2C\{[^}]+\}/);

if (match) {
    console.log("┌─────────────────────────────────────────────────────┐");
    console.log("│                     🚩 FLAG FOUND 🚩                │");
    console.log("├─────────────────────────────────────────────────────┤");
    console.log("│  " + match[0].padEnd(51) + "│");
    console.log("└─────────────────────────────────────────────────────┘");
} else {
    console.log("❌ Flag not found!");
}

console.log("\n=== Key Findings ===");
console.log("• Encryption: AES-128-CBC");
console.log("• Key password: 'sulawesi' (Indonesian island)");
console.log("• Key derivation: SHA-256 hash, first 16 bytes");
console.log("• Compression: zstd before encryption");
console.log("• Obfuscation: Heavy JavaScript obfuscation in binary");
