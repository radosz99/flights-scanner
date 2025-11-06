.PHONY: scan help

# Default target
help:
	@echo "Available commands:"
	@echo "  make scan    - Run the Ryanair flight scanner"
	@echo "  make help    - Show this help message"

# Run the scanner
scan:
	python3.13 ryanair_scanner.py
