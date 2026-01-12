#!/usr/bin/env python3
import os

def main():
    print("Hello, World! The environment is set up correctly.")
    # Verify .env exists (even if empty)
    if os.path.exists(".env"):
        print(".env file found.")
    else:
        print("WARNING: .env file NOT found.")

if __name__ == "__main__":
    main()
